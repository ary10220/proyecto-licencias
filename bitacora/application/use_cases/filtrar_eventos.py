"""
Caso de uso: aplicar filtros a un queryset de eventos de bitacora.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db.models import QuerySet


@dataclass(frozen=True)
class BitacoraFiltro:
    usuario: Optional[str] = None
    accion: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None


def aplicar_filtros(qs: QuerySet, *, filtro: BitacoraFiltro) -> QuerySet:
    if filtro.usuario:
        qs = qs.filter(usuario__username=filtro.usuario)
    if filtro.accion:
        qs = qs.filter(accion=filtro.accion)
    if filtro.fecha_inicio:
        qs = qs.filter(fecha__date__gte=filtro.fecha_inicio)
    if filtro.fecha_fin:
        qs = qs.filter(fecha__date__lte=filtro.fecha_fin)
    return qs


def filtro_desde_request(request) -> BitacoraFiltro:
    return BitacoraFiltro(
        usuario=request.GET.get("usuario") or None,
        accion=request.GET.get("accion") or None,
        fecha_inicio=request.GET.get("fecha_inicio") or None,
        fecha_fin=request.GET.get("fecha_fin") or None,
    )
