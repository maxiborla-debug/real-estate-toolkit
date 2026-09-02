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
    """Un rango aceptable para un campo numérico.

    Estar dentro de [min, max] da score 1.0 sin importar el valor exacto
    (ej: "1 o 2 baños" no es limitante). Alejarse del rango resta score
    linealmente hasta llegar a 0 a `tolerance` unidades del borde.
    """

    min: float | None = None
    max: float | None = None
    weight: float = 1.0
    tolerance: float = 1.0


@dataclass
class ListCriterion:
    """Una lista de valores deseados (amenities, exterior, servicios).

    El score es la proporción de `wanted` que el aviso cumple.
    """

    wanted: list[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class GeoZone:
    lat: float
    lon: float
    radius_km: float


@dataclass
class SearchCriteria:
    operation: str = "alquiler"
    property_types: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    geo_zones: list[GeoZone] = field(default_factory=list)
    price: RangeCriterion = field(default_factory=RangeCriterion)
    ambientes: RangeCriterion = field(default_factory=RangeCriterion)
    dormitorios: RangeCriterion = field(default_factory=RangeCriterion)
    banos: RangeCriterion = field(default_factory=RangeCriterion)
    m2_cubiertos: RangeCriterion = field(default_factory=RangeCriterion)
    antiguedad: RangeCriterion = field(default_factory=RangeCriterion)
    amenities: ListCriterion = field(default_factory=ListCriterion)
    exterior: ListCriterion = field(default_factory=ListCriterion)
    servicios: ListCriterion = field(default_factory=ListCriterion)
    min_score: float = 50.0


@dataclass
class EmailConfig:
    recipient: str
    sender_name: str = "Alertas de Propiedades"


@dataclass
class AppConfig:
    search: SearchCriteria
    sources: list[str]
    email: EmailConfig
    smtp_user: str
    smtp_password: str


def _range(raw: dict[str, Any] | None) -> RangeCriterion:
    return RangeCriterion(**(raw or {}))


def _list(raw: dict[str, Any] | None) -> ListCriterion:
    return ListCriterion(**(raw or {}))


def load_config(
    config_path: str | Path = "config/config.yaml",
    env_path: str | Path = ".env",
) -> AppConfig:
    if Path(env_path).exists():
        load_dotenv(env_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    search_raw = raw.get("search", {})
    geo_zones = [GeoZone(**gz) for gz in search_raw.get("geo_zones", [])]

    search = SearchCriteria(
        operation=search_raw.get("operation", "alquiler"),
        property_types=search_raw.get("property_types", []),
        zones=search_raw.get("zones", []),
        geo_zones=geo_zones,
        price=_range(search_raw.get("price")),
        ambientes=_range(search_raw.get("ambientes")),
        dormitorios=_range(search_raw.get("dormitorios")),
        banos=_range(search_raw.get("banos")),
        m2_cubiertos=_range(search_raw.get("m2_cubiertos")),
        antiguedad=_range(search_raw.get("antiguedad")),
        amenities=_list(search_raw.get("amenities")),
        exterior=_list(search_raw.get("exterior")),
        servicios=_list(search_raw.get("servicios")),
        min_score=search_raw.get("min_score", 50.0),
    )

    email_raw = raw.get("email", {})
    email = EmailConfig(
        recipient=email_raw.get("recipient", ""),
        sender_name=email_raw.get("sender_name", "Alertas de Propiedades"),
    )

    return AppConfig(
        search=search,
        sources=raw.get("sources", []),
        email=email,
        smtp_user=os.getenv("GMAIL_USER", ""),
        smtp_password=os.getenv("GMAIL_APP_PASSWORD", ""),
    )
