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

import threading

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_WAIT_AFTER_LOAD_MS = 2_000  # margen para que terminen los fetch de datos client-side
DEFAULT_HARD_TIMEOUT_S = 45.0  # tope absoluto para fetch_rendered_html_safe


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


def fetch_rendered_html_safe(url: str, hard_timeout_s: float = DEFAULT_HARD_TIMEOUT_S, **kwargs) -> str:
    """Igual que `fetch_rendered_html`, pero nunca puede colgar al proceso
    que la llama más de `hard_timeout_s`.

    Los timeouts internos de Playwright (`timeout_ms` en `page.goto` /
    `page.wait_for_selector`) confiamos en que alcanzan en el caso normal,
    pero si el propio proceso de Chromium o el driver de Playwright quedan
    sin responder a nivel sistema operativo (visto en la práctica: una
    corrida quedó colgada ~15 minutos en una máquina que seguía prendida y
    conectada), esos timeouts no sirven porque nunca llegan a ejecutarse.

    Corre el fetch real en un hilo daemon: si no termina a tiempo, esta
    función devuelve el control igual (con un TimeoutError) y el proceso
    puede seguir con el resto de los sitios — el hilo colgado, si lo hay,
    se abandona (un daemon thread no impide que el proceso termine).
    """
    outcome: dict = {}

    def _run() -> None:
        try:
            outcome["html"] = fetch_rendered_html(url, **kwargs)
        except Exception as exc:  # se re-lanza en el hilo principal, más abajo
            outcome["error"] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=hard_timeout_s)

    if thread.is_alive():
        raise TimeoutError(
            f"fetch_rendered_html no respondió en {hard_timeout_s:.0f}s para {url} "
            "(el navegador probablemente quedó colgado a nivel sistema operativo)"
        )
    if "error" in outcome:
        raise outcome["error"]
    return outcome["html"]
