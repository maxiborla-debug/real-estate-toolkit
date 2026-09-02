from unittest.mock import patch

import requests

from realestate.probe import probe_site


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "<html>ok</html>"):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")


def test_probe_site_reports_status_and_length():
    with patch("realestate.probe.requests.get", return_value=_FakeResponse(200)):
        result = probe_site("test", "https://example.com")
    assert result["status"] == 200
    assert result["blocked_hint"] is False
    assert result["length"] > 0


def test_probe_site_detects_block_marker():
    with patch(
        "realestate.probe.requests.get",
        return_value=_FakeResponse(200, "<html>Access Denied</html>"),
    ):
        result = probe_site("test", "https://example.com")
    assert result["blocked_hint"] is True


def test_probe_site_reports_request_errors():
    with patch("realestate.probe.requests.get", side_effect=requests.RequestException("timeout")):
        result = probe_site("test", "https://example.com")
    assert result["status"] is None
    assert "error" in result
