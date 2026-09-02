"""Motor de matching: compara una `Property` contra los `SearchCriteria` del
usuario y devuelve un puntaje de 0 a 100.

Filosofía:
- Operación, tipo de propiedad, zona, precio, ambientes, dormitorios, baños
  (mínimo), m2 y "apto crédito" (si se pidió) son FILTROS DUROS: si la
  propiedad no los cumple, se descarta directamente (score = 0) — no tiene
  sentido un "70% de zona" o un "80% de ambientes" cuando pediste
  exactamente 2 a 4 y descartar el resto. Si el dato no está informado en
  el aviso, también se descarta (no podemos confirmar que cumple).
- Dentro de esos filtros duros, algunos campos además gradúan el score
  ("bigger_is_better": m2 y baños) — cuanto más grande/más baños, mejor,
  sin dejar de exigir el piso mínimo.
- Zona y orientación son "preferencias por niveles": no excluyen entre sí
  (ya excluidos por el filtro duro de zona), pero suman más score cuanto
  más arriba está tu preferencia (ej: Nuñez > Saavedra > Coghlan > Villa
  Urquiza; Norte/Noreste > Este/Oeste > Sur).
- Parking y balcón/terraza/patio/jardín son "no excluyentes" salvo que se
  pida lo contrario: el exterior es obligatorio (al menos uno de la lista),
  el parking es un bonus que suma pero no descarta si falta.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import RangeCriterion, RequiredFeatureCriterion, SearchCriteria, TieredPreferenceCriterion
from .geo import haversine_km
from .models import Property


def _passes_hard_range(value: float | None, criterion: RangeCriterion) -> bool:
    """Para un criterio `hard`: True si no hay filtro configurado, o si el
    valor cae dentro de [min, max]. Si el aviso no informa el dato, se
    descarta (no se puede confirmar que cumple)."""
    if criterion.min is None and criterion.max is None:
        return True
    if value is None:
        return False
    lo = criterion.min if criterion.min is not None else float("-inf")
    hi = criterion.max if criterion.max is not None else float("inf")
    return lo <= value <= hi


def _score_range_field(value: float | None, criterion: RangeCriterion) -> float | None:
    """Score (0-1) de un campo de rango para el promedio ponderado.

    - Si el criterio es `hard` y NO `bigger_is_better`: ya se decidió todo
      en el filtro duro (pasa o se descarta); acá no aporta gradiente.
    - Si es `hard` y `bigger_is_better`: dentro del rango permitido, más
      alto puntúa más (usa `max` o, si no hay techo, `soft_ceiling`).
    - Si es blando (no hard): dentro de [min, max] da 1.0; afuera decae
      según `tolerance` (comportamiento de siempre).
    """
    if value is None:
        return None

    if criterion.hard:
        if not criterion.bigger_is_better:
            return None
        lo = criterion.min if criterion.min is not None else 0.0
        hi = criterion.max if criterion.max is not None else criterion.soft_ceiling
        if hi is None or hi <= lo:
            return 1.0
        return max(0.0, min(1.0, (value - lo) / (hi - lo)))

    lo = criterion.min if criterion.min is not None else float("-inf")
    hi = criterion.max if criterion.max is not None else float("inf")
    if lo <= value <= hi:
        return 1.0
    distance = (lo - value) if value < lo else (value - hi)
    if criterion.tolerance <= 0:
        return 0.0
    return max(0.0, 1.0 - distance / criterion.tolerance)


def _price_in_target_currency(prop: Property, target_currency: str, ars_per_usd: float | None) -> float | None:
    """Precio del aviso expresado en `target_currency`. Si ya está en esa
    moneda, se devuelve tal cual. Si está en la otra (ARS<->USD) y tenemos
    cotización del día, se convierte. Si no podemos convertir con
    confianza (falta cotización, o es una combinación de monedas no
    soportada), devuelve `None` — no comparamos a ciegas."""
    if prop.price is None:
        return None
    if prop.currency == target_currency:
        return prop.price
    if ars_per_usd is None or ars_per_usd <= 0:
        return None
    if prop.currency == "USD" and target_currency == "ARS":
        return prop.price * ars_per_usd
    if prop.currency == "ARS" and target_currency == "USD":
        return prop.price / ars_per_usd
    return None


def _parking_score(parking: int | None) -> float | None:
    if parking is None:
        return None
    return 1.0 if parking >= 1 else 0.0


def _zones_as_tiers(zones: list[str]) -> list[list[str]]:
    """Cada barrio de la lista es su propio nivel de preferencia, en el
    orden en que se escribieron (el primero es el más preferido)."""
    return [[z] for z in zones]


def _neighborhood_tier_score(neighborhood: str, tiers: list[list[str]]) -> float | None:
    if not tiers or not neighborhood:
        return None
    n = len(tiers)
    low = neighborhood.lower()
    for i, tier in enumerate(tiers):
        if any(name.lower() in low for name in tier):
            return 1.0 if n == 1 else (n - 1 - i) / (n - 1)
    return None


def _tier_score(value: str | None, criterion: TieredPreferenceCriterion) -> float | None:
    if not criterion.tiers or not value:
        return None
    n = len(criterion.tiers)
    low = value.lower()
    for i, tier in enumerate(criterion.tiers):
        if low in {t.lower() for t in tier}:
            return 1.0 if n == 1 else (n - 1 - i) / (n - 1)
    return None


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


def _passes_exterior_required(prop: Property, criterion: RequiredFeatureCriterion) -> bool:
    if not criterion.wanted:
        return True
    have = {v.lower() for v in prop.exterior}
    wanted = {w.lower() for w in criterion.wanted}
    if not (have & wanted):
        return False
    if criterion.min_area_m2 is not None and prop.exterior_m2 is not None:
        return prop.exterior_m2 >= criterion.min_area_m2
    return True  # tiene el amenity; si no informan el m2, se deja pasar


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

    # El precio se compara siempre en la moneda del perfil (`criteria.currency`).
    # Si el aviso está publicado en la otra moneda (ARS<->USD), se convierte
    # con la cotización del día (`criteria.ars_per_usd`, ver fx.py) en vez de
    # descartarlo directamente.
    price_in_profile_currency = _price_in_target_currency(prop, criteria.currency, criteria.ars_per_usd)
    if prop.price is not None and price_in_profile_currency is None:
        return MatchResult(prop, 0.0, False)
    if criteria.price.hard and not _passes_hard_range(price_in_profile_currency, criteria.price):
        return MatchResult(prop, 0.0, False)
    if criteria.ambientes.hard and not _passes_hard_range(prop.ambientes, criteria.ambientes):
        return MatchResult(prop, 0.0, False)
    if criteria.dormitorios.hard and not _passes_hard_range(prop.dormitorios, criteria.dormitorios):
        return MatchResult(prop, 0.0, False)
    if criteria.banos.hard and not _passes_hard_range(prop.banos, criteria.banos):
        return MatchResult(prop, 0.0, False)
    if criteria.m2.hard and not _passes_hard_range(prop.m2, criteria.m2):
        return MatchResult(prop, 0.0, False)
    if not _passes_exterior_required(prop, criteria.exterior_required):
        return MatchResult(prop, 0.0, False)
    if criteria.apto_credito_required and prop.apto_credito is not True:
        return MatchResult(prop, 0.0, False)

    # --- Criterios blandos / graduados ---
    fields: list[tuple[float | None, float]] = [
        (_score_range_field(price_in_profile_currency, criteria.price), criteria.price.weight),
        (_score_range_field(prop.ambientes, criteria.ambientes), criteria.ambientes.weight),
        (_score_range_field(prop.dormitorios, criteria.dormitorios), criteria.dormitorios.weight),
        (_score_range_field(prop.banos, criteria.banos), criteria.banos.weight),
        (_score_range_field(prop.m2, criteria.m2), criteria.m2.weight),
        (_parking_score(prop.parking), criteria.parking_weight),
        (
            _neighborhood_tier_score(prop.neighborhood, _zones_as_tiers(criteria.zones)),
            criteria.zone_weight,
        ),
        (_tier_score(prop.orientacion, criteria.orientacion), criteria.orientacion.weight),
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
    `min_score` y devuelve el resto ordenado de mayor a menor score."""
    results = [score_property(p, criteria) for p in properties]
    passed = [r for r in results if r.passed]
    return sorted(passed, key=lambda r: r.score, reverse=True)
