"""Conector de ejemplo para Solo Dueños (soloduenos.com).

Portal orientado a avisos publicados directamente por propietarios (sin
inmobiliaria intermediaria). No tengo información técnica confirmada sobre
su sitio; inspeccionalo directamente (`robots.txt`, si depende de JS)
antes de implementar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class SoloDuenosConnector(RealEstateConnector):
    name = "soloduenos"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Solo Dueños respetando robots.txt y "
            "un rate limit razonable."
        )
