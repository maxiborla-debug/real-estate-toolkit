"""Conector de ejemplo para Inmuebles Clarín (inmuebles.clarin.com).

Sección de clasificados inmobiliarios del diario Clarín. No tengo
información técnica confirmada sobre su estructura; inspeccionalo
directamente (`robots.txt`, si depende de JS) antes de implementar. Ver
docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class InmueblesClarinConnector(RealEstateConnector):
    name = "inmuebles_clarin"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Inmuebles Clarín respetando "
            "robots.txt y un rate limit razonable."
        )
