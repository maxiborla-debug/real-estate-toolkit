"""Conector de ejemplo para CABAProp (cabaprop.com.ar).

Portal/inmobiliaria enfocada en CABA. No tengo información técnica
confirmada sobre su estructura (API, JS, etc.) — es un sitio más chico que
Zonaprop/Argenprop, así que conviene inspeccionarlo directamente
(`robots.txt`, si el HTML trae los datos ya renderizados o hace falta un
browser) antes de decidir el enfoque. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class CabapropConnector(RealEstateConnector):
    name = "cabaprop"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en CABAProp respetando robots.txt y un "
            "rate limit razonable."
        )
