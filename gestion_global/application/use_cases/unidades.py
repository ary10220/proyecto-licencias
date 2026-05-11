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

from bitacora.actions import log_unidad_crear, log_unidad_editar, log_unidad_eliminar
from ...infrastructure import repositories as repo
from ...infrastructure.models import Unidad


def uc_listar_unidades():
    return repo.list_unidades()


def uc_crear_unidad(*, request, form) -> Unidad:
    unidad = form.save()
    log_unidad_crear(request, unidad)
    return unidad


def uc_editar_unidad(*, request, form, unidad: Unidad) -> Unidad:
    unidad = form.save()
    log_unidad_editar(request, unidad)
    return unidad


def uc_eliminar_unidad(*, request, unidad: Unidad) -> str:
    label = str(unidad)
    repo.delete_unidad(unidad)
    log_unidad_eliminar(request, label)
    return label
