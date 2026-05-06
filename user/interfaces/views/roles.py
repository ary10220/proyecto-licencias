from .base import *  # noqa: F401,F403

from ...application.use_cases import (
    uc_crear_rol,
    uc_editar_rol,
    uc_eliminar_rol,
)
from ...infrastructure import repositories as repo


# LISTAR ROLES
@login_required
@permiso_requerido('auth.view_group')
def lista_roles(request):
    roles = repo.list_roles()
    context = {
        'roles': roles,
        'tenants': repo.list_tenants(),
        'titulo': 'Gestión de Roles',
    }
    return render(request, 'user/roles/lista.html', context)


# CREAR ROL
@login_required
@permiso_requerido('auth.add_group')
def crear_rol(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            rol = uc_crear_rol(request, form)
            messages.success(request, f"Rol {rol.name} creado correctamente. Puedes revisar o ajustar sus permisos.")
            return redirect('lista_roles')
    else:
        form = GroupForm()

    context = {
        'form': form,
        'permission_groups': obtener_permisos_por_modulo(form),
        'tenants': repo.list_tenants(),
        'titulo': 'Crear Rol',
        'modo': 'crear',
    }
    return render(request, 'user/roles/form.html', context)


# EDITAR ROL
@login_required
@permiso_requerido('auth.change_group')
def editar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=rol)
        if form.is_valid():
            rol = uc_editar_rol(request, form)
            messages.success(request, f"Rol {rol.name} actualizado correctamente.")
            return redirect('lista_roles')
    else:
        form = GroupForm(instance=rol)

    context = {
        'form': form,
        'permission_groups': obtener_permisos_por_modulo(form),
        'rol': rol,
        'tenants': repo.list_tenants(),
        'titulo': f'Editar Rol: {rol.name}',
        'modo': 'editar',
    }
    return render(request, 'user/roles/form.html', context)


# VER DETALLE DE ROL
@login_required
@permiso_requerido('auth.view_group')
def detalle_rol(request, group_id):
    rol = get_object_or_404(Group.objects.prefetch_related('permissions__content_type'), id=group_id)
    permisos_por_modulo = obtener_permisos_por_modulo(GroupForm(instance=rol))

    context = {
        'rol': rol,
        'permission_groups': permisos_por_modulo,
        'tenants': repo.list_tenants(),
        'titulo': f'Detalle del Rol: {rol.name}',
    }
    return render(request, 'user/roles/detalle.html', context)


# ELIMINAR ROL
@login_required
@permiso_requerido('auth.delete_group', fallback='lista_roles')
@require_POST
def eliminar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)
    nombre, _total_permisos = uc_eliminar_rol(request, rol)
    messages.success(request, f"Rol {nombre} eliminado correctamente.")
    return redirect('lista_roles')
