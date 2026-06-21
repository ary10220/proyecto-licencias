"""Repositorio de Licencia (CRUD operativo)."""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from ...models import Licencia


def list_licencias(
    *,
    tenant_id: int | None = None,
    empresa_id: int | None = None,
    proveedor_id: int | None = None,
    tipo_id: int | None = None,
    estado: str = "",
    q: str = "",
    fecha_desde=None,
    fecha_hasta=None,
) -> QuerySet[Licencia]:
    """Lista licencias optimizada con select_related para evitar N+1."""
    qs = Licencia.objects.select_related(
        'tipo',
        'empresa',
        'tenant',
        'proveedor',
        'factura_origen',
    ).prefetch_related('asignaciones__empleado')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if proveedor_id:
        qs = qs.filter(proveedor_id=proveedor_id)
    if tipo_id:
        qs = qs.filter(tipo_id=tipo_id)
    if fecha_desde:
        qs = qs.filter(fecha_vencimiento__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_vencimiento__lte=fecha_hasta)
    if q:
        qs = qs.filter(
            Q(tipo__nombre__icontains=q)
            | Q(tipo__fabricante__icontains=q)
            | Q(tipo__codigo__icontains=q)
            | Q(empresa__nombre__icontains=q)
            | Q(tenant__nombre__icontains=q)
            | Q(proveedor__nombre__icontains=q)
            | Q(factura_origen__numero__icontains=q)
        )
    if estado:
        if estado == Licencia.ESTADO_ASIGNADA:
            qs = qs.filter(asignaciones__activo=True)
        elif estado == Licencia.ESTADO_VENCIDA:
            from django.utils import timezone
            qs = qs.filter(fecha_vencimiento__lt=timezone.now().date())
        elif estado == 'POR_VENCER':
            from datetime import timedelta
            from django.utils import timezone
            hoy = timezone.now().date()
            qs = qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hoy + timedelta(days=30))
        elif estado == Licencia.ESTADO_DISPONIBLE:
            from django.utils import timezone
            qs = qs.filter(
                estado_operativo=Licencia.ESTADO_DISPONIBLE,
                fecha_vencimiento__gte=timezone.now().date(),
            ).exclude(asignaciones__activo=True)
        else:
            qs = qs.filter(estado_operativo=estado)
    return qs.distinct().order_by('fecha_vencimiento', 'tipo__nombre')


def get_licencia(pk: int) -> Licencia:
    return get_object_or_404(Licencia, pk=pk)


def delete_licencia(licencia: Licencia) -> None:
    licencia.delete()


def licencias_por_ids(ids: list[int]) -> QuerySet[Licencia]:
    return Licencia.objects.filter(id__in=ids)
