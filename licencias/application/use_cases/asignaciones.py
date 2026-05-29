"""
================================================================================
CU - Asignar / Liberar licencia
================================================================================
Permite asignar una licencia disponible a un empleado, o liberarla.

Reglas:
  - No se puede asignar una licencia ya asignada activamente (race condition).
  - No se puede asignar a un empleado que ya tiene el mismo TipoLicencia activo
    (duplicidad de licenciamiento).
  - Liberar marca la asignacion como inactiva (no la borra) y graba fecha_retiro.
================================================================================
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from bitacora.actions import log_asignacion_licencia, log_liberar_licencia
from ...models import Asignacion, Licencia
from empleados.models import Empleado


def uc_asignar_licencia(*, request, licencia: Licencia, empleado: Empleado) -> tuple[bool, str]:
    """Asigna licencia a empleado validando concurrencia y duplicidad por tipo."""
    with transaction.atomic():
        licencia = Licencia.objects.select_for_update().select_related('empresa', 'tenant', 'tipo').get(pk=licencia.pk)

        if not licencia.puede_asignarse:
            return False, f"La licencia no esta disponible para asignacion (estado: {licencia.estado})."

        if licencia.empresa_id and empleado.empresa_id != licencia.empresa_id:
            return False, "Validacion multi-tenant: el empleado pertenece a otra empresa."

        if licencia.empresa_id and licencia.empresa.tenant_id != licencia.tenant_id:
            return False, "Inconsistencia: la empresa de la licencia no pertenece al tenant registrado."

        if getattr(empleado, 'empresa_id', None) and empleado.empresa.tenant_id != licencia.tenant_id:
            return False, "Validacion multi-tenant: el empleado pertenece a otro tenant."

        if licencia.asignaciones.filter(activo=True).exists():
            activa = licencia.asignaciones.filter(activo=True).select_related('empleado').first()
            nombre = getattr(getattr(activa, 'empleado', None), 'nombre_completo', 'otro empleado')
            return False, f"Violacion de concurrencia: la licencia ya esta asignada a {nombre}."

        tiene_duplicada = Asignacion.objects.filter(
            empleado=empleado,
            licencia__tipo=licencia.tipo,
            activo=True,
        ).exists()
        if tiene_duplicada:
            return False, f"Regla de negocio: {empleado.nombre_completo} ya posee una instancia activa de '{licencia.tipo.nombre}'."

        Asignacion.objects.create(
            licencia=licencia,
            empleado=empleado,
            estado='ASIGNADA',
            activo=True,
        )
        licencia.estado_operativo = Licencia.ESTADO_ASIGNADA
        licencia.save(update_fields=['estado_operativo'])
    log_asignacion_licencia(request, licencia, empleado)
    return True, f"Transaccion exitosa: licencia asignada a {empleado.nombre_completo}."


def uc_liberar_licencia(*, request, licencia: Licencia) -> tuple[bool, str, int]:
    """Marca todas las asignaciones activas como liberadas. Returns (ok, msg, cantidad)."""
    asignaciones_activas = licencia.asignaciones.filter(activo=True).select_related('empleado')
    if not asignaciones_activas.exists():
        return False, "El activo no presentaba asignaciones activas.", 0

    empleados_afectados = [
        getattr(asig.empleado, 'nombre_completo', str(asig.empleado))
        for asig in asignaciones_activas
    ]
    count = 0
    with transaction.atomic():
        for asignacion in asignaciones_activas:
            asignacion.estado = 'LIBERADA'
            asignacion.activo = False
            if not asignacion.fecha_retiro:
                asignacion.fecha_retiro = timezone.now()
            asignacion.save()
            count += 1
        licencia.estado_operativo = (
            Licencia.ESTADO_VENCIDA if licencia.esta_vencida else Licencia.ESTADO_DISPONIBLE
        )
        licencia.save(update_fields=['estado_operativo'])

    log_liberar_licencia(request, licencia, empleados=empleados_afectados, cantidad=count)
    return True, f"Activo revocado. Se consolidaron {count} registros en la bitacora.", count
