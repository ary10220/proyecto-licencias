"""Repositorio de Factura (CU - Gestionar factura)."""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from ..models import Factura


def list_facturas(
    *,
    q: str = "",
    estado: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    tipo_id: str | None = None,
    stock: str = "todos",
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
) -> QuerySet[Factura]:
    """Lista facturas con filtros de busqueda y estado."""
    qs = (
        Factura.objects
        .select_related('proveedor', 'tenant', 'empresa', 'propuesta')
        .prefetch_related('detalles__tipo_licencia')
    )
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if tipo_id:
        qs = qs.filter(detalles__tipo_licencia_id=tipo_id)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if estado and estado != "todos":
        qs = qs.filter(estado=estado.upper())
    if stock == "generado":
        qs = qs.filter(stock_generado=True)
    elif stock == "pendiente":
        qs = qs.filter(stock_generado=False)
    if q:
        qs = qs.filter(
            Q(numero__icontains=q)
            | Q(empresa__nombre__icontains=q)
            | Q(tenant__nombre__icontains=q)
            | Q(razon_social__icontains=q)
            | Q(nit__icontains=q)
            | Q(propuesta__numero__icontains=q)
            | Q(detalles__tipo_licencia__nombre__icontains=q)
            | Q(detalles__tipo_licencia__fabricante__icontains=q)
        )
    return qs.distinct().order_by('-fecha', '-id')


def get_factura(pk: int) -> Factura:
    return get_object_or_404(Factura, pk=pk)


def delete_factura(factura: Factura) -> None:
    factura.delete()


def distinct_estados_factura() -> list[tuple[str, str]]:
    return list(Factura.ESTADOS)
