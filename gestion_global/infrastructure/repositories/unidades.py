"""Repositorio de Unidad (CU08). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Unidad


def list_unidades() -> QuerySet[Unidad]:
    return Unidad.objects.select_related("area").order_by("area__nombre", "nombre")


def get_unidad(pk: int) -> Unidad:
    return get_object_or_404(Unidad, pk=pk)


def delete_unidad(unidad: Unidad) -> None:
    unidad.delete()
