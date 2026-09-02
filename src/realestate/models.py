"""Modelo normalizado de una propiedad, sin importar de qué portal vino.

Es una dataclass simple a propósito: cualquier conector nuevo puede llenar
sólo los campos que su portal expone y dejar el resto en `None`/lista vacía
— el motor de matching (`matching.py`) sabe ignorar campos sin dato en vez
de penalizarlos (salvo en los campos marcados como filtro obligatorio, ver
docs/CONFIGURACION.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Property:
    id: str
    source: str          # "zonaprop" | "argenprop" | "mercadolibre" | "remax" | ...
    url: str
    operation: str         # "venta" | "alquiler"
    property_type: str      # "departamento" | "casa" | "ph" | "duplex" | "semipiso" | ...
    title: str = ""
    price: Optional[float] = None
    currency: str = "ARS"  # "ARS" | "USD"
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
    exterior: list[str] = field(default_factory=list)      # balcon, terraza, "balcon terraza", patio, jardin
    exterior_m2: Optional[float] = None                      # m2 del balcón/terraza/patio/jardín, si el aviso lo informa
    parking: Optional[int] = None                              # cantidad de cocheras
    servicios: list[str] = field(default_factory=list)          # gas natural, agua corriente, etc.
    apto_credito: Optional[bool] = None                          # sólo relevante para "venta"
    orientacion: Optional[str] = None                             # "norte" | "noreste" | "este" | "oeste" | "sur" | ...
    posted_at: Optional[datetime] = None
    description: str = ""
    raw: dict = field(default_factory=dict)  # payload original, por si hace falta

    @property
    def m2(self) -> Optional[float]:
        """m2 "efectivos" para matchear contra el rango de metros: se usa
        el total si el aviso lo informa, y si no, el cubierto."""
        return self.m2_totales if self.m2_totales is not None else self.m2_cubiertos
