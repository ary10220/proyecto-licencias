"""
Vistas (capa interfaces) del modulo `gestion_global`.

Re-export por feature:

    from gestion_global.interfaces import views
    path(..., views.lista_empresas, ...)
"""

from .empresas import *  # noqa: F401,F403
from .tenants import *  # noqa: F401,F403
from .areas import *  # noqa: F401,F403
from .divisiones import *  # noqa: F401,F403
from .unidades import *  # noqa: F401,F403
