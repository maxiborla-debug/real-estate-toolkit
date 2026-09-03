"""Conector real para Solo Dueños (soloduenos.com).

El sitio es una SPA (React) que consulta directamente a Supabase (Postgres
+ PostgREST) desde el navegador. La "anon key" pública que usa para eso
está pensada para ser pública — la seguridad real la da Row Level Security
del lado del servidor, no el secreto de esa key — así que cualquier
cliente (incluida esta app) puede usarla igual que hace el sitio.

Para no depender de que el nombre del archivo del bundle cambie en cada
deploy, el conector la descubre solo: trae la home, encuentra el
`<script type="module">` principal, y extrae de ahí la URL del proyecto de
Supabase y la anon key con una regex. Ese valor nunca se imprime ni se
loggea — sólo se usa en memoria para armar los headers de las requests.

Tabla real (descubierta inspeccionando el bundle, ver docs/PLATAFORMAS.md):
`properties`, con columnas como `status` ("activa" = publicado),
`deleted_at`, `price` / `rental_price` según `operation_type`
("venta" | "alquiler" | "alquiler_temporario"), `property_type`,
`codigo_aviso`. El resto de los campos se mapean con nombres candidatos
razonables; si Solo Dueños cambia el esquema, algunos campos van a llegar
vacíos (matching.py ya sabe tratar eso como "sin dato", no como "no
cumple").
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

import requests

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria

HOME_URL = "https://www.soloduenos.com/"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

_BUNDLE_RE = re.compile(r'<script[^>]+type="module"[^>]+src="([^"]+\.js)"')
# Patrón real observado en el bundle: `Eh="https://xxx.supabase.co",Sh="<anon_key>"`
# — entre las dos strings hay una asignación de variable, no están pegadas.
_SUPABASE_RE = re.compile(r'https://([a-z0-9]+)\.supabase\.co"\s*,\s*[A-Za-z_$][\w$]*\s*=\s*"([^"]+)"')

PAGE_SIZE = 100
MAX_PAGES = 5


class SoloDuenosConnector(RealEstateConnector):
    name = "soloduenos"

    def __init__(self) -> None:
        self._project_url: Optional[str] = None
        self._anon_key: Optional[str] = None

    def _discover_supabase_credentials(self) -> tuple[str, str]:
        home = requests.get(HOME_URL, headers=REQUEST_HEADERS, timeout=20)
        home.raise_for_status()
        bundle_match = _BUNDLE_RE.search(home.text)
        if not bundle_match:
            raise RuntimeError("No se encontró el bundle de JS principal en la home de Solo Dueños.")
        bundle_url = bundle_match.group(1)
        if bundle_url.startswith("/"):
            bundle_url = "https://www.soloduenos.com" + bundle_url

        bundle = requests.get(bundle_url, headers=REQUEST_HEADERS, timeout=30)
        bundle.raise_for_status()
        creds_match = _SUPABASE_RE.search(bundle.text)
        if not creds_match:
            raise RuntimeError("No se encontraron credenciales de Supabase en el bundle de Solo Dueños.")
        project_ref, anon_key = creds_match.groups()
        return f"https://{project_ref}.supabase.co", anon_key

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        if not self._project_url or not self._anon_key:
            self._project_url, self._anon_key = self._discover_supabase_credentials()

        headers = {
            **REQUEST_HEADERS,
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._anon_key}",
        }

        raw_items: list[dict] = []
        offset = 0
        while offset < PAGE_SIZE * MAX_PAGES:
            params = {
                "select": "*",
                "status": "eq.activa",
                "deleted_at": "is.null",
                "limit": str(PAGE_SIZE),
                "offset": str(offset),
            }
            response = requests.get(
                f"{self._project_url}/rest/v1/properties",
                headers=headers,
                params=params,
                timeout=20,
            )
            if response.status_code in (401, 403):
                # Diagnóstico seguro: nunca imprime la key completa, sólo
                # largo y puntas, para poder confirmar si la extracción del
                # bundle sacó algo truncado/incorrecto sin exponer el valor.
                key = self._anon_key or ""
                print(
                    f"[soloduenos] {response.status_code} de Supabase. "
                    f"anon_key: largo={len(key)} inicio={key[:8]!r} fin={key[-6:]!r} "
                    f"body={response.text[:300]!r}"
                )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            raw_items.extend(batch)
            offset += PAGE_SIZE
            if len(batch) < PAGE_SIZE:
                break

        properties = [p for item in raw_items if (p := self._to_property(item)) is not None]

        if raw_items and not properties:
            print(
                f"[soloduenos] AVISO: se encontraron {len(raw_items)} avisos pero no se "
                "pudo normalizar ninguno — claves del primer item:"
            )
            print(sorted(raw_items[0].keys()))

        return properties

    @staticmethod
    def _get(item: dict, *keys: str):
        for key in keys:
            if item.get(key) not in (None, ""):
                return item[key]
        return None

    def _to_property(self, item: dict) -> Property | None:
        item_id = item.get("id")
        if item_id is None:
            return None

        operation_type = (item.get("operation_type") or "").lower()
        if "alquiler" in operation_type:
            operation = "alquiler"
            price = self._get(item, "rental_price", "price")
        elif "venta" in operation_type:
            operation = "venta"
            price = self._get(item, "price")
        else:
            operation = ""
            price = self._get(item, "price", "rental_price")

        codigo = item.get("codigo_aviso")
        url = f"https://www.soloduenos.com/propiedad/{item_id}" if item_id else ""

        return Property(
            id=str(item_id),
            source=self.name,
            url=url,
            operation=operation,
            property_type=str(self._get(item, "property_type") or "").lower(),
            title=str(self._get(item, "title", "codigo_aviso") or (f"Aviso {codigo}" if codigo else "")),
            price=float(price) if price is not None else None,
            currency=str(self._get(item, "currency") or "ARS"),
            neighborhood=str(self._get(item, "neighborhood", "zone_name", "address") or ""),
            lat=self._get(item, "lat", "latitude"),
            lon=self._get(item, "lon", "lng", "longitude"),
            ambientes=self._get(item, "rooms", "ambientes"),
            dormitorios=self._get(item, "bedrooms", "dormitorios"),
            banos=self._get(item, "bathrooms", "banos", "full_bathrooms"),
            m2_cubiertos=self._get(item, "covered_area", "m2_cubiertos"),
            m2_totales=self._get(item, "total_area", "m2_totales", "lot_area"),
            parking=self._get(item, "parking_lots", "parking", "garage"),
            raw=item,
        )
