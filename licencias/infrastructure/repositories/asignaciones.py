"""Repositorio de Asignacion."""

from __future__ import annotations

from ...models import Asignacion, Licencia


def asignacion_activa_de(licencia: Licencia) -> Asignacion | None:
    return licencia.asignaciones.filter(activo=True).first()


def historial_asignaciones(licencia: Licencia):
    return licencia.asignaciones.select_related('empleado').order_by('-fecha_asignacion')
