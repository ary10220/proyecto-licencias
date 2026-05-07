from .base import *  # noqa: F401,F403

from ...application.use_cases import (
    uc_crear_usuario,
    uc_editar_usuario,
    uc_listar_usuarios,
    uc_reset_password_usuario,
    uc_toggle_usuario,
)
from ...infrastructure import repositories as repo


# LISTAR USUARIOS
@login_required
@permiso_requerido('auth.view_user')
def lista_usuarios(request):
    usuarios = uc_listar_usuarios()
    context = {
        'usuarios': usuarios,
        'tenants': repo.list_tenants(),
        'titulo': 'Gestión de Usuarios',
    }
    return render(request, 'user/usuarios/lista.html', context)


# CREAR USUARIO
@login_required
@permiso_requerido('auth.add_user')
def crear_usuario(request):
    if request.method == 'POST':
        form = UserForm(request.POST, current_user=request.user)
        if form.is_valid():
            usuario = uc_crear_usuario(request, form)
            messages.success(
                request,
                f"Usuario {usuario.username} creado correctamente. Puedes revisar o completar sus datos.",
            )
            return redirect('lista_usuarios')
    else:
        form = UserForm(current_user=request.user)

    context = {
        'form': form,
        'tenants': repo.list_tenants(),
        'titulo': 'Crear Usuario',
        'modo': 'crear',
    }
    return render(request, 'user/usuarios/form.html', context)


# EDITAR USUARIO
@login_required
@permiso_requerido('auth.change_user')
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=usuario, current_user=request.user)
        if form.is_valid():
            usuario = uc_editar_usuario(request, form)
            if usuario.pk == request.user.pk and getattr(form, 'password_changed', False):
                update_session_auth_hash(request, usuario)
            messages.success(request, f"Cambios de {usuario.username} guardados correctamente.")
            return redirect('lista_usuarios')
    else:
        form = UserForm(instance=usuario, current_user=request.user)

    context = {
        'form': form,
        'usuario_editado': usuario,
        'tenants': repo.list_tenants(),
        'titulo': f'Editar Usuario: {usuario.username}',
        'modo': 'editar',
    }
    return render(request, 'user/usuarios/form.html', context)


@login_required
@permiso_requerido('auth.change_user', fallback='lista_usuarios')
@require_POST
def reset_password_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    result = uc_reset_password_usuario(request, usuario)

    if not result.ok:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'message': result.message}, status=result.status)
        if result.status == 429:
            messages.warning(request, result.message)
        else:
            messages.error(request, result.message)
        return redirect('editar_usuario', user_id=usuario.id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'email': result.email, 'username': result.username})

    messages.success(request, f"Se envio un correo de restablecimiento a {result.email}.")
    return redirect('editar_usuario', user_id=usuario.id)


# ACTIVAR / DESACTIVAR
@login_required
@permiso_requerido('auth.change_user', fallback='lista_usuarios')
@require_POST
def toggle_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propio usuario mientras estás autenticado.")
        return redirect('lista_usuarios')

    usuario, estado = uc_toggle_usuario(request, usuario)
    messages.success(request, f"Usuario {usuario.username} {estado} correctamente.")
    return redirect('lista_usuarios')
