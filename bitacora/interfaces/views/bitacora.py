from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from ...application.use_cases.listar_eventos import BitacoraFiltro, uc_listar_bitacora


@login_required
def lista_bitacora(request):
    if not request.user.has_perm("bitacora.view_bitacora"):
        raise PermissionDenied

    filtro = BitacoraFiltro(
        usuario=request.GET.get("usuario") or None,
        accion=request.GET.get("accion") or None,
        fecha_inicio=request.GET.get("fecha_inicio") or None,
        fecha_fin=request.GET.get("fecha_fin") or None,
    )

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

