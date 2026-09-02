"""Conector de ejemplo para Zonaprop.

Zonaprop no publica una API pública oficial para terceros. El scraping de
resultados de búsqueda es la vía habitual, pero la página usa bastante
JavaScript: probablemente necesites Playwright/Selenium en vez de sólo
`requests` para que el contenido esté renderizado. Ver docs/PLATAFORMAS.md.

Reemplazá el `raise NotImplementedError` por tu propia implementación,
respetando `robots.txt` y un rate limit razonable.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class ZonapropConnector(RealEstateConnector):
    name = "zonaprop"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Zonaprop (probablemente con "
            "Playwright, dado que la página depende de JS) respetando "
            "robots.txt y un rate limit razonable."
        )
