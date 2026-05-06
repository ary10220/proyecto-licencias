from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from functools import wraps
from bitacora.application.use_cases.log_event import log_event
from bitacora.actions import (
    log_area_usuario_crear,
    log_area_usuario_editar,
    log_area_usuario_eliminar,
    log_cargo_crear,
    log_cargo_editar,
    log_cargo_eliminar,
    log_password_change_inicial,
    log_perfil_actualizar_foto,
    log_perfil_eliminar_foto,
    log_rol_crear,
    log_rol_editar,
    log_rol_eliminar,
    log_usuario_crear,
    log_usuario_editar,
    log_usuario_toggle,
    log_usuario_reset_password,
)
from empleados.models import Cargo
from ..forms import AreaUsuarioForm, CargoForm, FotoPerfilForm, GroupForm, ROLE_PERMISSION_GROUPS, UserForm
from ...models import AreaUsuario, PerfilUsuario
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

