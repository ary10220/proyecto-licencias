"""
Caso de uso: obtener el detalle de un evento de bitacora.

Aplica reglas de visibilidad: un usuario no superuser solo puede ver
los eventos donde figura como autor.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from ...domain.services import limpiar_descripcion, resolver_modulo
from ...models import Bitacora


def uc_ver_detalle_evento(*, evento_id: int, is_superuser: bool, username: str | None):
    evento = get_object_or_404(
        Bitacora.objects.select_related("usuario"),
        pk=evento_id,
    )

    if not is_superuser:
        autor = evento.usuario.username if evento.usuario else None
        if autor != username:
            raise PermissionDenied("No puede ver eventos de otros usuarios.")

    evento.modulo_label = resolver_modulo(evento.modulo, evento.descripcion, evento.accion)
    evento.descripcion_label = limpiar_descripcion(evento.descripcion)
    return evento
