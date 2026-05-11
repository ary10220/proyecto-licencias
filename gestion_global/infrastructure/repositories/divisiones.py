"""Repositorio de Division (CU11). El modelo vive en empleados/."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import GerenciaDivision


def list_divisiones() -> QuerySet[GerenciaDivision]:
    return (
        GerenciaDivision.objects
        .select_related("empresa")
        .order_by("empresa__nombre", "nombre")
    )


def get_division(pk: int) -> GerenciaDivision:
    return get_object_or_404(GerenciaDivision, pk=pk)


def delete_division(division: GerenciaDivision) -> None:
    division.delete()
