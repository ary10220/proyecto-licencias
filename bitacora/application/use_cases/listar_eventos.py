from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.core.paginator import Paginator

from ...infrastructure.repositories import bitacora as repo


@dataclass(frozen=True)
class BitacoraFiltro:
    usuario: Optional[str] = None
    accion: Optional[str] = None
    fecha_inicio: Optional[str] = None  # YYYY-MM-DD
    fecha_fin: Optional[str] = None     # YYYY-MM-DD


def uc_listar_bitacora(*, filtro: BitacoraFiltro, is_superuser: bool, username: str | None, page: int | None, per_page: int = 10):
    """
    Devuelve (page_obj, usuarios_distintos).
    Mantiene la misma lógica actual: superuser ve todo, usuario normal ve solo lo suyo.
    """
    registros = repo.query_eventos()

    if not is_superuser and username:
        registros = registros.filter(usuario__username=username)

    if filtro.usuario:
        registros = registros.filter(usuario__username=filtro.usuario)

    if filtro.accion:
        registros = registros.filter(accion=filtro.accion)

    if filtro.fecha_inicio:
        registros = registros.filter(fecha__date__gte=filtro.fecha_inicio)

    if filtro.fecha_fin:
        registros = registros.filter(fecha__date__lte=filtro.fecha_fin)

    registros = registros.order_by("-fecha")

    paginator = Paginator(registros, per_page)
    page_obj = paginator.get_page(page)

    usuarios = repo.distinct_usernames()
    return page_obj, usuarios

