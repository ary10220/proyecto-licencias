from __future__ import annotations

from django.contrib.auth.models import Group

from bitacora.actions import (
    log_rol_crear,
    log_rol_editar,
    log_rol_eliminar,
)

from ...infrastructure import repositories as repo


def uc_crear_rol(request, form) -> Group:
    rol = form.save()
    log_rol_crear(request, rol)
    return rol


def uc_editar_rol(request, form) -> Group:
    rol = form.save()
    log_rol_editar(request, rol)
    return rol


def uc_eliminar_rol(request, rol: Group) -> tuple[str, int]:
    nombre = rol.name
    total_permisos = repo.count_permisos_rol(rol)
    rol.delete()
    log_rol_eliminar(request, nombre, total_permisos)
    return nombre, total_permisos

