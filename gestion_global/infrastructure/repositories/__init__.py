"""
Repositorios (capa infrastructure) del modulo `gestion_global`.

Cada submodulo expone funciones puras de acceso a datos (querysets,
get/list/delete). NO contienen logica de negocio ni manejan request HTTP.

    from gestion_global.infrastructure import repositories as repo
"""

from .empresas import (
    list_empresas,
    get_empresa,
    delete_empresa,
)
from .tenants import (
    list_tenants,
    get_tenant,
    delete_tenant,
)
from .areas import (
    list_areas,
    get_area,
    delete_area,
)
from .divisiones import (
    list_divisiones,
    get_division,
    delete_division,
)
from .unidades import (
    list_unidades,
    get_unidad,
    delete_unidad,
)

__all__ = [
    "list_empresas", "get_empresa", "delete_empresa",
    "list_tenants", "get_tenant", "delete_tenant",
    "list_areas", "get_area", "delete_area",
    "list_divisiones", "get_division", "delete_division",
    "list_unidades", "get_unidad", "delete_unidad",
]
