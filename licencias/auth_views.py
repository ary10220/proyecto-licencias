"""
Vistas custom de autenticacion que extienden las built-in de Django.

Resuelven la interaccion entre `PasswordResetConfirmView` y django-axes:
si un usuario fue bloqueado por intentos fallidos y luego restablece su
password, debemos limpiar el bloqueo para que pueda loguearse normalmente
sin pasar por la pantalla de codigo de desbloqueo.
"""

from __future__ import annotations

import logging

from django.contrib.auth.views import (
    PasswordResetConfirmView,
    PasswordChangeView,
)
from django.urls import reverse_lazy

from axes.utils import reset


logger = logging.getLogger(__name__)


def _reset_axes_lockout(username: str) -> None:
    """Limpia el lockout de Axes para un username (todas sus IPs)."""
    if not username:
        return
    try:
        cleared = reset(username=username)
        logger.info("[axes_reset_post_password] %s - %s registros limpiados.", username, cleared)
    except Exception as exc:
        logger.exception("[axes_reset_post_password] error limpiando lockout de %s: %s", username, exc)


class AxesAwarePasswordResetConfirmView(PasswordResetConfirmView):
    """
    Misma pantalla nativa de confirmar nueva password tras "olvide mi
    contrasena", pero al guardar la nueva contrasena tambien limpia los
    intentos fallidos de Axes para ese usuario. Asi el siguiente login
    no manda al usuario al flujo de desbloqueo por codigo.
    """

    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        # `self.user` lo deja seteado el dispatch de PasswordResetConfirmView
        user = getattr(self, "user", None)
        if user is not None:
            _reset_axes_lockout(user.username)
        return response


class AxesAwarePasswordChangeView(PasswordChangeView):
    """
    Cambio de password de un usuario logueado. Despues de guardar la
    nueva contrasena tambien limpia el lockout de Axes (defensivo).
    """

    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.is_authenticated:
            _reset_axes_lockout(user.username)
        return response
