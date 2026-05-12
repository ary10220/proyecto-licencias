"""
================================================================================
CU08 - Gestionar Unidades
================================================================================
Permite administrar el catalogo de unidades organizacionales del sistema
(consultar, actualizar y deshabilitar) dentro del modulo de Gestion Global.

Actores:        A1 (Administrador), A4 (Recursos Humanos)
Pre-condicion:  Sesion activa con permisos de gestion de unidades.
Post-condicion: La unidad queda actualizada o deshabilitada correctamente
                y el cambio queda reflejado en el catalogo (y bitacora).

Excepciones:
  Datos invalidos, duplicados, o usuario sin permisos -> rechaza
  la operacion y muestra error.
================================================================================
"""

from __future__ import annotations

from django.core.exceptions import ValidationError

from bitacora.actions import (
    log_unidad_crear,
    log_unidad_editar,
    log_unidad_eliminar,
    log_unidad_reactivar,
)
from empleados.models import Empleado
from ...infrastructure import repositories as repo
from ...infrastructure.models import Unidad


def uc_listar_unidades(*, q="", estado="activos"):
    return repo.list_unidades(q=q, estado=estado)


def uc_crear_unidad(*, request, form) -> Unidad:
    unidad = form.save()
    log_unidad_crear(request, unidad)
    return unidad


def uc_editar_unidad(*, request, form, unidad: Unidad) -> Unidad:
    unidad = form.save()
    log_unidad_editar(request, unidad)
    return unidad


def uc_eliminar_unidad(*, request, unidad: Unidad) -> str:
    if Empleado.objects.filter(unidad=unidad, activo=True).exists():
        raise ValidationError("No se puede inactivar una unidad con empleados activos.")
    label = str(unidad)
    repo.set_unidad_activa(unidad, False)
    log_unidad_eliminar(request, label)
    return label


def uc_reactivar_unidad(*, request, unidad: Unidad) -> str:
    if not unidad.area.activo:
        raise ValidationError("No se puede reactivar una unidad cuya area esta inactiva.")
    repo.set_unidad_activa(unidad, True)
    log_unidad_reactivar(request, unidad)
    return str(unidad)
