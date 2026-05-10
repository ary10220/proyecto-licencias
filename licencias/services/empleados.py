"""
Servicio de ciclo de vida del empleado.

Reglas de negocio centralizadas:
  - Inhabilitación operativa
  - Cascada de revocación de licencias asignadas (delegada a liberar_licencia)
  - Registro de evento umbrella en bitácora

La cascada está envuelta en @transaction.atomic: si alguna liberación falla,
el empleado.activo = False rollbackea junto con todo el resto.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from empleados.models import Empleado
from bitacora.actions import log_baja_empleado

from ..models import Asignacion
from .asignacion import liberar_licencia
from .exceptions import EmpleadoNoEncontradoError, EmpleadoYaInactivoError


@transaction.atomic
def dar_baja_empleado(empleado_id: int, request) -> dict:
    """Inhabilita un empleado y libera todas sus asignaciones activas.

    Returns:
        {'empleado': Empleado, 'licencias_liberadas': int}
    """
    try:
        empleado = Empleado.objects.get(pk=empleado_id)
    except Empleado.DoesNotExist:
        raise EmpleadoNoEncontradoError(f"Empleado {empleado_id} no existe")

    if not empleado.activo:
        raise EmpleadoYaInactivoError(empleado.nombre_completo)

    empleado.activo = False
    empleado.save()

    motivo = (
        f"Revocación automatizada por baja operativa "
        f"el {timezone.now().strftime('%d/%m/%Y')}."
    )
    asignaciones_ids = list(
        Asignacion.objects
        .filter(empleado=empleado, activo=True)
        .values_list('id', flat=True)
    )
    for asignacion_id in asignaciones_ids:
        liberar_licencia(asignacion_id, motivo, request)

    licencias_liberadas = len(asignaciones_ids)
    log_baja_empleado(request, empleado, licencias_liberadas=licencias_liberadas)

    return {'empleado': empleado, 'licencias_liberadas': licencias_liberadas}
