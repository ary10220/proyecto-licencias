from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from empleados.models import Cargo
from .forms import CargoForm, GroupForm, ROLE_PERMISSION_GROUPS, UserForm
from licencias.models import Tenant


def es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def tiene_permiso(permiso):
    def verificar(user):
        return user.is_authenticated and (user.is_superuser or user.has_perm(permiso))
    return verificar


def obtener_permisos_por_modulo(form):
    permisos_seleccionados = set(str(pk) for pk in form['permissions'].value() or [])
    grupos = []

    for grupo in ROLE_PERMISSION_GROUPS:
        filtros = Q(pk__in=[])
        for codigo in grupo['permisos']:
            app_label, codename = codigo.split('.', 1)
            filtros |= Q(content_type__app_label=app_label, codename=codename)
        permisos = Permission.objects.filter(filtros).select_related('content_type').order_by('content_type__model', 'codename')
        grupos.append({
            'titulo': grupo['titulo'],
            'descripcion': grupo['descripcion'],
            'permisos': permisos,
            'seleccionados': permisos_seleccionados,
        })

    return grupos

# LISTAR USUARIOS
@login_required
@user_passes_test(tiene_permiso('auth.view_user'))
def lista_usuarios(request):
    usuarios = User.objects.select_related('perfil', 'perfil__cargo').prefetch_related('groups').order_by('username')
    context = {
        'usuarios': usuarios,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestión de Usuarios'
    }
    return render(request, 'users/lista.html', context)


# CREAR USUARIO
@login_required
@user_passes_test(tiene_permiso('auth.add_user'))
def crear_usuario(request):
    if request.method == 'POST':
        form = UserForm(request.POST, current_user=request.user)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"Usuario {usuario.username} creado correctamente. Puedes revisar o completar sus datos.")
            return redirect('editar_usuario', user_id=usuario.id)
    else:
        form = UserForm(current_user=request.user)

    context = {
        'form': form,
        'tenants': Tenant.objects.all(),
        'titulo': 'Crear Usuario',
        'modo': 'crear'
    }
    return render(request, 'users/form.html', context)


# EDITAR USUARIO
@login_required
@user_passes_test(tiene_permiso('auth.change_user'))
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=usuario, current_user=request.user)
        if form.is_valid():
            usuario = form.save()
            if usuario.pk == request.user.pk and form.password_changed:
                update_session_auth_hash(request, usuario)
            messages.success(request, f"Cambios de {usuario.username} guardados correctamente.")
            return redirect('editar_usuario', user_id=usuario.id)
    else:
        form = UserForm(instance=usuario, current_user=request.user)

    context = {
        'form': form,
        'usuario_editado': usuario,
        'tenants': Tenant.objects.all(),
        'titulo': f'Editar Usuario: {usuario.username}',
        'modo': 'editar'
    }
    return render(request, 'users/form.html', context)


# ACTIVAR / DESACTIVAR
@login_required
@user_passes_test(tiene_permiso('auth.change_user'))
def toggle_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propio usuario mientras estás autenticado.")
        return redirect('lista_usuarios')

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f"Usuario {usuario.username} {estado} correctamente.")
    return redirect('lista_usuarios')


# LISTAR ROLES
@login_required
@user_passes_test(tiene_permiso('auth.view_group'))
def lista_roles(request):
    roles = Group.objects.prefetch_related('permissions').order_by('name')
    context = {
        'roles': roles,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestión de Roles'
    }
    return render(request, 'users/roles_lista.html', context)


# CREAR ROL
@login_required
@user_passes_test(tiene_permiso('auth.add_group'))
def crear_rol(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            rol = form.save()
            messages.success(request, f"Rol {rol.name} creado correctamente. Puedes revisar o ajustar sus permisos.")
            return redirect('editar_rol', group_id=rol.id)
    else:
        form = GroupForm()

    context = {
        'form': form,
        'permission_groups': obtener_permisos_por_modulo(form),
        'tenants': Tenant.objects.all(),
        'titulo': 'Crear Rol',
        'modo': 'crear'
    }
    return render(request, 'users/roles_form.html', context)


# EDITAR ROL
@login_required
@user_passes_test(tiene_permiso('auth.change_group'))
def editar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            messages.success(request, f"Rol {rol.name} actualizado correctamente.")
            return redirect('editar_rol', group_id=rol.id)
    else:
        form = GroupForm(instance=rol)

    context = {
        'form': form,
        'permission_groups': obtener_permisos_por_modulo(form),
        'rol': rol,
        'tenants': Tenant.objects.all(),
        'titulo': f'Editar Rol: {rol.name}',
        'modo': 'editar'
    }
    return render(request, 'users/roles_form.html', context)


# VER DETALLE DE ROL
@login_required
@user_passes_test(tiene_permiso('auth.view_group'))
def detalle_rol(request, group_id):
    rol = get_object_or_404(Group.objects.prefetch_related('permissions__content_type'), id=group_id)
    permisos_por_modulo = obtener_permisos_por_modulo(GroupForm(instance=rol))

    context = {
        'rol': rol,
        'permission_groups': permisos_por_modulo,
        'tenants': Tenant.objects.all(),
        'titulo': f'Detalle del Rol: {rol.name}'
    }
    return render(request, 'users/roles_detalle.html', context)


# ELIMINAR ROL
@login_required
@user_passes_test(tiene_permiso('auth.delete_group'))
def eliminar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)
    nombre = rol.name
    rol.delete()
    messages.success(request, f"Rol {nombre} eliminado correctamente.")
    return redirect('lista_roles')


# LISTAR CARGOS
@login_required
@user_passes_test(tiene_permiso('empleados.view_cargo'))
def lista_cargos(request):
    cargos = Cargo.objects.order_by('nombre')
    context = {
        'cargos': cargos,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestión de Cargos'
    }
    return render(request, 'users/cargos_lista.html', context)


# CREAR CARGO
@login_required
@user_passes_test(tiene_permiso('empleados.add_cargo'))
def crear_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            cargo = form.save()
            messages.success(request, f"Cargo {cargo.nombre} creado correctamente. Puedes revisar o completar sus datos.")
            return redirect('editar_cargo', cargo_id=cargo.id)
    else:
        form = CargoForm()

    context = {
        'form': form,
        'tenants': Tenant.objects.all(),
        'titulo': 'Crear Cargo',
        'modo': 'crear'
    }
    return render(request, 'users/cargos_form.html', context)


# EDITAR CARGO
@login_required
@user_passes_test(tiene_permiso('empleados.change_cargo'))
def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)

    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            cargo = form.save()
            messages.success(request, f"Cargo {cargo.nombre} actualizado correctamente.")
            return redirect('editar_cargo', cargo_id=cargo.id)
    else:
        form = CargoForm(instance=cargo)

    context = {
        'form': form,
        'cargo': cargo,
        'tenants': Tenant.objects.all(),
        'titulo': f'Editar Cargo: {cargo.nombre}',
        'modo': 'editar'
    }
    return render(request, 'users/cargos_form.html', context)


# ELIMINAR CARGO
@login_required
@user_passes_test(tiene_permiso('empleados.delete_cargo'))
def eliminar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    nombre = cargo.nombre
    cargo.delete()
    messages.success(request, f"Cargo {nombre} eliminado correctamente.")
    return redirect('lista_cargos')
