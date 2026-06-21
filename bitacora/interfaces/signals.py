"""
Signals de auditoria de autenticacion.

`user_logged_out` puede dispararse con `user=None` en escenarios reales:
- Logout llamado dos veces (browser refresca el endpoint).
- Sesion expirada antes del logout.
- Logout sin usuario autenticado (links que llegan a /logout/ sin sesion).

Para esos casos, registramos el evento sin tirar AttributeError.
"""

from __future__ import annotations

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from ..application.use_cases.log_event import log_event
from ..domain.services import ACCIONES, MODULOS


def _username_safe(user):
    """Devuelve el username del user, o un placeholder si es None."""
    return getattr(user, "username", None) or "(sesion sin usuario)"


@receiver(user_logged_in)
def login(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGIN"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{_username_safe(user)} inicio sesion",
    )


@receiver(user_logged_out)
def logout(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGOUT"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{_username_safe(user)} cerro sesion",
    )
