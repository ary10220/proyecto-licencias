from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_POST
from functools import wraps
from bitacora.services import log_event
from empleados.models import Cargo
from .forms import AreaUsuarioForm, CargoForm, FotoPerfilForm, GroupForm, ROLE_PERMISSION_GROUPS, UserForm
from .models import AreaUsuario, PerfilUsuario
from licencias.models import Tenant


def es_superusuario(user):
    return user.is_authenticated and user.is_superuser


def tiene_permiso(permiso):
    def verificar(user):
        return user.is_authenticated and (user.is_superuser or user.has_perm(permiso))
    return verificar


def permiso_requerido(permiso, fallback='mi_perfil'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or request.user.has_perm(permiso):
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para acceder a esa accion.")
            return redirect(fallback)
        return wrapper
    return decorator


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


def nombres_roles(usuario):
    roles = list(usuario.groups.values_list('name', flat=True))
    return ', '.join(roles) if roles else 'Sin roles'


def crear_cargos_de_area(area, texto_cargos):
    nombres = [
        nombre.strip()
        for nombre in (texto_cargos or '').splitlines()
        if nombre.strip()
    ]
    creados = []

    for nombre in dict.fromkeys(nombres):
        cargo, creado = Cargo.objects.get_or_create(
            nombre=nombre,
            defaults={'area_usuario': area}
        )
        if not cargo.area_usuario:
            cargo.area_usuario = area
            cargo.save(update_fields=['area_usuario'])
        if creado:
            creados.append(cargo.nombre)

    return creados


def registrar_bitacora(request, accion, modulo, descripcion):
    registrado = log_event(
        request=request,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion
    )

    if not registrado:
        messages.warning(request, "La acción se guardó, pero no se pudo registrar en la bitácora.")

    return registrado


# MI PERFIL
@login_required
def mi_perfil(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'eliminar_foto':
            if perfil.foto:
                perfil.foto.delete(save=False)
                perfil.foto = None
                perfil.save(update_fields=['foto'])
                registrar_bitacora(request, "ELIMINAR", "Perfil", f"Eliminó su foto de perfil ({request.user.username})")
                messages.success(request, "Tu foto de perfil fue eliminada correctamente.")
            else:
                messages.info(request, "No tienes una foto de perfil para eliminar.")
            return redirect('mi_perfil')

        form = FotoPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            registrar_bitacora(request, "EDITAR", "Perfil", f"Actualizó su foto de perfil ({request.user.username})")
            messages.success(request, "Tu foto de perfil fue actualizada correctamente.")
            return redirect('mi_perfil')
    else:
        form = FotoPerfilForm(instance=perfil)

    context = {
        'form': form,
        'perfil': perfil,
        'tenants': Tenant.objects.all(),
        'titulo': 'Mi Perfil',
        'roles_usuario': request.user.groups.all(),
        'permisos_usuario': request.user.get_all_permissions(),
    }
    return render(request, 'users/perfil_detalle.html', context)

# LISTAR USUARIOS
@login_required
@permiso_requerido('auth.view_user')
def lista_usuarios(request):
    usuarios = User.objects.select_related('perfil', 'perfil__area_usuario', 'perfil__cargo').prefetch_related('groups').order_by('username')
    context = {
        'usuarios': usuarios,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestión de Usuarios'
    }
    return render(request, 'users/lista.html', context)


# CREAR USUARIO
@login_required
@permiso_requerido('auth.add_user')
def crear_usuario(request):
    if request.method == 'POST':
        form = UserForm(request.POST, current_user=request.user)
        if form.is_valid():
            usuario = form.save()
            registrar_bitacora(request, "CREAR", "Usuarios", f"Creó el usuario {usuario.username} con roles: {nombres_roles(usuario)}")
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
@permiso_requerido('auth.change_user')
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=usuario, current_user=request.user)
        if form.is_valid():
            usuario = form.save()
            if usuario.pk == request.user.pk and form.password_changed:
                update_session_auth_hash(request, usuario)
            detalle_password = " Se actualizó la contraseña." if form.password_changed else ""
            registrar_bitacora(request, "EDITAR", "Usuarios", f"Actualizó el usuario {usuario.username}. Roles actuales: {nombres_roles(usuario)}.{detalle_password}")
            messages.success(request, f"Cambios de {usuario.username} guardados correctamente.")
            form = UserForm(instance=usuario, current_user=request.user)
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
@permiso_requerido('auth.change_user', fallback='lista_usuarios')
@require_POST
def toggle_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes desactivar tu propio usuario mientras estás autenticado.")
        return redirect('lista_usuarios')

    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    estado = "activado" if usuario.is_active else "desactivado"
    registrar_bitacora(request, "ACTIVAR" if usuario.is_active else "DESACTIVAR", "Usuarios", f"Usuario {usuario.username} {estado}")
    messages.success(request, f"Usuario {usuario.username} {estado} correctamente.")
    return redirect('lista_usuarios')


# LISTAR ROLES
@login_required
@permiso_requerido('auth.view_group')
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
@permiso_requerido('auth.add_group')
def crear_rol(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            rol = form.save()
            registrar_bitacora(request, "CREAR", "Roles", f"Creó el rol {rol.name} con {rol.permissions.count()} permiso(s)")
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
@permiso_requerido('auth.change_group')
def editar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            registrar_bitacora(request, "EDITAR", "Roles", f"Actualizó el rol {rol.name}. Permisos asignados: {rol.permissions.count()}")
            messages.success(request, f"Rol {rol.name} actualizado correctamente.")
            form = GroupForm(instance=rol)
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
@permiso_requerido('auth.view_group')
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
@permiso_requerido('auth.delete_group', fallback='lista_roles')
@require_POST
def eliminar_rol(request, group_id):
    rol = get_object_or_404(Group, id=group_id)
    nombre = rol.name
    total_permisos = rol.permissions.count()
    rol.delete()
    registrar_bitacora(request, "ELIMINAR", "Roles", f"Eliminó el rol {nombre}, que tenía {total_permisos} permiso(s)")
    messages.success(request, f"Rol {nombre} eliminado correctamente.")
    return redirect('lista_roles')


# LISTAR AREAS DE USUARIO
@login_required
@permiso_requerido('user.view_areausuario')
def lista_areas(request):
    areas = AreaUsuario.objects.prefetch_related('cargos').order_by('nombre')
    context = {
        'areas': areas,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestion de Areas de Usuario'
    }
    return render(request, 'users/areas_lista.html', context)


@login_required
@permiso_requerido('user.add_areausuario')
def crear_area(request):
    if request.method == 'POST':
        form = AreaUsuarioForm(request.POST)
        if form.is_valid():
            area = form.save()
            cargos_creados = crear_cargos_de_area(area, form.cleaned_data.get('cargos_iniciales'))
            detalle = f" con cargos iniciales: {', '.join(cargos_creados)}" if cargos_creados else ""
            registrar_bitacora(request, "CREAR", "Areas de Usuario", f"Creo el area {area.nombre}{detalle}")
            messages.success(request, f"Area {area.nombre} creada correctamente.")
            return redirect('editar_area', area_id=area.id)
    else:
        form = AreaUsuarioForm()

    context = {
        'form': form,
        'tenants': Tenant.objects.all(),
        'titulo': 'Crear Area',
        'modo': 'crear'
    }
    return render(request, 'users/areas_form.html', context)


@login_required
@permiso_requerido('user.change_areausuario')
def editar_area(request, area_id):
    area = get_object_or_404(AreaUsuario, id=area_id)

    if request.method == 'POST':
        form = AreaUsuarioForm(request.POST, instance=area)
        if form.is_valid():
            area = form.save()
            cargos_creados = crear_cargos_de_area(area, form.cleaned_data.get('cargos_iniciales'))
            detalle = f" Agrego cargos: {', '.join(cargos_creados)}." if cargos_creados else ""
            registrar_bitacora(request, "EDITAR", "Areas de Usuario", f"Actualizo el area {area.nombre}.{detalle}")
            messages.success(request, f"Area {area.nombre} actualizada correctamente.")
            form = AreaUsuarioForm(instance=area)
    else:
        form = AreaUsuarioForm(instance=area)

    context = {
        'form': form,
        'area': area,
        'cargos_area': area.cargos.order_by('nombre'),
        'tenants': Tenant.objects.all(),
        'titulo': f'Editar Area: {area.nombre}',
        'modo': 'editar'
    }
    return render(request, 'users/areas_form.html', context)


@login_required
@permiso_requerido('user.delete_areausuario', fallback='lista_areas')
@require_POST
def eliminar_area(request, area_id):
    area = get_object_or_404(AreaUsuario, id=area_id)
    nombre = area.nombre
    total_cargos = area.cargos.count()
    area.cargos.update(area_usuario=None)
    area.delete()
    registrar_bitacora(request, "ELIMINAR", "Areas de Usuario", f"Elimino el area {nombre}. Cargos desvinculados: {total_cargos}")
    messages.success(request, f"Area {nombre} eliminada correctamente. Sus cargos quedaron sin area.")
    return redirect('lista_areas')


# LISTAR CARGOS
@login_required
@permiso_requerido('empleados.view_cargo')
def lista_cargos(request):
    cargos = Cargo.objects.select_related('area_usuario').order_by('area_usuario__nombre', 'nombre')
    context = {
        'cargos': cargos,
        'tenants': Tenant.objects.all(),
        'titulo': 'Gestión de Cargos'
    }
    return render(request, 'users/cargos_lista.html', context)


# CREAR CARGO
@login_required
@permiso_requerido('empleados.add_cargo')
def crear_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            cargo = form.save()
            registrar_bitacora(request, "CREAR", "Cargos", f"Creó el cargo {cargo.nombre}")
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
@permiso_requerido('empleados.change_cargo')
def editar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)

    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            cargo = form.save()
            registrar_bitacora(request, "EDITAR", "Cargos", f"Actualizó el cargo {cargo.nombre}")
            messages.success(request, f"Cargo {cargo.nombre} actualizado correctamente.")
            form = CargoForm(instance=cargo)
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
@permiso_requerido('empleados.delete_cargo', fallback='lista_cargos')
@require_POST
def eliminar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id=cargo_id)
    nombre = cargo.nombre
    cargo.delete()
    registrar_bitacora(request, "ELIMINAR", "Cargos", f"Eliminó el cargo {nombre}")
    messages.success(request, f"Cargo {nombre} eliminado correctamente.")
    return redirect('lista_cargos')
