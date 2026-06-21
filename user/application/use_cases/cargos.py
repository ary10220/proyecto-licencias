from bitacora.actions import log_cargo_eliminar


def uc_eliminar_cargo(request, cargo) -> str:
    nombre = cargo.nombre
    cargo.delete()
    log_cargo_eliminar(request, nombre)
    return nombre

