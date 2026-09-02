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

_BLOCK_MARKERS = ("access denied", "captcha", "cloudflare", "attention required", "bot detection")


def probe_site(name: str, url: str) -> dict:
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
    except requests.RequestException as exc:
        return {"source": name, "url": url, "status": None, "error": repr(exc)}

    text_lower = response.text.lower() if response.status_code == 200 else ""
    return {
        "source": name,
        "url": url,
        "status": response.status_code,
        "length": len(response.content),
        "blocked_hint": any(marker in text_lower for marker in _BLOCK_MARKERS) if text_lower else None,
    }


def probe_all() -> list[dict]:
    return [probe_site(name, url) for name, url in SITES.items()]
