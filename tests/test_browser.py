import time
from unittest.mock import MagicMock, patch

import pytest

from realestate.browser import fetch_rendered_html, fetch_rendered_html_safe


def _make_playwright_mock(page: MagicMock) -> MagicMock:
    browser = MagicMock()
    browser.new_page.return_value = page
    chromium = MagicMock()
    chromium.launch.return_value = browser
    playwright = MagicMock()
    playwright.chromium = chromium
    context = MagicMock()
    context.__enter__.return_value = playwright
    context.__exit__.return_value = False
    return context, browser


def test_fetch_rendered_html_returns_page_content():
    page = MagicMock()
    page.content.return_value = "<html>ok</html>"
    context, browser = _make_playwright_mock(page)

    with patch("realestate.browser.sync_playwright", return_value=context):
        html = fetch_rendered_html("https://example.com")

    assert html == "<html>ok</html>"
    page.goto.assert_called_once()
    browser.close.assert_called_once()


def test_fetch_rendered_html_waits_for_selector_when_given():
    page = MagicMock()
    page.content.return_value = "<html>ok</html>"
    context, _ = _make_playwright_mock(page)

    with patch("realestate.browser.sync_playwright", return_value=context):
        fetch_rendered_html("https://example.com", wait_selector=".listing")

    page.wait_for_selector.assert_called_once()
    page.wait_for_timeout.assert_not_called()


def test_fetch_rendered_html_falls_back_to_timeout_without_selector():
    page = MagicMock()
    page.content.return_value = "<html>ok</html>"
    context, _ = _make_playwright_mock(page)

    with patch("realestate.browser.sync_playwright", return_value=context):
        fetch_rendered_html("https://example.com")

    page.wait_for_timeout.assert_called_once()
    page.wait_for_selector.assert_not_called()


def test_fetch_rendered_html_closes_browser_even_on_error():
    page = MagicMock()
    page.goto.side_effect = RuntimeError("boom")
    context, browser = _make_playwright_mock(page)

    with patch("realestate.browser.sync_playwright", return_value=context):
        try:
            fetch_rendered_html("https://example.com")
        except RuntimeError:
            pass

    browser.close.assert_called_once()


def test_fetch_rendered_html_safe_returns_result_when_fast_enough():
    with patch("realestate.browser.fetch_rendered_html", return_value="<html>ok</html>"):
        html = fetch_rendered_html_safe("https://example.com", hard_timeout_s=5)

    assert html == "<html>ok</html>"


def test_fetch_rendered_html_safe_reraises_underlying_error():
    with patch("realestate.browser.fetch_rendered_html", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            fetch_rendered_html_safe("https://example.com", hard_timeout_s=5)


def test_fetch_rendered_html_safe_times_out_instead_of_hanging_forever():
    def _hang(url, **kwargs):
        time.sleep(10)  # más que el hard_timeout_s de abajo
        return "<html>nunca llega</html>"

    with patch("realestate.browser.fetch_rendered_html", side_effect=_hang):
        with pytest.raises(TimeoutError, match="no respondió"):
            fetch_rendered_html_safe("https://example.com", hard_timeout_s=0.1)
