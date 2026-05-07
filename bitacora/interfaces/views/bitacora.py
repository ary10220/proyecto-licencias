"""
Vistas principales del modulo bitacora: listado y detalle de eventos.
"""

from __future__ import annotations

from .base import (
    login_required,
    permiso_requerido,
    render,
)

from ...application.use_cases import (
    filtro_desde_request,
    uc_listar_bitacora,
    uc_ver_detalle_evento,
)
from ...domain.services import (
    clasificar_nivel,
    color_para_accion,
)


@login_required
@permiso_requerido("bitacora.view_bitacora")
def lista_bitacora(request):
    filtro = filtro_desde_request(request)

    page_obj, usuarios = uc_listar_bitacora(
        filtro=filtro,
        is_superuser=bool(request.user.is_superuser),
        username=request.user.username if request.user.is_authenticated else None,
        page=request.GET.get("page"),
        per_page=10,
    )

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "registros": page_obj,
        "page_obj": page_obj,
        "usuarios": usuarios,
        "filtros": request.GET,
        "query_string": query_params.urlencode(),
    }
    return render(request, "bitacora/lista.html", context)


@login_required
@permiso_requerido("bitacora.view_bitacora")
def detalle_evento(request, evento_id: int):
    evento = uc_ver_detalle_evento(
        evento_id=evento_id,
        is_superuser=bool(request.user.is_superuser),
        username=request.user.username if request.user.is_authenticated else None,
    )

    context = {
        "evento": evento,
        "nivel": clasificar_nivel(evento.accion),
        "color": color_para_accion(evento.accion),
        "modulo_label": getattr(evento, "modulo_label", evento.modulo),
    }
    return render(request, "bitacora/detalle.html", context)
