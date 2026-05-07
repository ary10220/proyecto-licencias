"""
Vistas auxiliares para los filtros avanzados de la bitacora.

Expone endpoints JSON usados por la UI para poblar los selects de
acciones/modulos/usuarios sin tener que hardcodearlos en el template.
"""

from __future__ import annotations

from .base import (
    JsonResponse,
    login_required,
    permiso_requerido,
)

from ...domain.services import ACCIONES, MODULOS
from ...infrastructure.repositories import bitacora as repo


@login_required
@permiso_requerido("bitacora.view_bitacora", json=True)
def opciones_filtros(request):
    """
    Endpoint JSON para poblar los selects del panel de filtros.

    Devuelve:
        - usuarios: lista de usernames distintos.
        - acciones: lista [{value, label}, ...].
        - modulos: lista [{value, label}, ...].
    """
    usuarios = list(repo.distinct_usernames())

    return JsonResponse({
        "usuarios": [u for u in usuarios if u],
        "acciones": [{"value": k, "label": v} for k, v in ACCIONES.items()],
        "modulos": [{"value": k, "label": v} for k, v in MODULOS.items()],
    })
