"""Conector de ejemplo para Mudafy (mudafy.com.ar).

Proptech relativamente nueva, orientada a compra/venta directa. No tengo
confirmado si publica una API pública; probablemente haga falta scrapear
los resultados de búsqueda del sitio. Verificá `robots.txt` y si la página
depende de JS antes de implementar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class MudafyConnector(RealEstateConnector):
    name = "mudafy"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Mudafy respetando robots.txt y un "
            "rate limit razonable."
        )
