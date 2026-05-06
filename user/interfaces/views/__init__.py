"""
Paquete de vistas (capa interfaces) del módulo `user`.

Re-export de vistas para que `user.interfaces.urls` pueda hacer:

    from . import views
    path(..., views.mi_perfil, ...)
"""

from .usuarios import *  # noqa: F401,F403
from .roles import *  # noqa: F401,F403
from .perfil import *  # noqa: F401,F403
from .areas import *  # noqa: F401,F403
from .cargos import *  # noqa: F401,F403
from .password import *  # noqa: F401,F403

