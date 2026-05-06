from __future__ import annotations

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


@receiver(user_logged_in)
def login(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGIN"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{user.username} inició sesión",
    )


@receiver(user_logged_out)
def logout(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGOUT"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{user.username} cerró sesión",
    )
