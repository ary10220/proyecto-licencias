"""
================================================================================
CU - Gestionar propuesta comercial
================================================================================
Permite registrar, actualizar, aprobar, rechazar y eliminar propuestas
comerciales (cotizaciones) emitidas a un cliente.

Actores:        A1 (Administrador), A2 (Ejecutivo Comercial)
Pre-condicion:  Sesion activa con permisos sobre propuestas.
Post-condicion: La accion queda registrada en bitacora.

Flujo principal (crear/editar):
  1. El actor accede a la vista Propuestas.
  2. Selecciona crear o editar y completa el form con el detalle de items.
  3. La vista delega al use case (este modulo).
  4. El use case persiste la cotizacion + detalles dentro de una transaccion.
  5. La accion se registra en bitacora.

Flujo de aprobacion/rechazo:
  - Una propuesta PENDIENTE puede pasar a APROBADA o RECHAZADA.
  - Una propuesta APROBADA puede facturarse (cambia a FACTURADA al
    emitir la factura asociada).
  - Una propuesta RECHAZADA o FACTURADA NO puede aprobarse de nuevo.

Excepciones:
  - Detalles vacios o cantidades invalidas -> rechazado por el formset.
  - Empresa no pertenece al tenant -> rechazado por el form.
================================================================================
"""

from __future__ import annotations

from django.db import transaction

from bitacora.actions import (
    log_propuesta_aprobar,
    log_propuesta_crear,
    log_propuesta_editar,
    log_propuesta_eliminar,
    log_propuesta_rechazar,
)
from ...infrastructure import repositories as repo
from ...infrastructure.models import PropuestaLicencia


def uc_listar_propuestas(
    *,
    q: str = "",
    estado: str = "todos",
    tenant_id: str | None = None,
    empresa_id: str | None = None,
    tipo_id: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    """Devuelve queryset filtrado para mostrar en pantalla."""
    return repo.list_propuestas(
        q=q,
        estado=estado,
        tenant_id=tenant_id,
        empresa_id=empresa_id,
        tipo_id=tipo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


def uc_crear_propuesta(*, request, propuesta_form, detalle_formset) -> PropuestaLicencia:
    """Guarda propuesta + detalles en transaccion + log bitacora."""
    with transaction.atomic():
        propuesta = propuesta_form.save()
        detalle_formset.instance = propuesta
        detalle_formset.save()
    log_propuesta_crear(request, propuesta)
    return propuesta


def uc_editar_propuesta(*, request, propuesta_form, detalle_formset) -> PropuestaLicencia:
    """Actualiza propuesta + detalles en transaccion + log bitacora."""
    with transaction.atomic():
        propuesta = propuesta_form.save()
        detalle_formset.save()
    log_propuesta_editar(request, propuesta)
    return propuesta


def uc_actualizar_propuesta_administrativa(*, request, propuesta_form) -> PropuestaLicencia:
    """Actualiza solo estado y observaciones de una cotizacion aprobada."""
    propuesta = propuesta_form.save()
    log_propuesta_editar(request, propuesta)
    return propuesta


def uc_aprobar_propuesta(*, request, propuesta: PropuestaLicencia) -> tuple[bool, str]:
    """
    Cambia estado a APROBADA.
    Regla: solo se puede aprobar una cotizacion PENDIENTE.

    Retorna: (ok, mensaje_para_usuario)
    """
    if propuesta.estado != 'PENDIENTE':
        return False, f"No se puede aprobar una cotizacion {propuesta.get_estado_display().lower()}."
    propuesta.estado = 'APROBADA'
    propuesta.save(update_fields=['estado'])
    log_propuesta_aprobar(request, propuesta)
    return True, f"Cotizacion {propuesta.numero} aprobada."


def uc_rechazar_propuesta(*, request, propuesta: PropuestaLicencia) -> tuple[bool, str]:
    """
    Cambia estado a RECHAZADA.
    Regla: solo se puede rechazar una cotizacion PENDIENTE.
    """
    if propuesta.estado != 'PENDIENTE':
        return False, f"No se puede rechazar una cotizacion {propuesta.get_estado_display().lower()}."
    propuesta.estado = 'RECHAZADA'
    propuesta.save(update_fields=['estado'])
    log_propuesta_rechazar(request, propuesta)
    return True, f"Cotizacion {propuesta.numero} rechazada."


def uc_eliminar_propuesta(*, request, propuesta: PropuestaLicencia) -> tuple[bool, str]:
    """
    Borrado fisico de la cotizacion.
    Regla: una cotizacion APROBADA, FACTURADA o ANULADA no puede eliminarse.
    """
    if propuesta.estado in {'APROBADA', 'FACTURADA', 'ANULADA'}:
        return False, "No se puede eliminar una cotizacion aprobada, facturada o anulada."
    label = str(propuesta)
    repo.delete_propuesta(propuesta)
    log_propuesta_eliminar(request, label)
    return True, f"Propuesta '{label}' eliminada."
