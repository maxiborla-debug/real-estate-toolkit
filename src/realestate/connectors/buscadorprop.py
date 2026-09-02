"""Conector de ejemplo para BuscadorProp (buscadorprop.com.ar).

Por el nombre parecería ser un meta-buscador que agrega avisos de varios
portales — si es así, ojo con terminar scrapeando datos que ya venís
sacando de la fuente original (duplicados). No tengo información técnica
confirmada sobre el sitio; inspeccionalo directamente antes de implementar.
Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class BuscadorpropConnector(RealEstateConnector):
    name = "buscadorprop"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en BuscadorProp respetando robots.txt "
            "y un rate limit razonable. Revisá si duplica avisos de otras "
            "fuentes que ya tengas activas."
        )
