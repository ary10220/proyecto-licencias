"""Repositorio de Unidad (CU08). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Unidad


def _filtrar_estado(qs: QuerySet[Unidad], estado: str) -> QuerySet[Unidad]:
    if estado == "inactivos":
        return qs.filter(activo=False)
    if estado == "todos":
        return qs
    return qs.filter(activo=True)


def list_unidades(*, q: str = "", estado: str = "activos") -> QuerySet[Unidad]:
    qs = Unidad.objects.select_related("area", "area__empresa", "area__division")
    qs = _filtrar_estado(qs, estado)
    if q:
        qs = qs.filter(nombre__icontains=q)
    return qs.order_by("area__empresa__nombre", "area__nombre", "nombre")


def get_unidad(pk: int) -> Unidad:
    return get_object_or_404(Unidad, pk=pk)


def set_unidad_activa(unidad: Unidad, activo: bool) -> None:
    unidad.activo = activo
    unidad.save(update_fields=["activo"])
