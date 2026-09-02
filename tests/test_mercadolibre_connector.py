from unittest.mock import patch

from realestate.config import SearchCriteria
from realestate.connectors.mercadolibre import MercadoLibreConnector

FAKE_ITEM = {
    "id": "MLA123",
    "title": "Depto 3 ambientes con balcón en Nuñez",
    "price": 200000,
    "currency_id": "USD",
    "permalink": "https://example.com/item",
    "location": {
        "neighborhood": {"name": "Nuñez"},
        "geolocation": {"latitude": -34.55, "longitude": -58.46},
    },
    "attributes": [
        {"id": "OPERATION", "name": "Operación", "value_name": "Venta"},
        {"id": "PROPERTY_TYPE", "name": "Tipo de propiedad", "value_name": "Departamento"},
        {"id": "ROOMS", "name": "Ambientes", "value_name": "3"},
        {"id": "BEDROOMS", "name": "Dormitorios", "value_name": "2"},
        {"id": "FULL_BATHROOMS", "name": "Baños", "value_name": "2"},
        {"id": "COVERED_AREA", "name": "Superficie cubierta", "value_name": "80 m²"},
        {"id": "TOTAL_AREA", "name": "Superficie total", "value_name": "90 m²"},
        {"id": "PARKING_LOTS", "name": "Cocheras", "value_name": "1"},
        {"id": "ORIENTATION", "name": "Orientación", "value_name": "Norte"},
        {"id": "CREDIT_ELIGIBLE", "name": "Crédito hipotecario", "value_name": "Apto crédito"},
    ],
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_to_property_maps_known_fields():
    connector = MercadoLibreConnector()
    prop = connector._to_property(FAKE_ITEM)

    assert prop.id == "MLA123"
    assert prop.operation == "venta"
    assert prop.property_type == "departamento"
    assert prop.price == 200000
    assert prop.currency == "USD"
    assert prop.neighborhood == "Nuñez"
    assert prop.lat == -34.55
    assert prop.lon == -58.46
    assert prop.ambientes == 3
    assert prop.dormitorios == 2
    assert prop.banos == 2
    assert prop.m2_cubiertos == 80
    assert prop.m2_totales == 90
    assert prop.parking == 1
    assert "balcon" in prop.exterior
    assert prop.orientacion == "norte"
    assert prop.apto_credito is True


def test_to_property_returns_none_without_id():
    connector = MercadoLibreConnector()
    assert connector._to_property({}) is None


def test_unknown_operation_is_not_guessed():
    item = dict(FAKE_ITEM, attributes=[a for a in FAKE_ITEM["attributes"] if a["id"] != "OPERATION"])
    prop = MercadoLibreConnector()._to_property(item)
    assert prop.operation == ""


def test_apto_credito_none_when_not_mentioned():
    item = dict(FAKE_ITEM, attributes=[a for a in FAKE_ITEM["attributes"] if a["id"] != "CREDIT_ELIGIBLE"])
    prop = MercadoLibreConnector()._to_property(item)
    assert prop.apto_credito is None


def test_apto_credito_false_when_explicitly_not_apto():
    item = {
        "id": "MLA999",
        "title": "Depto",
        "attributes": [{"id": "CREDIT", "name": "Crédito", "value_name": "No apto crédito"}],
    }
    prop = MercadoLibreConnector()._to_property(item)
    assert prop.apto_credito is False


def test_search_listings_dedupes_across_zones():
    payload = {"results": [FAKE_ITEM], "paging": {"total": 1}}
    criteria = SearchCriteria(zones=["Nuñez", "Saavedra"])

    with patch(
        "realestate.connectors.mercadolibre.requests.get", return_value=_FakeResponse(payload)
    ) as mock_get:
        results = MercadoLibreConnector().search_listings(criteria)

    assert len(results) == 1
    assert mock_get.call_count == 2  # una búsqueda por zona


def test_search_listings_without_zones_does_one_search():
    payload = {"results": [FAKE_ITEM], "paging": {"total": 1}}
    criteria = SearchCriteria(zones=[])

    with patch(
        "realestate.connectors.mercadolibre.requests.get", return_value=_FakeResponse(payload)
    ) as mock_get:
        results = MercadoLibreConnector().search_listings(criteria)

    assert len(results) == 1
    assert mock_get.call_count == 1
