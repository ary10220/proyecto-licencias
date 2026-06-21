"""Repositorio de Proveedor + TipoLicencia (catalogo de licenciamiento)."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ...models import Proveedor, TipoLicencia


def list_proveedores() -> QuerySet[Proveedor]:
    return Proveedor.objects.all().order_by('nombre')


def get_proveedor(pk: int) -> Proveedor:
    return get_object_or_404(Proveedor, pk=pk)


def delete_proveedor(proveedor: Proveedor) -> None:
    proveedor.delete()


def list_tipos_licencia() -> QuerySet[TipoLicencia]:
    return TipoLicencia.objects.all().order_by('fabricante', 'nombre')


def get_tipo_licencia(pk: int) -> TipoLicencia:
    return get_object_or_404(TipoLicencia, pk=pk)


def delete_tipo_licencia(tipo: TipoLicencia) -> None:
    tipo.delete()
