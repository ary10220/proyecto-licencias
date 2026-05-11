"""Repositorio de Tenant (CU12)."""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from ..models import Tenant


def list_tenants() -> QuerySet[Tenant]:
    return Tenant.objects.all().order_by("nombre")


def get_tenant(pk: int) -> Tenant:
    return get_object_or_404(Tenant, pk=pk)


def delete_tenant(tenant: Tenant) -> None:
    tenant.delete()
