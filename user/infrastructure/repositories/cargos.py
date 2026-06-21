from __future__ import annotations

from django.db.models import QuerySet

from empleados.models import Cargo


def list_cargos() -> QuerySet[Cargo]:
    # Orden estable por ID (coherente con Usuarios/Roles en pantallas de gestión).
    return Cargo.objects.select_related('area_usuario').order_by('id')


def get_cargo(cargo_id: int) -> Cargo:
    return Cargo.objects.get(id=cargo_id)
