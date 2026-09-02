"""Cotización dólar/peso, para poder comparar precios de alquiler publicados
indistintamente en ARS o en USD contra un mismo rango (en vez de descartar
un aviso en USD sólo porque tu rango está en ARS, o viceversa).

Usa la API pública y gratuita de DolarAPI (dolarapi.com), consultando el
dólar "oficial". Si la consulta falla (sin internet, la API caída, etc.),
cae a un valor fijo (`fallback`) para no romper todo el scan por esto —
actualizalo de tanto en tanto en `config.yaml` (`fx_fallback_ars_per_usd`)
si notás que se desactualiza.
"""
from __future__ import annotations

import requests

DOLARAPI_URL = "https://dolarapi.com/v1/dolares/oficial"
DEFAULT_FALLBACK_ARS_PER_USD = 1400.0


def get_ars_per_usd(fallback: float = DEFAULT_FALLBACK_ARS_PER_USD) -> float:
    """Pesos argentinos por cada dólar, al día de hoy (según DolarAPI)."""
    try:
        response = requests.get(DOLARAPI_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["venta"])
    except Exception:
        return fallback
