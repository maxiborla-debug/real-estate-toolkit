"""Conector real para MercadoLibre Inmuebles, usando su API pública
(`api.mercadolibre.com`), sin necesidad de autenticación para búsquedas de
lectura.

Cómo busca: en vez de adivinar los IDs internos de los filtros de
ubicación/operación de MercadoLibre (cambian y no están documentados de
forma estable), se hace una búsqueda de texto libre (`q=<barrio>`) dentro
de la categoría de Inmuebles por cada zona configurada en
`criteria.zones`, y se deja que TODO el filtrado real (operación, tipo,
rango de precio, ambientes, etc.) lo haga `matching.py` sobre los datos ya
normalizados — así no dependemos de la API para filtrar bien, sólo para
traer candidatos.

Los nombres de los atributos (`ROOMS`, `BEDROOMS`, etc.) son los que
MercadoLibre expone hoy para esta categoría según su documentación
pública; si en el futuro los cambian, algunos campos van a llegar vacíos
(no rompe nada, matching.py trata los datos faltantes como "sin
información", no como "no cumple") — y esta conector imprime un aviso de
diagnóstico si detecta que dejó de poder mapear los datos.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

import requests

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria

SEARCH_URL = "https://api.mercadolibre.com/sites/MLA/search"
CATEGORY_INMUEBLES = "MLA1459"
PAGE_SIZE = 50
MAX_PAGES_PER_ZONE = 4  # tope de páginas por zona buscada, para no pedir de más

# Attribute IDs tal como los expone hoy la API de MercadoLibre para esta
# categoría. Ver el aviso de diagnóstico en los logs si dejan de matchear.
ATTR_OPERATION = "OPERATION"
ATTR_PROPERTY_TYPE = "PROPERTY_TYPE"
ATTR_ROOMS = "ROOMS"
ATTR_BEDROOMS = "BEDROOMS"
ATTR_BATHROOMS = ("FULL_BATHROOMS", "BATHROOMS")
ATTR_COVERED_AREA = "COVERED_AREA"
ATTR_TOTAL_AREA = "TOTAL_AREA"
ATTR_PARKING = "PARKING_LOTS"

# Balcón/terraza/patio/jardín, "apto crédito" y orientación no tienen un ID
# de atributo estable y documentado en la API pública, así que se detectan
# buscando palabras clave en el texto de TODOS los atributos (nombre +
# valor) — más robusto que apostar a un ID interno que puede no existir.
_EXTERIOR_KEYWORDS: dict[str, list[str]] = {
    "balcon": ["balcón", "balcon"],
    "terraza": ["terraza"],
    "patio": ["patio"],
    "jardin": ["jardín", "jardin"],
}
_ORIENTATION_VALUES = ("noreste", "noroeste", "sureste", "suroeste", "norte", "sur", "este", "oeste")

# Sólo dígitos ASCII: `str.isdigit()` también da True para cosas como el
# superíndice "²" de "80 m²", lo que rompía el parseo si se filtraba
# carácter por carácter en vez de con esta regex.
_NUMBER_RE = re.compile(r"[0-9]+(?:[.,][0-9]+)?")


class MercadoLibreConnector(RealEstateConnector):
    name = "mercadolibre"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        zones = criteria.zones or [None]
        seen_ids: set[str] = set()
        raw_items: list[dict] = []

        for zone in zones:
            for item in self._search_zone(zone):
                item_id = item.get("id")
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                raw_items.append(item)

        properties: list[Property] = []
        for item in raw_items:
            prop = self._to_property(item)
            if prop is not None:
                properties.append(prop)

        if raw_items and not properties:
            # Trajimos avisos pero no pudimos normalizar ninguno: lo más
            # probable es que MercadoLibre haya cambiado los nombres de
            # atributos de arriba. Dejamos un ejemplo crudo en los logs
            # para poder arreglarlo rápido.
            print(
                f"[mercadolibre] AVISO: se encontraron {len(raw_items)} avisos pero no se "
                "pudo normalizar ninguno — revisar los ATTR_* de mercadolibre.py contra "
                "un item de ejemplo:"
            )
            print(raw_items[0])

        return properties

    def _search_zone(self, zone: str | None) -> list[dict]:
        results: list[dict] = []
        offset = 0
        while offset < PAGE_SIZE * MAX_PAGES_PER_ZONE:
            params = {"category": CATEGORY_INMUEBLES, "limit": PAGE_SIZE, "offset": offset}
            if zone:
                params["q"] = zone
            response = requests.get(SEARCH_URL, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            batch = data.get("results", [])
            results.extend(batch)
            total = data.get("paging", {}).get("total", 0)
            offset += PAGE_SIZE
            if not batch or offset >= total:
                break
        return results

    def _to_property(self, item: dict) -> Property | None:
        item_id = item.get("id")
        if not item_id:
            return None

        attrs = {a.get("id"): a for a in item.get("attributes", []) if a.get("id")}

        def attr_text(*attr_ids: str) -> str | None:
            for attr_id in attr_ids:
                attr = attrs.get(attr_id)
                value = attr.get("value_name") if attr else None
                if value:
                    return str(value)
            return None

        def attr_number(*attr_ids: str) -> float | None:
            value = attr_text(*attr_ids)
            if value is None:
                return None
            match = _NUMBER_RE.search(value)
            if not match:
                return None
            number = match.group(0)
            if "," in number:
                number = number.replace(".", "").replace(",", ".")
            try:
                return float(number)
            except ValueError:
                return None

        operation_raw = (attr_text(ATTR_OPERATION) or "").lower()
        if "venta" in operation_raw:
            operation = "venta"
        elif "alquiler" in operation_raw:
            operation = "alquiler"
        else:
            operation = ""  # desconocida: no va a matchear ningún perfil, no se inventa

        property_type = (attr_text(ATTR_PROPERTY_TYPE) or "").lower()

        location = item.get("location") or {}
        address = item.get("address") or {}
        neighborhood = (
            (location.get("neighborhood") or {}).get("name")
            or (location.get("city") or {}).get("name")
            or address.get("city_name")
            or ""
        )
        geo = location.get("geolocation") or item.get("geolocation") or {}

        parking_raw = attr_number(ATTR_PARKING)

        return Property(
            id=str(item_id),
            source=self.name,
            url=item.get("permalink", ""),
            operation=operation,
            property_type=property_type,
            title=item.get("title", ""),
            price=item.get("price"),
            currency=item.get("currency_id", "ARS"),
            neighborhood=neighborhood,
            lat=geo.get("latitude"),
            lon=geo.get("longitude"),
            ambientes=attr_number(ATTR_ROOMS),
            dormitorios=attr_number(ATTR_BEDROOMS),
            banos=attr_number(*ATTR_BATHROOMS),
            m2_cubiertos=attr_number(ATTR_COVERED_AREA),
            m2_totales=attr_number(ATTR_TOTAL_AREA),
            parking=int(parking_raw) if parking_raw is not None else None,
            exterior=self._extract_exterior(item),
            apto_credito=self._extract_apto_credito(item),
            orientacion=self._extract_orientacion(item),
            raw=item,
        )

    @staticmethod
    def _attribute_blob(item: dict) -> str:
        parts = [
            f"{a.get('name', '')} {a.get('value_name', '')}" for a in item.get("attributes", [])
        ]
        parts.append(item.get("title", ""))
        return " ".join(parts).lower()

    def _extract_exterior(self, item: dict) -> list[str]:
        blob = self._attribute_blob(item)
        return [label for label, keywords in _EXTERIOR_KEYWORDS.items() if any(kw in blob for kw in keywords)]

    def _extract_apto_credito(self, item: dict) -> bool | None:
        blob = self._attribute_blob(item)
        if "credito" not in blob and "crédito" not in blob:
            return None  # no lo mencionan: desconocido, no se inventa
        return "no apto" not in blob and "no es apto" not in blob

    def _extract_orientacion(self, item: dict) -> str | None:
        for attr in item.get("attributes", []):
            if "orientac" in (attr.get("name") or "").lower():
                value = (attr.get("value_name") or "").lower()
                for direction in _ORIENTATION_VALUES:
                    if direction in value:
                        return direction
        return None
