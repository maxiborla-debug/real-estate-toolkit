"""Modelo normalizado de una propiedad, sin importar de qué portal vino.

Es una dataclass simple a propósito: cualquier conector nuevo puede llenar
sólo los campos que su portal expone y dejar el resto en `None`/lista vacía
— el motor de matching (`matching.py`) sabe ignorar campos sin dato en vez
de penalizarlos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Property:
    id: str
    source: str          # "zonaprop" | "argenprop" | "mercadolibre" | "properati" | ...
    url: str
    operation: str         # "venta" | "alquiler"
    property_type: str      # "departamento" | "casa" | "ph" | "terreno" | ...
    title: str = ""
    price: Optional[float] = None
    currency: str = "ARS"
    neighborhood: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    ambientes: Optional[float] = None
    dormitorios: Optional[float] = None
    banos: Optional[float] = None
    m2_cubiertos: Optional[float] = None
    m2_totales: Optional[float] = None
    antiguedad_anios: Optional[float] = None  # 0 = a estrenar
    amenities: list[str] = field(default_factory=list)   # pileta, gimnasio, sum, seguridad 24hs...
    exterior: list[str] = field(default_factory=list)      # balcon, terraza, patio, jardin
    parking: Optional[int] = None                            # cantidad de cocheras
    servicios: list[str] = field(default_factory=list)        # gas natural, agua corriente, etc.
    posted_at: Optional[datetime] = None
    description: str = ""
    raw: dict = field(default_factory=dict)  # payload original, por si hace falta
