from realestate.config import RangeCriterion, RequiredFeatureCriterion, SearchCriteria, TieredPreferenceCriterion
from realestate.matching import score_property
from realestate.models import Property


def _criteria(**overrides) -> SearchCriteria:
    base = SearchCriteria(
        operation="alquiler",
        property_types=["departamento"],
        zones=["Nuñez", "Saavedra", "Coghlan", "Villa Urquiza"],
        zone_weight=1.0,
        ambientes=RangeCriterion(min=2, max=4, hard=True),
        dormitorios=RangeCriterion(min=2, max=3, hard=True),
        banos=RangeCriterion(min=1, hard=True, bigger_is_better=True, soft_ceiling=3),
        m2=RangeCriterion(min=45, max=125, hard=True, bigger_is_better=True),
        exterior_required=RequiredFeatureCriterion(
            wanted=["balcon", "terraza", "balcon terraza", "patio", "jardin"], min_area_m2=10
        ),
        orientacion=TieredPreferenceCriterion(tiers=[["norte", "noreste"], ["este", "oeste"], ["sur"]]),
        parking_weight=0.5,
        min_score=50,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _property(**overrides) -> Property:
    base = Property(
        id="1",
        source="zonaprop",
        url="https://example.com",
        operation="alquiler",
        property_type="departamento",
        neighborhood="Nuñez",
        ambientes=3,
        dormitorios=2,
        banos=2,
        m2_totales=80,
        exterior=["balcon"],
        exterior_m2=12,
        orientacion="norte",
        parking=1,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_full_match_scores_high():
    result = score_property(_property(), _criteria())
    assert result.passed
    assert result.score > 50


def test_price_in_wrong_currency_is_excluded():
    criteria = _criteria(currency="USD", price=RangeCriterion(min=150000, max=250000, hard=True))
    result = score_property(_property(price=200000, currency="ARS"), criteria)
    assert result.score == 0


def test_price_in_expected_currency_within_range_passes():
    criteria = _criteria(currency="USD", price=RangeCriterion(min=150000, max=250000, hard=True))
    result = score_property(_property(price=200000, currency="USD"), criteria)
    assert result.passed


def test_price_converted_from_usd_to_ars_when_rate_available():
    criteria = _criteria(
        currency="ARS", price=RangeCriterion(min=1100000, max=2100000, hard=True), ars_per_usd=1400
    )
    # 1000 USD * 1400 = 1.400.000 ARS, dentro del rango
    result = score_property(_property(price=1000, currency="USD"), criteria)
    assert result.passed


def test_price_converted_from_usd_excluded_when_outside_range():
    criteria = _criteria(
        currency="ARS", price=RangeCriterion(min=1100000, max=2100000, hard=True), ars_per_usd=1400
    )
    # 100 USD * 1400 = 140.000 ARS, muy por debajo del rango
    result = score_property(_property(price=100, currency="USD"), criteria)
    assert result.score == 0


def test_wrong_operation_is_hard_excluded():
    result = score_property(_property(operation="venta"), _criteria())
    assert result.score == 0
    assert not result.passed


def test_out_of_zone_is_hard_excluded():
    result = score_property(_property(neighborhood="Belgrano"), _criteria())
    assert result.score == 0


def test_ambientes_outside_hard_range_is_excluded():
    result = score_property(_property(ambientes=5), _criteria())
    assert result.score == 0


def test_ambientes_missing_data_is_excluded_when_hard():
    result = score_property(_property(ambientes=None), _criteria())
    assert result.score == 0


def test_dormitorios_outside_hard_range_is_excluded():
    result = score_property(_property(dormitorios=1), _criteria())
    assert result.score == 0


def test_banos_below_floor_is_excluded():
    result = score_property(_property(banos=0), _criteria())
    assert result.score == 0


def test_banos_above_floor_scores_higher_but_is_not_excluded():
    one_bano = score_property(_property(banos=1), _criteria())
    two_banos = score_property(_property(banos=2), _criteria())
    assert one_bano.passed
    assert two_banos.passed
    assert two_banos.score > one_bano.score


def test_m2_outside_hard_range_is_excluded():
    too_small = score_property(_property(m2_totales=40), _criteria())
    too_big = score_property(_property(m2_totales=130), _criteria())
    assert too_small.score == 0
    assert too_big.score == 0


def test_bigger_m2_within_range_scores_higher():
    smaller = score_property(_property(m2_totales=50), _criteria())
    bigger = score_property(_property(m2_totales=120), _criteria())
    assert bigger.score > smaller.score


def test_missing_exterior_feature_is_excluded():
    result = score_property(_property(exterior=[]), _criteria())
    assert result.score == 0


def test_exterior_area_below_minimum_is_excluded():
    result = score_property(_property(exterior=["balcon"], exterior_m2=5), _criteria())
    assert result.score == 0


def test_exterior_without_reported_area_is_not_excluded():
    result = score_property(_property(exterior=["patio"], exterior_m2=None), _criteria())
    assert result.passed


def test_apto_credito_required_excludes_when_false():
    criteria = _criteria(apto_credito_required=True)
    result = score_property(_property(apto_credito=False), criteria)
    assert result.score == 0


def test_apto_credito_required_excludes_when_unknown():
    criteria = _criteria(apto_credito_required=True)
    result = score_property(_property(apto_credito=None), criteria)
    assert result.score == 0


def test_apto_credito_not_required_by_default():
    result = score_property(_property(apto_credito=None), _criteria())
    assert result.passed


def test_orientation_tiers_score_north_above_south():
    norte = score_property(_property(orientacion="norte"), _criteria())
    sur = score_property(_property(orientacion="sur"), _criteria())
    assert norte.score > sur.score


def test_missing_orientation_does_not_penalize():
    missing = score_property(_property(orientacion=None), _criteria())
    sur = score_property(_property(orientacion="sur"), _criteria())
    assert missing.score >= sur.score


def test_zone_preference_order_scores_higher_for_first_choice():
    top_choice = score_property(_property(neighborhood="Nuñez"), _criteria())
    last_choice = score_property(_property(neighborhood="Villa Urquiza"), _criteria())
    assert top_choice.score > last_choice.score


def test_parking_is_a_bonus_not_a_requirement():
    with_parking = score_property(_property(parking=1), _criteria())
    without_parking = score_property(_property(parking=0), _criteria())
    assert with_parking.passed
    assert without_parking.passed
    assert with_parking.score > without_parking.score


def test_missing_parking_data_does_not_penalize():
    missing = score_property(_property(parking=None), _criteria())
    none = score_property(_property(parking=0), _criteria())
    assert missing.score >= none.score
