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

from bitacora.actions import log_area_crear, log_area_editar, log_area_eliminar
from ...infrastructure import repositories as repo
from ...infrastructure.models import GerenciaArea


def uc_listar_areas():
    return repo.list_areas()


def uc_crear_area(*, request, form) -> GerenciaArea:
    area = form.save()
    log_area_crear(request, area)
    return area


def uc_editar_area(*, request, form, area: GerenciaArea) -> GerenciaArea:
    area = form.save()
    log_area_editar(request, area)
    return area


def uc_eliminar_area(*, request, area: GerenciaArea) -> str:
    label = str(area)
    repo.delete_area(area)
    log_area_eliminar(request, label)
    return label
