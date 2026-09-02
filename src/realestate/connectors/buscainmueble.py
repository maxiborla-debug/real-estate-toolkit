"""Conector de ejemplo para Busca Inmueble (buscainmueble.com).

No tengo información técnica confirmada sobre este sitio; inspeccionalo
directamente (`robots.txt`, si depende de JS, si agrega avisos de otras
fuentes) antes de implementar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class BuscaInmuebleConnector(RealEstateConnector):
    name = "buscainmueble"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Busca Inmueble respetando "
            "robots.txt y un rate limit razonable."
        )
