"""
Repositorios (capa infrastructure) del modulo `licencias`.

Cada submodulo expone funciones puras de acceso a datos: querysets,
get_*, list_*, delete_*. SIN logica de negocio, SIN HTTP, SIN request.

    from licencias.infrastructure import repositories as repo
"""

from .licencias import (
    list_licencias,
    get_licencia,
    delete_licencia,
    licencias_por_ids,
)
from .asignaciones import (
    asignacion_activa_de,
    historial_asignaciones,
)
from .catalogo import (
    list_proveedores,
    get_proveedor,
    delete_proveedor,
    list_tipos_licencia,
    get_tipo_licencia,
    delete_tipo_licencia,
)

__all__ = [
    "list_licencias", "get_licencia", "delete_licencia", "licencias_por_ids",
    "asignacion_activa_de", "historial_asignaciones",
    "list_proveedores", "get_proveedor", "delete_proveedor",
    "list_tipos_licencia", "get_tipo_licencia", "delete_tipo_licencia",
]
