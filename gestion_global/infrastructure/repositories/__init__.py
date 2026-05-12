"""
Repositorios (capa infrastructure) del modulo `gestion_global`.

Cada submodulo expone funciones puras de acceso a datos (querysets,
get/list/delete). NO contienen logica de negocio ni manejan request HTTP.

    from gestion_global.infrastructure import repositories as repo
"""

from .empresas import (
    list_empresas,
    get_empresa,
    set_empresa_activa,
)
from .tenants import (
    list_tenants,
    get_tenant,
    set_tenant_activo,
)
from .areas import (
    list_areas,
    get_area,
    set_area_activa,
)
from .divisiones import (
    list_divisiones,
    get_division,
    set_division_activa,
)
from .unidades import (
    list_unidades,
    get_unidad,
    set_unidad_activa,
)

__all__ = [
    "list_empresas", "get_empresa", "set_empresa_activa",
    "list_tenants", "get_tenant", "set_tenant_activo",
    "list_areas", "get_area", "set_area_activa",
    "list_divisiones", "get_division", "set_division_activa",
    "list_unidades", "get_unidad", "set_unidad_activa",
]
