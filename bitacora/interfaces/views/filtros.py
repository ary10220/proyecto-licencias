"""
Vista auxiliar: opciones de filtros (endpoint AJAX).
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
    usuarios = list(repo.distinct_usernames())
    return JsonResponse({
        "usuarios": [u for u in usuarios if u],
        "acciones": [{"value": k, "label": v} for k, v in ACCIONES.items()],
        "modulos": [{"value": k, "label": v} for k, v in MODULOS.items()],
    })
