"""
Signals del modulo licencias.

Conecta el evento `user_locked_out` de django-axes para preparar el flujo
de desbloqueo cuando un usuario alcanza el limite de intentos fallidos.

DECISION DE DISENO:
El envio del correo NO se hace aqui. El signal de Axes corre con
`signal.send_robust()` que silencia excepciones, y ademas el contexto del
request en ese momento es inestable (Axes intercepta antes de finalizar
el response). En lugar de eso, marcamos un flag en sesion y delegamos el
envio a la vista `validar_token_bloqueo`, que corre en el contexto normal
de un GET (el mismo donde el reenvio manual funciona sin problema).
"""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.dispatch import receiver

from axes.signals import user_locked_out


logger = logging.getLogger(__name__)


@receiver(user_locked_out)
def preparar_desbloqueo(sender, request, username, **kwargs):
    """
    Se dispara cuando Axes bloquea al usuario tras 3 intentos fallidos.

    Solo deja en sesion los marcadores necesarios para que la pantalla
    `/desbloqueo-seguro/` (vista `validar_token_bloqueo`) sepa para quien
    enviar el token apenas el browser siga el redirect.
    """
    if request is None:
        logger.warning("[axes_lockout] signal disparado sin request, no se puede marcar sesion (%s).", username)
        return

    user = User.objects.filter(username=username).first()
    if not user:
        logger.warning("[axes_lockout] usuario inexistente: %s", username)
        return

    request.session["usuario_bloqueado_nombre"] = username
    # Flag que la vista de desbloqueo leera para hacer el envio automatico
    # en su propio contexto (donde send_mail funciona sin problema).
    request.session["enviar_token_pendiente"] = True
    request.session.modified = True

    logger.info(
        "[axes_lockout] usuario %s bloqueado; marcado para envio automatico de token.",
        username,
    )
