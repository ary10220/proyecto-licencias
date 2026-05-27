"""Repositorio de Empresa (CU07)."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Empresa


def _filtrar_estado(qs: QuerySet[Empresa], estado: str) -> QuerySet[Empresa]:
    if estado == "inactivos":
        return qs.filter(activo=False)
    if estado == "todos":
        return qs
    return qs.filter(activo=True)


def list_empresas(*, q: str = "", estado: str = "activos") -> QuerySet[Empresa]:
    """Lista todas las empresas con su tenant precargado."""
    qs = Empresa.objects.select_related("tenant")
    qs = _filtrar_estado(qs, estado)
    if q:
        qs = qs.filter(nombre__icontains=q)
    return qs.order_by("tenant__nombre", "nombre")


def get_empresa(pk: int) -> Empresa:
    return get_object_or_404(Empresa, pk=pk)


def set_empresa_activa(empresa: Empresa, activo: bool) -> None:
    empresa.activo = activo
    empresa.save(update_fields=["activo"])
