"""Repositorio de Division (CU11). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import GerenciaDivision


def _filtrar_estado(qs: QuerySet[GerenciaDivision], estado: str) -> QuerySet[GerenciaDivision]:
    if estado == "inactivos":
        return qs.filter(activo=False)
    if estado == "todos":
        return qs
    return qs.filter(activo=True)


def list_divisiones(*, q: str = "", estado: str = "activos") -> QuerySet[GerenciaDivision]:
    qs = (
        GerenciaDivision.objects
        .select_related("empresa")
    )
    qs = _filtrar_estado(qs, estado)
    if q:
        qs = qs.filter(nombre__icontains=q) | qs.filter(codigo__icontains=q)
    return qs.order_by("empresa__nombre", "nombre")


def get_division(pk: int) -> GerenciaDivision:
    return get_object_or_404(GerenciaDivision, pk=pk)


def set_division_activa(division: GerenciaDivision, activo: bool) -> None:
    division.activo = activo
    division.save(update_fields=["activo"])
