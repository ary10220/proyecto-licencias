from bitacora.actions import (
    log_perfil_actualizar_foto,
    log_perfil_eliminar_foto,
)


def uc_perfil_eliminar_foto(request, perfil) -> bool:
    if not getattr(perfil, 'foto', None):
        return False
    perfil.foto.delete(save=False)
    perfil.foto = None
    perfil.save(update_fields=['foto'])
    log_perfil_eliminar_foto(request, request.user.username)
    return True


def uc_perfil_actualizar_foto(request, form) -> None:
    form.save()
    log_perfil_actualizar_foto(request, request.user.username)

