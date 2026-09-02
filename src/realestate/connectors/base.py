"""Interfaz que debe implementar cada conector de portal inmobiliario.

Mirar avisos públicos de propiedades no requiere loguearse ni "aplicar" a
nada, así que el riesgo legal/de cuenta es mucho menor que automatizar una
postulación laboral — pero igual respetá `robots.txt`, un rate limit
razonable, y usá la API oficial del portal si la tiene en vez de scrapear
su HTML. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..models import Property

if TYPE_CHECKING:
    from ..config import SearchCriteria


class RealEstateConnector(ABC):
    """Contrato mínimo para agregar un nuevo portal."""

    name: str = "base"

    @abstractmethod
    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        """Devuelve avisos normalizados como `Property`.

        Implementá acá la búsqueda real (requests a la página de
        resultados, la API oficial del portal si la tiene, parseo de HTML,
        etc.) respetando robots.txt y un rate limit razonable.
        """
