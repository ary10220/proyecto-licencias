"""
Signals del modulo licencias.

`user_locked_out` de django-axes solo deja el flag `enviar_token_pendiente`
en sesion. El envio real lo hace la vista `validar_token_bloqueo` en su
proximo GET (mismo contexto que el reenvio manual, donde send_mail funciona).
"""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.dispatch import receiver

from axes.signals import user_locked_out


logger = logging.getLogger(__name__)


@receiver(user_locked_out)
def preparar_desbloqueo(sender, request, username, **kwargs):
    """Marca la sesion para que la siguiente vista dispare el envio."""
    if request is None:
        logger.warning("[axes_lockout] signal sin request, no se puede marcar sesion.")
        return

    user = User.objects.filter(username=username).first()
    if not user:
        logger.warning("[axes_lockout] usuario inexistente: %s", username)
        return

    request.session["usuario_bloqueado_nombre"] = username
    request.session["enviar_token_pendiente"] = True
    request.session.modified = True
    logger.info("[axes_lockout] usuario %s bloqueado, marcado para envio automatico.", username)
