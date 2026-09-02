from unittest.mock import patch

from realestate.fx import get_ars_per_usd


def test_returns_fallback_when_request_fails():
    with patch("realestate.fx.requests.get", side_effect=RuntimeError("sin red")):
        assert get_ars_per_usd(fallback=1234.0) == 1234.0


def test_parses_venta_field_from_response():
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"venta": "987.5"}

    with patch("realestate.fx.requests.get", return_value=FakeResponse()):
        assert get_ars_per_usd() == 987.5
