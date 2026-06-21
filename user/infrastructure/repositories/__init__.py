"""
Repositorio (capa infrastructure) del módulo `user`.

Se organiza por feature en submódulos (usuarios/roles/perfil/areas/cargos),
pero se re-exportan funciones aquí para que los imports sean simples:

    from user.infrastructure import repositories as repo
"""

from .tenants import list_tenants
from .usuarios import (
    get_or_create_perfil,
    get_usuario,
    list_usuarios,
    toggle_usuario_activo,
)
from .roles import (
    count_permisos_rol,
    get_rol,
    get_rol_with_permissions,
    list_permissions_for_codes,
    list_roles,
)
from .areas import (
    delete_area_usuario,
    get_area_usuario,
    list_areas_usuario,
)
from .cargos import (
    get_cargo,
    list_cargos,
)

__all__ = [
    'list_tenants',
    'list_usuarios',
    'get_usuario',
    'toggle_usuario_activo',
    'get_or_create_perfil',
    'list_roles',
    'get_rol',
    'get_rol_with_permissions',
    'count_permisos_rol',
    'list_permissions_for_codes',
    'list_areas_usuario',
    'get_area_usuario',
    'delete_area_usuario',
    'list_cargos',
    'get_cargo',
]

