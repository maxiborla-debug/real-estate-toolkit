"""Conector de ejemplo para RE/MAX Argentina (remax.com.ar).

Sitio de una franquicia grande, con múltiples oficinas/agentes publicando
avisos. No tiene una API pública documentada para terceros que yo pueda
confirmar — probablemente haya que scrapear los resultados de búsqueda.
Verificá `robots.txt` y el comportamiento real del sitio (si depende de
JS) antes de implementar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class RemaxConnector(RealEstateConnector):
    name = "remax"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en RE/MAX Argentina respetando "
            "robots.txt y un rate limit razonable."
        )
