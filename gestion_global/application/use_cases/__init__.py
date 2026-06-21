"""
Casos de uso (capa application) del modulo `gestion_global`.

Cada submodulo implementa un Caso de Uso del CICLO 2:

    CU07 - Gestionar empresa cliente   -> use_cases/empresas.py
    CU08 - Gestionar unidades          -> use_cases/unidades.py
    CU10 - Gestionar areas             -> use_cases/areas.py
    CU11 - Gestionar divisiones        -> use_cases/divisiones.py
    CU12 - Gestionar tenant            -> use_cases/tenants.py

Re-export para imports cortos:

    from gestion_global.application.use_cases import uc_crear_empresa
"""

from .empresas import (
    uc_listar_empresas,
    uc_crear_empresa,
    uc_editar_empresa,
    uc_eliminar_empresa,
    uc_reactivar_empresa,
)
from .tenants import (
    uc_listar_tenants,
    uc_crear_tenant,
    uc_editar_tenant,
    uc_eliminar_tenant,
    uc_reactivar_tenant,
)
from .areas import (
    uc_listar_areas,
    uc_crear_area,
    uc_editar_area,
    uc_eliminar_area,
    uc_reactivar_area,
)
from .divisiones import (
    uc_listar_divisiones,
    uc_crear_division,
    uc_editar_division,
    uc_eliminar_division,
    uc_reactivar_division,
)
from .unidades import (
    uc_listar_unidades,
    uc_crear_unidad,
    uc_editar_unidad,
    uc_eliminar_unidad,
    uc_reactivar_unidad,
)

__all__ = [
    "uc_listar_empresas", "uc_crear_empresa", "uc_editar_empresa", "uc_eliminar_empresa", "uc_reactivar_empresa",
    "uc_listar_tenants", "uc_crear_tenant", "uc_editar_tenant", "uc_eliminar_tenant", "uc_reactivar_tenant",
    "uc_listar_areas", "uc_crear_area", "uc_editar_area", "uc_eliminar_area", "uc_reactivar_area",
    "uc_listar_divisiones", "uc_crear_division", "uc_editar_division", "uc_eliminar_division", "uc_reactivar_division",
    "uc_listar_unidades", "uc_crear_unidad", "uc_editar_unidad", "uc_eliminar_unidad", "uc_reactivar_unidad",
]
