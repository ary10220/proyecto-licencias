from .base import *  # noqa: F401,F403

from ...application.use_cases import (
    uc_perfil_actualizar_foto,
    uc_perfil_eliminar_foto,
)
from ...infrastructure import repositories as repo


# MI PERFIL
@login_required
def mi_perfil(request):
    perfil = repo.get_or_create_perfil(request.user)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'eliminar_foto':
            eliminado = uc_perfil_eliminar_foto(request, perfil)
            if eliminado:
                messages.success(request, "Tu foto de perfil fue eliminada correctamente.")
            else:
                messages.info(request, "No tienes una foto de perfil para eliminar.")
            return redirect('mi_perfil')

        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            uc_perfil_actualizar_foto(request, form)
            messages.success(request, "Tu foto de perfil fue actualizada correctamente.")
            return redirect('mi_perfil')
    else:
        form = FotoPerfilForm(instance=perfil)

    context = {
        'form': form,
        'perfil': perfil,
        'tenants': repo.list_tenants(),
        'titulo': 'Mi Perfil',
        'roles_usuario': request.user.groups.all(),
        'permisos_usuario': request.user.get_all_permissions(),
    }
    return render(request, 'user/perfil/detalle.html', context)
