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

from bitacora.actions import log_division_crear, log_division_editar, log_division_eliminar
from ...infrastructure import repositories as repo
from ...infrastructure.models import GerenciaDivision


def uc_listar_divisiones():
    return repo.list_divisiones()


def uc_crear_division(*, request, form) -> GerenciaDivision:
    division = form.save()
    log_division_crear(request, division)
    return division


def uc_editar_division(*, request, form, division: GerenciaDivision) -> GerenciaDivision:
    division = form.save()
    log_division_editar(request, division)
    return division


def uc_eliminar_division(*, request, division: GerenciaDivision) -> str:
    label = str(division)
    repo.delete_division(division)
    log_division_eliminar(request, label)
    return label
