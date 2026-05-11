"""Repositorio de Empresa (CU07)."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Empresa


def list_empresas() -> QuerySet[Empresa]:
    """Lista todas las empresas con su tenant precargado."""
    return Empresa.objects.select_related("tenant").order_by("tenant__nombre", "nombre")


def get_empresa(pk: int) -> Empresa:
    return get_object_or_404(Empresa, pk=pk)


def delete_empresa(empresa: Empresa) -> None:
    empresa.delete()
