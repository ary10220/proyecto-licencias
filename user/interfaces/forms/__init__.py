"""
Paquete de formularios (capa interfaces) del módulo `user`.

Organizado por feature, re-exporta las clases usadas por las vistas.
"""

from .roles import GroupForm, ROLE_PERMISSION_GROUPS
from .areas import AreaUsuarioForm
from .cargos import CargoForm
from .perfil import FotoPerfilForm
from .usuarios import UserForm

__all__ = [
    'ROLE_PERMISSION_GROUPS',
    'GroupForm',
    'AreaUsuarioForm',
    'CargoForm',
    'FotoPerfilForm',
    'UserForm',
]

