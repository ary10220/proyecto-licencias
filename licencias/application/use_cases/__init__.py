"""
Casos de uso (capa application) del modulo `licencias`.

Cada submodulo agrupa CUs relacionados:

    licencias.py      -> CU - Gestionar licencia (CRUD)
    asignaciones.py   -> CU - Asignar/liberar licencia a empleado
    catalogo.py       -> CU - Gestionar catalogo (Proveedor + TipoLicencia)

Re-export para imports cortos:

    from licencias.application.use_cases import uc_crear_licencia
"""

from .licencias import (
    uc_listar_licencias,
    uc_crear_licencia,
    uc_editar_licencia,
    uc_eliminar_licencia,
    uc_eliminar_licencias_masivo,
)
from .asignaciones import (
    uc_asignar_licencia,
    uc_liberar_licencia,
)
from .catalogo import (
    uc_listar_proveedores,
    uc_crear_proveedor,
    uc_editar_proveedor,
    uc_eliminar_proveedor,
    uc_listar_tipos_licencia,
    uc_crear_tipo_licencia,
    uc_editar_tipo_licencia,
    uc_eliminar_tipo_licencia,
)

__all__ = [
    "uc_listar_licencias", "uc_crear_licencia", "uc_editar_licencia",
    "uc_eliminar_licencia", "uc_eliminar_licencias_masivo",
    "uc_asignar_licencia", "uc_liberar_licencia",
    "uc_listar_proveedores", "uc_crear_proveedor", "uc_editar_proveedor", "uc_eliminar_proveedor",
    "uc_listar_tipos_licencia", "uc_crear_tipo_licencia", "uc_editar_tipo_licencia", "uc_eliminar_tipo_licencia",
]
