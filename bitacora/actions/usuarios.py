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
        descripcion=f"Actualizo su foto de perfil ({username}).",
    )


def log_perfil_eliminar_foto(request, username):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["PERFIL"],
        descripcion=f"Elimino su foto de perfil ({username}).",
    )


def log_usuario_crear(request, usuario):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["USUARIOS"],
        descripcion=f"Creo el usuario {usuario.username} con roles: {_roles_label(usuario)}.",
    )


def log_usuario_editar(request, usuario, password_changed=False):
    detalle = " Se actualizo la contrasena." if password_changed else ""
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS"],
        descripcion=f"Actualizo el usuario {usuario.username}. Roles actuales: {_roles_label(usuario)}.{detalle}",
    )


def log_usuario_toggle(request, usuario, estado):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"] if estado == "activado" else ACCIONES["BAJA"],
        modulo=MODULOS["USUARIOS"],
        descripcion=f"Usuario {usuario.username} {estado}.",
    )


def log_usuario_reset_password(request, usuario, email):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["USUARIOS"],
        descripcion=f"Envio enlace de restablecimiento a {usuario.username} ({email}).",
    )


def log_rol_crear(request, rol):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ROLES"],
        descripcion=f"Creo el rol {rol.name} con {rol.permissions.count()} permiso(s).",
    )


def log_rol_editar(request, rol):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ROLES"],
        descripcion=f"Actualizo el rol {rol.name}. Permisos asignados: {rol.permissions.count()}.",
    )


def log_rol_eliminar(request, nombre, total_permisos):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["ROLES"],
        descripcion=f"Elimino el rol {nombre}, que tenia {total_permisos} permiso(s).",
    )


def log_area_usuario_crear(request, area, cargos_creados=0):
    detalle = f" Cargos creados: {cargos_creados}." if cargos_creados else ""
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creo el area de usuario {area.nombre}.{detalle}",
    )


def log_area_usuario_editar(request, area, cargos_creados=0):
    detalle = f" Cargos creados: {cargos_creados}." if cargos_creados else ""
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Actualizo el area de usuario {area.nombre}.{detalle}",
    )


def log_area_usuario_eliminar(request, nombre, total_cargos):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Elimino el area de usuario {nombre}. Cargos desvinculados: {total_cargos}.",
    )


def log_cargo_crear(request, cargo):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Creo el cargo {cargo.nombre}.",
    )


def log_cargo_editar(request, cargo):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Actualizo el cargo {cargo.nombre}.",
    )


def log_cargo_eliminar(request, nombre):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["ORG"],
        descripcion=f"Elimino el cargo {nombre}.",
    )


def log_password_change_inicial(request, username):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["AUTH"],
        descripcion=f"{username} cambio su contrasena inicial.",
    )
