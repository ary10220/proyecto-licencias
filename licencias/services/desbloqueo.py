"""
Servicio: generar y enviar token de desbloqueo de cuenta.

Centraliza la logica usada por el flujo automatico (signal `user_locked_out`)
y por el reenvio manual desde la pantalla de desbloqueo.
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
DEDUP_LOCK_SECONDS = 10
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
    """Envia un token de desbloqueo. Retorna (ok, mensaje)."""
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        logger.warning("[desbloqueo] usuario %s sin email.", user.username)
        return False, "El usuario no tiene correo registrado."

    lock_key = LOCK_CACHE_KEY.format(source=source, username=user.username)
    if not cache.add(lock_key, "1", timeout=DEDUP_LOCK_SECONDS):
        logger.info("[desbloqueo] envio descartado por dedup-lock (%s).", source)
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
        cache.delete(lock_key)
        logger.exception("[desbloqueo] fallo SMTP (source=%s): %s", source, exc)
        return False, "No se pudo enviar el codigo de desbloqueo."

    cache.set(
        TOKEN_CACHE_KEY.format(username=user.username),
        token,
        timeout=TOKEN_TTL_SECONDS,
    )
    logger.info("[desbloqueo] token enviado (source=%s).", source)
    return True, f"Codigo enviado a {email}."
