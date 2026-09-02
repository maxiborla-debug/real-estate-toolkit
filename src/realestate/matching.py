"""Motor de matching: compara una `Property` contra los `SearchCriteria` del
usuario y devuelve un puntaje de 0 a 100.

Filosofía:
- Zona, operación, tipo de propiedad y precio son filtros duros: si la
  propiedad está fuera del área pedida, es del tipo de operación
  equivocado (venta vs alquiler) o se va de precio, se descarta
  directamente (score = 0) — no tiene sentido un "70% de zona".
- El resto de los criterios (ambientes, dormitorios, baños, m2, antigüedad,
  amenities, exterior, servicios) son "blandos": cada uno define un rango o
  una lista deseada, se calcula qué tan bien matchea, y el score final es
  el promedio ponderado. Estar dentro de un rango (ej: 1 a 2 baños) da
  100% en ese campo sin importar si es 1 o 2 — no es limitante.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import ListCriterion, RangeCriterion, SearchCriteria
from .geo import haversine_km
from .models import Property


def _range_score(value: float | None, criterion: RangeCriterion) -> float | None:
    """1.0 si `value` cae dentro de [min, max]; decae linealmente hasta 0 a
    `tolerance` unidades del borde más cercano. `None` si no hay dato para
    ese campo (no penaliza: simplemente se ignora para esa propiedad)."""
    if value is None:
        return None
    lo = criterion.min if criterion.min is not None else float("-inf")
    hi = criterion.max if criterion.max is not None else float("inf")
    if lo <= value <= hi:
        return 1.0
    distance = (lo - value) if value < lo else (value - hi)
    if criterion.tolerance <= 0:
        return 0.0
    return max(0.0, 1.0 - distance / criterion.tolerance)


def _list_score(values: list[str], criterion: ListCriterion) -> float | None:
    if not criterion.wanted:
        return None
    have = {v.lower() for v in values}
    wanted = {w.lower() for w in criterion.wanted}
    matched = have & wanted
    return len(matched) / len(wanted)


def _passes_zone_filter(prop: Property, criteria: SearchCriteria) -> bool:
    if not criteria.zones and not criteria.geo_zones:
        return True  # sin filtro de zona configurado
    if criteria.geo_zones and prop.lat is not None and prop.lon is not None:
        return any(
            haversine_km(prop.lat, prop.lon, zone.lat, zone.lon) <= zone.radius_km
            for zone in criteria.geo_zones
        )
    if criteria.zones and prop.neighborhood:
        neighborhood = prop.neighborhood.lower()
        return any(zone.lower() in neighborhood for zone in criteria.zones)
    # Configuraste zonas pero el aviso no trae ni barrio ni coordenadas: no
    # podemos confirmar que matchea, así que se descarta por precaución.
    return False


@dataclass
class MatchResult:
    property: Property
    score: float
    passed: bool


def score_property(prop: Property, criteria: SearchCriteria) -> MatchResult:
    # --- Filtros duros ---
    if criteria.operation and prop.operation != criteria.operation:
        return MatchResult(prop, 0.0, False)
    if criteria.property_types and prop.property_type not in criteria.property_types:
        return MatchResult(prop, 0.0, False)
    if not _passes_zone_filter(prop, criteria):
        return MatchResult(prop, 0.0, False)
    if prop.price is not None and _range_score(prop.price, criteria.price) == 0.0:
        return MatchResult(prop, 0.0, False)

    # --- Criterios blandos ponderados ---
    fields: list[tuple[float | None, float]] = [
        (_range_score(prop.ambientes, criteria.ambientes), criteria.ambientes.weight),
        (_range_score(prop.dormitorios, criteria.dormitorios), criteria.dormitorios.weight),
        (_range_score(prop.banos, criteria.banos), criteria.banos.weight),
        (_range_score(prop.m2_cubiertos, criteria.m2_cubiertos), criteria.m2_cubiertos.weight),
        (_range_score(prop.antiguedad_anios, criteria.antiguedad), criteria.antiguedad.weight),
        (_list_score(prop.amenities, criteria.amenities), criteria.amenities.weight),
        (_list_score(prop.exterior, criteria.exterior), criteria.exterior.weight),
        (_list_score(prop.servicios, criteria.servicios), criteria.servicios.weight),
    ]

    weighted_sum = 0.0
    weight_total = 0.0
    for value, weight in fields:
        if value is None or weight <= 0:
            continue
        weighted_sum += value * weight
        weight_total += weight

    score = (weighted_sum / weight_total * 100) if weight_total > 0 else 100.0
    passed = score >= criteria.min_score
    return MatchResult(prop, round(score, 1), passed)


def rank_properties(properties: list[Property], criteria: SearchCriteria) -> list[MatchResult]:
    """Puntúa todas las propiedades, descarta las que no llegan a
    `min_score` y devuelve el resto ordenado de mayor a menor."""
    results = [score_property(p, criteria) for p in properties]
    passed = [r for r in results if r.passed]
    return sorted(passed, key=lambda r: r.score, reverse=True)
