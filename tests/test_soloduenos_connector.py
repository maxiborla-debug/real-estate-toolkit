from unittest.mock import patch

from realestate.config import SearchCriteria
from realestate.connectors.soloduenos import SoloDuenosConnector

HOME_HTML = (
    '<html><head></head><body>'
    '<script type="module" crossorigin src="/assets/index-ABC123.js"></script>'
    "</body></html>"
)
BUNDLE_JS = 'const Eh="https://xyzproject.supabase.co",Sh="fake-anon-key-123",H=createClient(Eh,Sh);'
PROPERTIES_JSON = [
    {
        "id": 42,
        "operation_type": "alquiler",
        "rental_price": 1500000,
        "property_type": "departamento",
        "codigo_aviso": 999,
        "status": "activa",
        "deleted_at": None,
    }
]


class _FakeResponse:
    def __init__(self, *, text=None, json_data=None, status_code=200):
        self._text = text
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        pass

    @property
    def text(self):
        return self._text

    def json(self):
        return self._json


def _fake_get(url, headers=None, params=None, timeout=None):
    if url == "https://www.soloduenos.com/":
        return _FakeResponse(text=HOME_HTML)
    if url.endswith(".js"):
        return _FakeResponse(text=BUNDLE_JS)
    if "/rest/v1/properties" in url:
        return _FakeResponse(json_data=PROPERTIES_JSON)
    raise AssertionError(f"URL inesperada: {url}")


def test_search_listings_discovers_and_fetches():
    with patch("realestate.connectors.soloduenos.requests.get", side_effect=_fake_get):
        results = SoloDuenosConnector().search_listings(SearchCriteria())

    assert len(results) == 1
    assert results[0].operation == "alquiler"
    assert results[0].price == 1500000
    assert results[0].property_type == "departamento"


def test_discovery_only_happens_once_per_connector_instance():
    calls: list[str] = []

    def counting_get(url, headers=None, params=None, timeout=None):
        calls.append(url)
        return _fake_get(url, headers=headers, params=params, timeout=timeout)

    connector = SoloDuenosConnector()
    with patch("realestate.connectors.soloduenos.requests.get", side_effect=counting_get):
        connector.search_listings(SearchCriteria())
        connector.search_listings(SearchCriteria())

    assert calls.count("https://www.soloduenos.com/") == 1


def test_uses_discovered_anon_key_in_request_headers():
    captured: dict = {}

    def spy_get(url, headers=None, params=None, timeout=None):
        if "/rest/v1/properties" in url:
            captured["headers"] = headers
        return _fake_get(url, headers=headers, params=params, timeout=timeout)

    with patch("realestate.connectors.soloduenos.requests.get", side_effect=spy_get):
        SoloDuenosConnector().search_listings(SearchCriteria())

    assert captured["headers"]["apikey"] == "fake-anon-key-123"
    assert captured["headers"]["Authorization"] == "Bearer fake-anon-key-123"


def test_to_property_maps_venta_operation():
    item = {"id": 1, "operation_type": "venta", "price": 200000, "property_type": "casa"}
    prop = SoloDuenosConnector()._to_property(item)
    assert prop.operation == "venta"
    assert prop.price == 200000


def test_to_property_returns_none_without_id():
    assert SoloDuenosConnector()._to_property({}) is None
