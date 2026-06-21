"""Repositorio de Area (CU10). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import GerenciaArea


def _filtrar_estado(qs: QuerySet[GerenciaArea], estado: str) -> QuerySet[GerenciaArea]:
    if estado == "inactivos":
        return qs.filter(activo=False)
    if estado == "todos":
        return qs
    return qs.filter(activo=True)


def list_areas(*, q: str = "", estado: str = "activos") -> QuerySet[GerenciaArea]:
    qs = (
        GerenciaArea.objects
        .select_related("empresa", "division")
    )
    qs = _filtrar_estado(qs, estado)
    if q:
        qs = qs.filter(nombre__icontains=q) | qs.filter(codigo__icontains=q)
    return qs.order_by("empresa__nombre", "nombre")


def get_area(pk: int) -> GerenciaArea:
    return get_object_or_404(GerenciaArea, pk=pk)


def set_area_activa(area: GerenciaArea, activo: bool) -> None:
    area.activo = activo
    area.save(update_fields=["activo"])
