"""
Servicio de asignación/liberación de licencias.

Reglas de negocio centralizadas:
  - Validación de duplicidad por TipoLicencia
  - Prevención de race condition (licencia ya asignada)
  - Snapshots organizacionales (delegado a Asignacion.save())
  - Registro en bitácora

Las excepciones del módulo (ver exceptions.py) son tipadas para que la
capa de presentación pueda traducir cada caso a un mensaje de usuario.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from empleados.models import Empleado
from bitacora.actions import log_asignacion_licencia, log_liberar_licencia

from ..models import Asignacion, Licencia
from .exceptions import (
    AsignacionInactivaError,
    AsignacionNoEncontradaError,
    EmpleadoNoEncontradoError,
    EmpleadoYaTieneTipoError,
    LicenciaNoEncontradaError,
    LicenciaYaAsignadaError,
)


@transaction.atomic
def asignar_licencia(licencia_id: int, empleado_id: int, request) -> Asignacion:
    """Vincula una licencia a un empleado. Lanza excepciones tipadas."""
    try:
        licencia = Licencia.objects.select_related('tipo').get(pk=licencia_id)
    except Licencia.DoesNotExist:
        raise LicenciaNoEncontradaError(f"Licencia {licencia_id} no existe")

    try:
        empleado = Empleado.objects.get(pk=empleado_id)
    except Empleado.DoesNotExist:
        raise EmpleadoNoEncontradoError(f"Empleado {empleado_id} no existe")

    asignacion_actual = licencia.usuario_activo
    if asignacion_actual is not None:
        raise LicenciaYaAsignadaError(asignacion_actual.empleado.nombre_completo)

    duplicada = Asignacion.objects.filter(
        empleado=empleado, licencia__tipo=licencia.tipo, activo=True
    ).exists()
    if duplicada:
        raise EmpleadoYaTieneTipoError(empleado.nombre_completo, licencia.tipo.nombre)

    asignacion = Asignacion.objects.create(
        licencia=licencia, empleado=empleado, activo=True
    )
    log_asignacion_licencia(request, licencia, empleado)
    return asignacion


@transaction.atomic
def liberar_licencia(asignacion_id: int, motivo: str, request) -> None:
    """Revoca una asignación activa. Persiste motivo en observaciones."""
    try:
        asignacion = Asignacion.objects.select_related(
            'licencia', 'empleado'
        ).get(pk=asignacion_id)
    except Asignacion.DoesNotExist:
        raise AsignacionNoEncontradaError(f"Asignación {asignacion_id} no existe")

    if not asignacion.activo:
        raise AsignacionInactivaError("La asignación ya no está activa")

    asignacion.activo = False
    if not asignacion.fecha_retiro:
        asignacion.fecha_retiro = timezone.now()
    if motivo:
        asignacion.observaciones = motivo
    asignacion.save()

    log_liberar_licencia(
        request,
        asignacion.licencia,
        empleados=[asignacion.empleado.nombre_completo],
        cantidad=1,
    )
