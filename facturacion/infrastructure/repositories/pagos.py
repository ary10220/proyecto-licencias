"""Repositorio de pagos de facturacion."""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from ..models import Factura, PagoFactura


def list_facturas_para_pagos(
    *,
    q: str = "",
    estado_pago: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    metodo_pago: str = "todos",
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
) -> QuerySet[Factura]:
    qs = (
        Factura.objects
        .select_related('tenant', 'empresa', 'proveedor', 'propuesta')
        .prefetch_related('pagos', 'detalles__tipo_licencia')
        .exclude(estado='BORRADOR')
    )
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if metodo_pago and metodo_pago != 'todos':
        qs = qs.filter(Q(metodo_pago=metodo_pago) | Q(pagos__metodo_pago=metodo_pago))
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if q:
        qs = qs.filter(
            Q(numero__icontains=q)
            | Q(empresa__nombre__icontains=q)
            | Q(tenant__nombre__icontains=q)
            | Q(razon_social__icontains=q)
            | Q(nit__icontains=q)
            | Q(propuesta__numero__icontains=q)
            | Q(pagos__referencia__icontains=q)
        )

    facturas = qs.distinct().order_by('-fecha', '-id')
    if estado_pago and estado_pago != 'todos':
        estado_pago = estado_pago.upper()
        ids = [factura.id for factura in facturas if factura.estado_pago_calculado == estado_pago]
        facturas = facturas.filter(id__in=ids)
    return facturas


def list_pagos_recientes(
    *,
    q: str = "",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    metodo_pago: str = "todos",
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    limit: int = 50,
) -> QuerySet[PagoFactura]:
    qs = (
        PagoFactura.objects
        .select_related('factura', 'factura__tenant', 'factura__empresa', 'creado_por')
    )
    if tenant_id:
        qs = qs.filter(factura__tenant_id=tenant_id)
    if empresa_id:
        qs = qs.filter(factura__empresa_id=empresa_id)
    if metodo_pago and metodo_pago != 'todos':
        qs = qs.filter(metodo_pago=metodo_pago)
    if fecha_desde:
        qs = qs.filter(fecha_pago__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_pago__lte=fecha_hasta)
    if q:
        qs = qs.filter(
            Q(factura__numero__icontains=q)
            | Q(factura__empresa__nombre__icontains=q)
            | Q(factura__tenant__nombre__icontains=q)
            | Q(referencia__icontains=q)
            | Q(observaciones__icontains=q)
        )
    return qs.order_by('-fecha_pago', '-id')[:limit]


def get_pago(pk: int) -> PagoFactura:
    return get_object_or_404(PagoFactura, pk=pk)
