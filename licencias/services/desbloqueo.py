"""
Servicio: generar y enviar token de desbloqueo de cuenta.

Almacena token y dedup-lock en la SESION del usuario (no en cache global)
para que sea consistente entre workers WSGI en produccion (PythonAnywhere
usa LocMemCache aislado por proceso, lo cual rompia el flujo).

API:
    enviar_token_desbloqueo(request, user, source) -> (ok, mensaje)
    validar_token_desbloqueo(request, username, token_ingresado) -> bool
    limpiar_token_desbloqueo(request) -> None
"""

from __future__ import annotations

import logging
import random
import time
from typing import Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


TOKEN_TTL_SECONDS = 300            # 5 minutos
DEDUP_LOCK_SECONDS = 10            # evita doble envio rapido
SESSION_TOKEN_KEY = "desbloqueo_token"
SESSION_TOKEN_EXP_KEY = "desbloqueo_token_exp"
SESSION_LAST_SENT_KEY = "desbloqueo_last_sent_ts"


def _generar_token() -> str:
    return f"{random.randint(0, 999999):06d}"


def _construir_mensaje(user: User, token: str) -> Tuple[str, str]:
    subject = "Acceso protegido - Codigo de desbloqueo"
    message = (
        f"Hola {user.username},\n\n"
        "Tu cuenta fue bloqueada tras varios intentos fallidos de inicio de sesion.\n"
        f"Tu codigo de desbloqueo es: {token}\n\n"
        "Este codigo es valido por 5 minutos."
    )
    return subject, message


def _now() -> float:
    return time.time()


def enviar_token_desbloqueo(*, request, user: User, source: str) -> Tuple[bool, str]:
    """
    Envia un token de desbloqueo al email del usuario.
    Persiste el token y su expiracion en `request.session`.

    Retorna (ok, mensaje_para_usuario).
    """
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        logger.warning("[desbloqueo] usuario %s sin email.", user.username)
        return False, "El usuario no tiene correo registrado."

    # Dedup: evita reenvios rapidos (botones doble-click, refresh con flag, etc.)
    last_sent = request.session.get(SESSION_LAST_SENT_KEY)
    if last_sent and (_now() - float(last_sent)) < DEDUP_LOCK_SECONDS:
        logger.info("[desbloqueo] envio descartado por dedup (source=%s).", source)
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
        logger.exception("[desbloqueo] fallo SMTP (source=%s): %s", source, exc)
        return False, "No se pudo enviar el codigo de desbloqueo."

    request.session[SESSION_TOKEN_KEY] = token
    request.session[SESSION_TOKEN_EXP_KEY] = _now() + TOKEN_TTL_SECONDS
    request.session[SESSION_LAST_SENT_KEY] = _now()
    request.session.modified = True

    logger.info("[desbloqueo] token enviado a %s (source=%s).", email, source)
    return True, f"Codigo enviado a {email}."


def validar_token_desbloqueo(*, request, token_ingresado: str) -> bool:
    """Compara el token ingresado contra el de sesion. False si expirado o inexistente."""
    token = request.session.get(SESSION_TOKEN_KEY)
    exp = request.session.get(SESSION_TOKEN_EXP_KEY)

    if not token or not exp:
        return False
    if _now() > float(exp):
        # Expirado: lo limpiamos para forzar reenvio.
        limpiar_token_desbloqueo(request)
        return False
    return str(token_ingresado).strip() == str(token).strip()


def limpiar_token_desbloqueo(request) -> None:
    """Borra rastros del token tras un consumo exitoso o expiracion."""
    request.session.pop(SESSION_TOKEN_KEY, None)
    request.session.pop(SESSION_TOKEN_EXP_KEY, None)
    request.session.pop(SESSION_LAST_SENT_KEY, None)
    request.session.modified = True
