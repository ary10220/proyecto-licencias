"""Repositorio de Tenant (CU12)."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Tenant


def _filtrar_estado(qs: QuerySet[Tenant], estado: str) -> QuerySet[Tenant]:
    if estado == "inactivos":
        return qs.filter(activo=False)
    if estado == "todos":
        return qs
    return qs.filter(activo=True)


def list_tenants(*, q: str = "", estado: str = "activos") -> QuerySet[Tenant]:
    qs = _filtrar_estado(Tenant.objects.all(), estado)
    if q:
        qs = qs.filter(nombre__icontains=q)
    return qs.order_by("nombre")


def get_tenant(pk: int) -> Tenant:
    return get_object_or_404(Tenant, pk=pk)


def set_tenant_activo(tenant: Tenant, activo: bool) -> None:
    tenant.activo = activo
    tenant.save(update_fields=["activo"])
