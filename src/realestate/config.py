"""Carga config.yaml (criterios de búsqueda) + .env (credenciales de email
para pruebas locales — en producción van como Secrets de GitHub Actions).

Ver docs/CONFIGURACION.md para el detalle de cada campo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class RangeCriterion:
    """Un rango numérico, con dos modos de uso:

    - `hard=False` (por defecto): rango "blando" — estar adentro da score
      1.0, alejarse resta score linealmente hasta 0 a `tolerance` unidades
      del borde.
    - `hard=True`: filtro estricto — un valor fuera de [min, max] descarta
      la propiedad directamente (no se muestra, sea cual sea el resto del
      match). Si además `bigger_is_better=True`, dentro del rango permitido
      el score no es plano: cuanto más alto el valor, mejor (ej: metros
      cuadrados, cantidad de baños). `soft_ceiling` sirve para poner un
      techo al gradiente cuando no hay `max` (ej: baños, donde no tiene
      sentido premiar sin límite).

    Un valor faltante en el aviso para un campo `hard` hace que se
    descarte (no podemos confirmar que cumple el mínimo/máximo pedido) —
    mismo criterio que se usa para la zona.
    """

    min: float | None = None
    max: float | None = None
    weight: float = 1.0
    tolerance: float = 1.0
    hard: bool = False
    bigger_is_better: bool = False
    soft_ceiling: float | None = None


@dataclass
class RequiredFeatureCriterion:
    """Al menos uno de `wanted` tiene que estar presente en el aviso, sino
    se descarta. Si se define `min_area_m2` y el aviso informa el m2 de ese
    espacio, también tiene que cumplir ese mínimo (si no lo informa, se
    deja pasar con sólo tener el amenity)."""

    wanted: list[str] = field(default_factory=list)
    min_area_m2: float | None = None


@dataclass
class TieredPreferenceCriterion:
    """Niveles de preferencia, de mejor a peor (ej: orientación). Cada nivel
    es una lista de valores equivalentes entre sí. No excluye nada: si el
    valor del aviso no está en ningún nivel, o no hay dato, no suma ni resta
    score — sólo gradúa entre los valores que sí conocemos."""

    tiers: list[list[str]] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class GeoZone:
    lat: float
    lon: float
    radius_km: float


@dataclass
class SearchCriteria:
    """Criterios combinados (compartidos + los propios de un perfil/operación)
    contra los que se puntúa cada `Property`. Ver `AppConfig.criteria_for`."""

    operation: str = "alquiler"
    property_types: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)  # ordenados de más a menos preferido
    zone_weight: float = 1.0
    geo_zones: list[GeoZone] = field(default_factory=list)
    currency: str = "ARS"
    ars_per_usd: float | None = None  # cotización del día, para comparar avisos en la otra moneda
    price: RangeCriterion = field(default_factory=RangeCriterion)
    ambientes: RangeCriterion = field(default_factory=RangeCriterion)
    dormitorios: RangeCriterion = field(default_factory=RangeCriterion)
    banos: RangeCriterion = field(default_factory=RangeCriterion)
    m2: RangeCriterion = field(default_factory=RangeCriterion)
    exterior_required: RequiredFeatureCriterion = field(default_factory=RequiredFeatureCriterion)
    orientacion: TieredPreferenceCriterion = field(default_factory=TieredPreferenceCriterion)
    parking_weight: float = 0.0
    apto_credito_required: bool = False
    min_score: float = 50.0


@dataclass
class ProfileConfig:
    """Un perfil de búsqueda = una operación (compra/alquiler), con su propio
    rango de precio, moneda y destinatario de mail. Cada perfil se escanea y
    se manda por mail POR SEPARADO."""

    operation: str        # "venta" | "alquiler"
    label: str              # nombre para mostrar en el asunto del mail
    recipient: str
    currency: str           # moneda en la que está expresado `price` (ej: "USD", "ARS")
    price: RangeCriterion
    apto_credito_required: bool = False


@dataclass
class SharedCriteria:
    """Criterios que aplican por igual a todos los perfiles."""

    property_types: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    zone_weight: float = 1.0
    geo_zones: list[GeoZone] = field(default_factory=list)
    ambientes: RangeCriterion = field(default_factory=RangeCriterion)
    dormitorios: RangeCriterion = field(default_factory=RangeCriterion)
    banos: RangeCriterion = field(default_factory=RangeCriterion)
    m2: RangeCriterion = field(default_factory=RangeCriterion)
    exterior_required: RequiredFeatureCriterion = field(default_factory=RequiredFeatureCriterion)
    orientacion: TieredPreferenceCriterion = field(default_factory=TieredPreferenceCriterion)
    parking_weight: float = 0.0
    min_score: float = 50.0


@dataclass
class AppConfig:
    shared: SharedCriteria
    profiles: list[ProfileConfig]
    sources: list[str]
    sender_name: str
    smtp_user: str
    smtp_password: str
    fx_fallback_ars_per_usd: float = 1400.0

    def criteria_for(self, profile: ProfileConfig, ars_per_usd: float | None = None) -> SearchCriteria:
        """Combina los criterios compartidos con los propios de un perfil en
        un único `SearchCriteria`, listo para pasarle a un conector y al
        motor de matching. `ars_per_usd` es la cotización del día (ver
        `fx.get_ars_per_usd`), para poder comparar avisos publicados en la
        moneda "equivocada" para este perfil en vez de descartarlos."""
        s = self.shared
        return SearchCriteria(
            operation=profile.operation,
            property_types=s.property_types,
            zones=s.zones,
            zone_weight=s.zone_weight,
            geo_zones=s.geo_zones,
            currency=profile.currency,
            ars_per_usd=ars_per_usd,
            price=profile.price,
            ambientes=s.ambientes,
            dormitorios=s.dormitorios,
            banos=s.banos,
            m2=s.m2,
            exterior_required=s.exterior_required,
            orientacion=s.orientacion,
            parking_weight=s.parking_weight,
            apto_credito_required=profile.apto_credito_required,
            min_score=s.min_score,
        )


def _range(raw: dict[str, Any] | None) -> RangeCriterion:
    return RangeCriterion(**(raw or {}))


def _required_feature(raw: dict[str, Any] | None) -> RequiredFeatureCriterion:
    return RequiredFeatureCriterion(**(raw or {}))


def _tiered(raw: dict[str, Any] | None) -> TieredPreferenceCriterion:
    return TieredPreferenceCriterion(**(raw or {}))


def load_config(
    config_path: str | Path = "config/config.yaml",
    env_path: str | Path = ".env",
) -> AppConfig:
    if Path(env_path).exists():
        load_dotenv(env_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    shared_raw = raw.get("shared", {})
    geo_zones = [GeoZone(**gz) for gz in shared_raw.get("geo_zones", [])]

    shared = SharedCriteria(
        property_types=shared_raw.get("property_types", []),
        zones=shared_raw.get("zones", []),
        zone_weight=shared_raw.get("zone_weight", 1.0),
        geo_zones=geo_zones,
        ambientes=_range(shared_raw.get("ambientes")),
        dormitorios=_range(shared_raw.get("dormitorios")),
        banos=_range(shared_raw.get("banos")),
        m2=_range(shared_raw.get("m2")),
        exterior_required=_required_feature(shared_raw.get("exterior_required")),
        orientacion=_tiered(shared_raw.get("orientacion")),
        parking_weight=shared_raw.get("parking_weight", 0.0),
        min_score=shared_raw.get("min_score", 50.0),
    )

    profiles = [
        ProfileConfig(
            operation=p["operation"],
            label=p.get("label", p["operation"]),
            recipient=p.get("recipient", ""),
            currency=p.get("currency", "ARS"),
            price=_range(p.get("price")),
            apto_credito_required=p.get("apto_credito_required", False),
        )
        for p in raw.get("profiles", [])
    ]

    return AppConfig(
        shared=shared,
        profiles=profiles,
        sources=raw.get("sources", []),
        sender_name=raw.get("sender_name", "Alertas de Propiedades"),
        smtp_user=os.getenv("GMAIL_USER", ""),
        smtp_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        fx_fallback_ars_per_usd=raw.get("fx_fallback_ars_per_usd", 1400.0),
    )
