"""
Casos de uso (capa application) del módulo `user`.

Se organiza por feature en submódulos, pero re-exportamos las funciones
para mantener imports simples desde las views:

    from user.application.use_cases import uc_crear_usuario, ...
"""

from .usuarios import (
    PasswordResetResult,
    uc_crear_usuario,
    uc_editar_usuario,
    uc_listar_usuarios,
    uc_reset_password_usuario,
    uc_toggle_usuario,
)
from .roles import (
    uc_crear_rol,
    uc_editar_rol,
    uc_eliminar_rol,
)
from .perfil import (
    uc_perfil_actualizar_foto,
    uc_perfil_eliminar_foto,
)
from .areas import uc_eliminar_area_usuario
from .cargos import uc_eliminar_cargo

__all__ = [
    'PasswordResetResult',
    'uc_listar_usuarios',
    'uc_crear_usuario',
    'uc_editar_usuario',
    'uc_toggle_usuario',
    'uc_reset_password_usuario',
    'uc_crear_rol',
    'uc_editar_rol',
    'uc_eliminar_rol',
    'uc_perfil_eliminar_foto',
    'uc_perfil_actualizar_foto',
    'uc_eliminar_area_usuario',
    'uc_eliminar_cargo',
]

