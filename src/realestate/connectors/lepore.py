"""Conector de ejemplo para Lepore Propiedades (lepore.com.ar).

Inmobiliaria. No tengo información técnica confirmada sobre su sitio;
inspeccionalo directamente (`robots.txt`, si depende de JS) antes de
implementar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class LeporeConnector(RealEstateConnector):
    name = "lepore"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda en Lepore respetando robots.txt y un "
            "rate limit razonable."
        )
