from __future__ import annotations

from django.db.models import QuerySet

from ...models import AreaUsuario


def list_areas_usuario() -> QuerySet[AreaUsuario]:
    return AreaUsuario.objects.prefetch_related('cargos').order_by('nombre')


def get_area_usuario(area_id: int) -> AreaUsuario:
    return AreaUsuario.objects.get(id=area_id)


def delete_area_usuario(area: AreaUsuario) -> tuple[str, int]:
    """
    Borra el area y deja sus cargos sin area.
    Retorna (nombre_area, total_cargos_afectados)
    """
    nombre = area.nombre
    total_cargos = area.cargos.count()
    area.cargos.update(area_usuario=None)
    area.delete()
    return nombre, total_cargos

