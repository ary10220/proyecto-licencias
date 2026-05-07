from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _roles_label(usuario):
    try:
        roles = list(usuario.groups.values_list('name', flat=True))
    except Exception:
        roles = []
    return ", ".join(roles) if roles else "Sin roles"


def log_perfil_actualizar_foto(request, username):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["PERFIL"],
        descripcion=f"Actualizó su foto de perfil ({username}).",
    )


def log_perfil_eliminar_foto(request, username):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PERFIL"],
        descripcion=f"Eliminó su foto de perfil ({username}).",
    )


def log_usuario_crear(request, usuario):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Creó el usuario {usuario.username} con roles: {_roles_label(usuario)}.",
    )


def log_usuario_editar(request, usuario, password_changed=False):
    detalle = " Se actualizó la contraseña." if password_changed else ""
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Actualizó el usuario {usuario.username}. Roles actuales: {_roles_label(usuario)}.{detalle}",
    )


def log_usuario_toggle(request, usuario, estado):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"] if estado == "activado" else ACCIONES["BAJA"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Usuario {usuario.username} {estado}.",
    )


def log_usuario_reset_password(request, usuario, email):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Envío enlace de restablecimiento a {usuario.username} ({email}).",
    )


def log_rol_crear(request, rol):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Creó el rol {rol.name} con {rol.permissions.count()} permiso(s).",
    )


def log_rol_editar(request, rol):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Actualizó el rol {rol.name}. Permisos asignados: {rol.permissions.count()}.",
    )


def log_rol_eliminar(request, nombre, total_permisos):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Eliminó el rol {nombre}, que tenía {total_permisos} permiso(s).",
    )


def log_area_usuario_crear(request, area, cargos_creados=0):
    detalle = f" Cargos creados: {cargos_creados}." if cargos_creados else ""
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        # Áreas y cargos son parte de la estructura organizacional.
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Creó el área de usuario {area.nombre}.{detalle}",
    )


def log_area_usuario_editar(request, area, cargos_creados=0):
    detalle = f" Cargos creados: {cargos_creados}." if cargos_creados else ""
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Actualizó el área de usuario {area.nombre}.{detalle}",
    )


def log_area_usuario_eliminar(request, nombre, total_cargos):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Eliminó el área de usuario {nombre}. Cargos desvinculados: {total_cargos}.",
    )


def log_cargo_crear(request, cargo):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Creó el cargo {cargo.nombre}.",
    )


def log_cargo_editar(request, cargo):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Actualizó el cargo {cargo.nombre}.",
    )


def log_cargo_eliminar(request, nombre):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["USUARIOS_ACCESOS"],
        descripcion=f"Eliminó el cargo {nombre}.",
    )


def log_password_change_inicial(request, username):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{username} cambió su contraseña inicial.",
    )
