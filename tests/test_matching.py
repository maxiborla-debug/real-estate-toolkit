from realestate.config import ListCriterion, RangeCriterion, SearchCriteria
from realestate.matching import score_property
from realestate.models import Property


def _criteria(**overrides) -> SearchCriteria:
    base = SearchCriteria(
        operation="alquiler",
        property_types=["departamento"],
        zones=["Palermo"],
        banos=RangeCriterion(min=1, max=2, weight=1.0, tolerance=1),
        ambientes=RangeCriterion(min=2, max=3, weight=1.0, tolerance=1),
        amenities=ListCriterion(wanted=["pileta", "gimnasio"], weight=1.0),
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
        neighborhood="Palermo Hollywood",
        banos=2,
        ambientes=3,
        amenities=["pileta"],
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_full_match_scores_above_min():
    result = score_property(_property(), _criteria())
    assert result.passed
    assert result.score > 50


def test_wrong_operation_is_hard_excluded():
    result = score_property(_property(operation="venta"), _criteria())
    assert result.score == 0
    assert not result.passed


def test_out_of_zone_is_hard_excluded():
    result = score_property(_property(neighborhood="Belgrano"), _criteria())
    assert result.score == 0


def test_bathrooms_in_range_score_equally_regardless_of_exact_value():
    r1 = score_property(_property(banos=1), _criteria())
    r2 = score_property(_property(banos=2), _criteria())
    assert r1.score == r2.score


def test_bathrooms_outside_range_decays_but_is_not_hard_excluded():
    result = score_property(_property(banos=4), _criteria())
    assert 0 < result.score < 100


def test_missing_field_is_not_treated_as_a_bad_value():
    missing = score_property(_property(banos=None), _criteria())
    way_off = score_property(_property(banos=100), _criteria())
    assert missing.score > way_off.score
