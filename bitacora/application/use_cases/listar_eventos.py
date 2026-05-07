"""
Caso de uso: listar eventos de bitacora con filtros y paginacion.

La definicion de `BitacoraFiltro` se centralizo en `filtrar_eventos.py`.
Este modulo la re-exporta para mantener compatibilidad con los imports
existentes.
"""

from __future__ import annotations

from django.core.paginator import Paginator

from ...domain.services import limpiar_descripcion, resolver_modulo
from ...infrastructure.repositories import bitacora as repo
from .filtrar_eventos import BitacoraFiltro, aplicar_filtros  # noqa: F401


def _enriquecer_evento(evento):
    evento.modulo_label = resolver_modulo(evento.modulo, evento.descripcion, evento.accion)
    evento.descripcion_label = limpiar_descripcion(evento.descripcion)
    return evento


def uc_listar_bitacora(
    *,
    filtro: BitacoraFiltro,
    is_superuser: bool,
    username: str | None,
    page: int | None,
    per_page: int = 10,
):
    registros = repo.query_eventos()

    if not is_superuser and username:
        registros = registros.filter(usuario__username=username)

    registros = aplicar_filtros(registros, filtro=filtro)
    registros = registros.order_by("-fecha")

    paginator = Paginator(registros, per_page)
    page_obj = paginator.get_page(page)
    page_obj.object_list = [_enriquecer_evento(evento) for evento in page_obj.object_list]

    usuarios = repo.distinct_usernames()
    return page_obj, usuarios
