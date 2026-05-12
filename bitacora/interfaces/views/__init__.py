"""
Paquete de vistas (capa interfaces) del modulo `bitacora`.
"""

from .bitacora import detalle_evento, lista_bitacora  # noqa: F401
from .filtros import opciones_filtros  # noqa: F401

__all__ = [
    "lista_bitacora",
    "detalle_evento",
    "opciones_filtros",
]
