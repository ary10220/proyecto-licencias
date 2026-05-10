"""
Selectors: queries de solo-lectura optimizadas para el dashboard y reportes.

Por qué selectors y no services:
  - Services encapsulan ESCRITURAS (mutaciones, reglas de negocio que
    cambian estado).
  - Selectors encapsulan LECTURAS (queries agregadas, joins eficientes).
  - Separar ambos hace explícito qué tiene side-effects y qué no.

Cada selector debe resolverse en una sola query SQL siempre que sea posible.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Optional, Union

from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from .models import Asignacion, Licencia, Tenant


def obtener_kpis_dashboard(tenant: Optional[Union[Tenant, int]] = None) -> dict:
    """Calcula los KPIs del dashboard en una sola query agregada.

    Args:
        tenant: Tenant o tenant_id para filtrar; None devuelve KPIs globales.

    Returns:
        dict con keys:
          - 'total': cantidad de licencias.
          - 'ocupadas': licencias con >=1 asignación activa.
          - 'disponibles': licencias SIN asignación activa Y fecha_vencimiento >= hoy.
          - 'vencidas': fecha_vencimiento < hoy.
          - 'por_vencer': fecha_vencimiento entre hoy y hoy+30 (incluye ambos extremos).
    """
    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)

    qs = Licencia.objects.all()
    if tenant is not None:
        qs = qs.filter(tenant=tenant)

    active_subq = Asignacion.objects.filter(licencia=OuterRef('pk'), activo=True)

    return qs.annotate(tiene_activa=Exists(active_subq)).aggregate(
        total=Count('id'),
        ocupadas=Count('id', filter=Q(tiene_activa=True)),
        disponibles=Count(
            'id',
            filter=Q(tiene_activa=False, fecha_vencimiento__gte=hoy),
        ),
        vencidas=Count('id', filter=Q(fecha_vencimiento__lt=hoy)),
        por_vencer=Count(
            'id',
            filter=Q(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite_30_dias),
        ),
    )
