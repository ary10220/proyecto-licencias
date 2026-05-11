"""
================================================================================
CU10 - Gestionar Areas (Gestion Global)
================================================================================
Permite administrar el catalogo de areas organizacionales de las empresas
(consultar, actualizar, deshabilitar/eliminar).

Actores:        A1 (Administrador), A4 (Recursos Humanos)
Pre-condicion:  Sesion activa con permisos para gestionar areas.
Post-condicion: El area queda actualizada o deshabilitada/eliminada,
                reflejada en el catalogo y registrada en bitacora.

Excepciones:
  Datos invalidos/duplicados, dependencias que impiden la eliminacion,
  o falta de permisos -> cancela la operacion y muestra error.
================================================================================
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

from bitacora.actions import (
    log_area_crear,
    log_area_editar,
    log_area_eliminar,
    log_area_reactivar,
)
from empleados.models import Empleado
from ...infrastructure import repositories as repo
from ...infrastructure.models import GerenciaArea


def uc_listar_areas(*, q="", estado="activos"):
    return repo.list_areas(q=q, estado=estado)


def uc_crear_area(*, request, form) -> GerenciaArea:
    area = form.save()
    log_area_crear(request, area)
    return area


def uc_editar_area(*, request, form, area: GerenciaArea) -> GerenciaArea:
    area = form.save()
    log_area_editar(request, area)
    return area


def uc_eliminar_area(*, request, area: GerenciaArea) -> str:
    if area.unidades.filter(activo=True).exists():
        raise ValidationError("No se puede inactivar un area con unidades activas.")
    if Empleado.objects.filter(area=area, activo=True).exists():
        raise ValidationError("No se puede inactivar un area con empleados activos.")
    label = str(area)
    repo.set_area_activa(area, False)
    log_area_eliminar(request, label)
    return label


def uc_reactivar_area(*, request, area: GerenciaArea) -> str:
    if not area.empresa.activo:
        raise ValidationError("No se puede reactivar un area cuya empresa esta inactiva.")
    if area.division and not area.division.activo:
        raise ValidationError("No se puede reactivar un area cuya division esta inactiva.")
    repo.set_area_activa(area, True)
    log_area_reactivar(request, area)
    return str(area)
