"""Conector de ejemplo para MercadoLibre Inmuebles.

A diferencia de Zonaprop/Argenprop, MercadoLibre publica una API REST
pública (`api.mercadolibre.com`) que no requiere autenticación para
consultas de lectura básicas — es el punto de partida más sólido de los
cuatro portales. Antes de implementar, confirmá contra la documentación
vigente de MercadoLibre el ID de categoría de "Inmuebles" y los parámetros
de búsqueda disponibles (ubicación, operación, precio, etc.), ya que pueden
cambiar. Ver docs/PLATAFORMAS.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import Property
from .base import RealEstateConnector

if TYPE_CHECKING:
    from ..config import SearchCriteria


class MercadoLibreConnector(RealEstateConnector):
    name = "mercadolibre"

    def search_listings(self, criteria: "SearchCriteria") -> list[Property]:
        raise NotImplementedError(
            "Implementá la búsqueda contra la API pública de MercadoLibre "
            "(api.mercadolibre.com) para la categoría de Inmuebles vigente, "
            "normalizando cada resultado a `Property`."
        )
