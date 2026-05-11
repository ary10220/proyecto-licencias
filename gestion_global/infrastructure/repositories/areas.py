"""Repositorio de Area (CU10). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import GerenciaArea


def list_areas() -> QuerySet[GerenciaArea]:
    return (
        GerenciaArea.objects
        .select_related("empresa", "division")
        .order_by("empresa__nombre", "nombre")
    )


def get_area(pk: int) -> GerenciaArea:
    return get_object_or_404(GerenciaArea, pk=pk)


def delete_area(area: GerenciaArea) -> None:
    area.delete()
