"""Conector de ejemplo para Properati.

Properati está orientado a datos abiertos de mercado inmobiliario y
históricamente publicó datasets/APIs para investigación. Verificá qué
expone actualmente antes de decidir entre usar una API o scrapear el sitio
de avisos. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class ProperatiConnector(RealEstateConnector):
    name = "properati"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Properati (API de datos si está "
            "disponible, o scraping respetuoso de robots.txt)."
        )
