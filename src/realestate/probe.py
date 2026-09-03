"""Sonda de reachability: antes de invertir tiempo escribiendo el parser
completo de un portal, conviene saber si ese sitio directamente bloquea el
tráfico que sale desde donde corre el scan (ver docs/PLATAFORMAS.md — ya
confirmamos que MercadoLibre bloquea con 403 desde los runners de GitHub
Actions). Esto NO hace scraping de datos: es sólo un GET simple a la home
de cada sitio, para ver el status code y si hay señales obvias de bloqueo.
"""
from __future__ import annotations

import requests

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

SITES: dict[str, str] = {
    "mercadolibre": "https://www.mercadolibre.com.ar/c/inmuebles",
    "argenprop": "https://www.argenprop.com/",
    "zonaprop": "https://www.zonaprop.com.ar/",
    "remax": "https://www.remax.com.ar/",
    "mudafy": "https://mudafy.com.ar/",
    "cabaprop": "https://cabaprop.com.ar/",
    "buscadorprop": "https://www.buscadorprop.com.ar/",
    "toribio_achaval": "https://toribioachaval.com/",
    "inmuebles_clarin": "https://www.inmuebles.clarin.com/",
    "soloduenos": "https://www.soloduenos.com/",
    "buscainmueble": "https://www.buscainmueble.com/",
    "lepore": "https://lepore.com.ar/",
}

# Frases específicas de una página de desafío/bloqueo real, no de un simple
# widget de reCAPTCHA en un formulario de login (eso es normal y aparece en
# sitios sin ningún bloqueo — "captcha" o "cloudflare" sueltos daban falsos
# positivos: confirmado en Argenprop, cuyo único "captcha" de la página es
# el de su popup de registro, sin relación con scraping).
_BLOCK_MARKERS = (
    "access denied",
    "attention required! | cloudflare",
    "checking your browser before accessing",
    "verifying you are human",
    "please wait while we verify",
    "pardon our interruption",
    "unusual traffic",
    "bot detection",
)


def probe_site(name: str, url: str, use_browser: bool = False) -> dict:
    if use_browser:
        from .browser import fetch_rendered_html

        try:
            text = fetch_rendered_html(url)
        except Exception as exc:  # cualquier falla de Playwright (timeout, navegación, etc.)
            return {"source": name, "url": url, "status": None, "error": repr(exc), "mode": "browser"}
        text_lower = text.lower()
        return {
            "source": name,
            "url": url,
            "status": 200,  # si Playwright no tiró error, la página cargó
            "length": len(text),
            "blocked_hint": any(marker in text_lower for marker in _BLOCK_MARKERS),
            "mode": "browser",
        }

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
    except requests.RequestException as exc:
        return {"source": name, "url": url, "status": None, "error": repr(exc), "mode": "requests"}

    text_lower = response.text.lower() if response.status_code == 200 else ""
    return {
        "source": name,
        "url": url,
        "status": response.status_code,
        "length": len(response.content),
        "blocked_hint": any(marker in text_lower for marker in _BLOCK_MARKERS) if text_lower else None,
        "mode": "requests",
    }


def probe_all(use_browser: bool = False) -> list[dict]:
    return [probe_site(name, url, use_browser=use_browser) for name, url in SITES.items()]
