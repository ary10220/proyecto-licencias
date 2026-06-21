"""Repositorio de PropuestaLicencia (CU - Gestionar propuesta comercial)."""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404

from ..models import PropuestaLicencia


def list_propuestas(
    *,
    q: str = "",
    estado: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    tipo_id: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
) -> QuerySet[PropuestaLicencia]:
    """
    Lista propuestas con filtro de busqueda y estado.

    Args:
        q: texto a buscar en numero, empresa, tenant o producto.
        estado: filtro por estado de la propuesta ('todos', 'PENDIENTE',
                'APROBADA', 'RECHAZADA', 'FACTURADA').
    """
    qs = (
        PropuestaLicencia.objects
        .select_related('empresa', 'tenant')
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
    if q:
        qs = qs.filter(
            Q(numero__icontains=q)
            | Q(empresa__nombre__icontains=q)
            | Q(tenant__nombre__icontains=q)
            | Q(detalles__tipo_licencia__nombre__icontains=q)
            | Q(detalles__tipo_licencia__fabricante__icontains=q)
        )
    return qs.distinct().order_by('-fecha', '-id')


def get_propuesta(pk: int) -> PropuestaLicencia:
    return get_object_or_404(PropuestaLicencia, pk=pk)


def delete_propuesta(propuesta: PropuestaLicencia) -> None:
    propuesta.delete()


def distinct_estados_propuesta() -> list[tuple[str, str]]:
    """Choices estandar de estado para filtros del UI."""
    return list(PropuestaLicencia.ESTADOS)
