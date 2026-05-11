"""
================================================================================
CU11 - Gestionar Divisiones (Gestion Global)
================================================================================
Permite administrar el catalogo de divisiones internas de las empresas
(consultar, actualizar, deshabilitar/eliminar).

Actores:        A1 (Administrador), A4 (Recursos Humanos)
Pre-condicion:  Sesion activa con permisos para gestionar divisiones.
Post-condicion: La division queda actualizada o deshabilitada/eliminada,
                reflejada en el catalogo y registrada en bitacora.

Excepciones:
  Datos invalidos/duplicados, relaciones que impiden la eliminacion o
  falta de permisos -> rechaza la operacion y muestra error.
================================================================================
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

from bitacora.actions import (
    log_division_crear,
    log_division_editar,
    log_division_eliminar,
    log_division_reactivar,
)
from empleados.models import Empleado
from ...infrastructure import repositories as repo
from ...infrastructure.models import GerenciaDivision


def uc_listar_divisiones(*, q="", estado="activos"):
    return repo.list_divisiones(q=q, estado=estado)


def uc_crear_division(*, request, form) -> GerenciaDivision:
    division = form.save()
    log_division_crear(request, division)
    return division


def uc_editar_division(*, request, form, division: GerenciaDivision) -> GerenciaDivision:
    division = form.save()
    log_division_editar(request, division)
    return division


def uc_eliminar_division(*, request, division: GerenciaDivision) -> str:
    if division.areas.filter(activo=True).exists():
        raise ValidationError("No se puede inactivar una division con areas activas.")
    if Empleado.objects.filter(division=division, activo=True).exists():
        raise ValidationError("No se puede inactivar una division con empleados activos.")
    label = str(division)
    repo.set_division_activa(division, False)
    log_division_eliminar(request, label)
    return label


def uc_reactivar_division(*, request, division: GerenciaDivision) -> str:
    if not division.empresa.activo:
        raise ValidationError("No se puede reactivar una division cuya empresa esta inactiva.")
    repo.set_division_activa(division, True)
    log_division_reactivar(request, division)
    return str(division)
