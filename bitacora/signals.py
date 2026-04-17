from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .services import log_event
from .constants import ACCIONES, MODULOS


@receiver(user_logged_in)
def login(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGIN"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{user.username} inició sesión"
    )


@receiver(user_logged_out)
def logout(sender, request, user, **kwargs):
    log_event(
        request=request,
        accion=ACCIONES["LOGOUT"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{user.username} cerró sesión"
    )