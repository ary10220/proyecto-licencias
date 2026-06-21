"""
================================================================================
CU - Gestionar licencia
================================================================================
Permite registrar, actualizar, consultar y eliminar licencias del inventario.

Actores:        A1 (Administrador), A3 (Tecnico TI)
Pre-condicion:  Sesion activa con permisos de licencias.
Post-condicion: La accion queda registrada en bitacora.

Reglas de negocio:
  - No se puede eliminar una licencia con asignacion activa.
  - El borrado masivo omite licencias asignadas y opera solo sobre disponibles.
================================================================================
"""

from __future__ import annotations

from bitacora.actions import (
    log_creacion_licencias,
    log_editar_licencia,
    log_eliminar_licencia,
    log_eliminar_licencias_masivo,
)
from ...models import Licencia
from ...infrastructure import repositories as repo


def uc_listar_licencias(**filtros):
    return repo.list_licencias(**filtros)


def uc_crear_licencia(*, request, form) -> Licencia:
    licencia = form.save()
    log_creacion_licencias(request, licencia, cantidad=1)
    return licencia


def uc_editar_licencia(*, request, form, licencia: Licencia) -> Licencia:
    licencia = form.save()
    log_editar_licencia(request, licencia)
    return licencia


def uc_eliminar_licencia(*, request, licencia: Licencia) -> tuple[bool, str]:
    if licencia.asignaciones.filter(activo=True).exists():
        return False, "No se puede deshabilitar una licencia con asignacion activa. Liberala primero."
    licencia_id = licencia.pk
    label = str(licencia)
    licencia.estado_operativo = Licencia.ESTADO_REVOCADA
    licencia.save(update_fields=['estado_operativo'])
    log_eliminar_licencia(request, label, licencia_id=licencia_id)
    return True, f"Licencia '{label}' deshabilitada."


def uc_eliminar_licencias_masivo(*, request, ids: list[int]) -> tuple[int, int]:
    """Borrado masivo. Returns (eliminadas, omitidas)."""
    qs = repo.licencias_por_ids(ids)
    eliminadas = 0
    omitidas = 0
    for licencia in qs:
        if licencia.asignaciones.filter(activo=True).exists():
            omitidas += 1
            continue
        licencia.estado_operativo = Licencia.ESTADO_REVOCADA
        licencia.save(update_fields=['estado_operativo'])
        eliminadas += 1
    if eliminadas:
        log_eliminar_licencias_masivo(request, eliminadas)
    return eliminadas, omitidas
