"""Conector de ejemplo para Argenprop.

Igual que Zonaprop: sin API pública documentada y resultados renderizados
con JavaScript. Mismas recomendaciones de rate limiting y robots.txt — ver
docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class ArgenpropConnector(RealEstateConnector):
    name = "argenprop"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Argenprop respetando robots.txt y "
            "un rate limit razonable."
        )
