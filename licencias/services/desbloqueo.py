"""
Servicio: generar y enviar token de desbloqueo de cuenta.

Centraliza la logica usada por:
  - El signal `user_locked_out` de Axes (envio automatico al bloquearse).
  - La vista `enviar_token_bloqueo` (reenvio manual desde la pantalla).

Reglas:
  - Se envia el correo PRIMERO; solo si el envio fue exitoso se guarda el
    token en cache y se marca el lock anti-duplicados. Asi evitamos que un
    fallo SMTP deje el lock contaminado e impida reintentos.
  - El lock anti-duplicados es por (source, username) con timeout corto
    (10s), suficiente para evitar dobles disparos sin bloquear al usuario.
  - Cualquier excepcion de `send_mail` se loggea (no se traga) para que
    quede traza en consola/archivo.
"""

from __future__ import annotations

import logging
import random
from typing import Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


TOKEN_TTL_SECONDS = 300            # 5 minutos
DEDUP_LOCK_SECONDS = 10            # ventana anti dobles disparos
TOKEN_CACHE_KEY = "token_desbloqueo_{username}"
LOCK_CACHE_KEY = "unlock_token_lock:{source}:{username}"


def _generar_token() -> str:
    return str(random.randint(100000, 999999))


def _construir_mensaje(user: User, token: str) -> Tuple[str, str]:
    subject = "Acceso protegido - Codigo de desbloqueo"
    message = (
        f"Hola {user.username},\n\n"
        "Tu cuenta fue bloqueada tras 3 intentos fallidos de inicio de sesion.\n"
        f"Tu codigo de desbloqueo es: {token}\n\n"
        "Este codigo es valido por 5 minutos."
    )
    return subject, message


def enviar_token_desbloqueo(*, user: User, source: str) -> Tuple[bool, str]:
    """
    Envia un token de desbloqueo al correo del usuario.

    Args:
        user: usuario destinatario.
        source: 'autosend' (signal automatico) o 'manual' (vista de reenvio).
                Solo se usa para diferenciar las claves de dedup.

    Returns:
        (ok, mensaje) donde:
          - ok=True  si el envio fue exitoso (token guardado en cache).
          - ok=False si fallo. El mensaje describe el motivo.

    No levanta excepciones: los errores se loggean y se reportan via el
    valor de retorno.
    """
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        logger.warning(
            "[desbloqueo] usuario %s no tiene email registrado, no se envia token.",
            user.username,
        )
        return False, "El usuario no tiene correo registrado."

    lock_key = LOCK_CACHE_KEY.format(source=source, username=user.username)
    if not cache.add(lock_key, "1", timeout=DEDUP_LOCK_SECONDS):
        logger.info(
            "[desbloqueo] envio descartado por dedup-lock (%s) para %s.",
            source, user.username,
        )
        return False, "Se envio un codigo recientemente, espera unos segundos."

    token = _generar_token()
    subject, message = _construir_mensaje(user, token)

    try:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [email],
            fail_silently=False,
        )
    except Exception as exc:
        # Liberamos el lock para que el siguiente intento pueda reenviar.
        cache.delete(lock_key)
        logger.exception(
            "[desbloqueo] fallo al enviar email a %s (source=%s): %s",
            email, source, exc,
        )
        return False, "No se pudo enviar el codigo de desbloqueo."

    # Solo guardamos el token despues de un envio exitoso.
    cache.set(
        TOKEN_CACHE_KEY.format(username=user.username),
        token,
        timeout=TOKEN_TTL_SECONDS,
    )
    logger.info(
        "[desbloqueo] token enviado a %s (source=%s).", email, source,
    )
    return True, f"Codigo enviado a {email}."
