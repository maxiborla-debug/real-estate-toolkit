"""Fetch de páginas con un navegador real (Playwright/Chromium), para los
sitios que exigen ejecutar JavaScript o hacen un desafío anti-bot básico
que un simple `requests.get` no puede pasar.

No resuelve un bloqueo por reputación de IP (eso es un problema de RED, no
de qué tan "real" parece el cliente) — para eso hace falta correr desde una
IP no-datacenter. Pero sí resuelve:
- Sitios SPA que renderizan todo por JS (nada que scrapear en el HTML
  crudo).
- Desafíos básicos tipo "esperá mientras verificamos tu navegador" que
  sólo se resuelven ejecutando JS de verdad.

Uso típico:
    html = fetch_rendered_html("https://ejemplo.com/propiedades")
"""
from __future__ import annotations

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_WAIT_AFTER_LOAD_MS = 2_000  # margen para que terminen los fetch de datos client-side


def fetch_rendered_html(
    url: str,
    wait_selector: str | None = None,
    wait_after_load_ms: int = DEFAULT_WAIT_AFTER_LOAD_MS,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> str:
    """Abre `url` en un Chromium headless y devuelve el HTML ya renderizado.

    `wait_selector`: si se pasa, espera a que ese selector CSS aparezca en
    la página (útil para esperar a que carguen los resultados de una
    búsqueda) en vez de sólo esperar un tiempo fijo.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
            else:
                page.wait_for_timeout(wait_after_load_ms)
            return page.content()
        finally:
            browser.close()
