from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _empleado_label(empleado):
    try:
        return getattr(empleado, 'nombre_completo', None) or str(empleado)
    except Exception:
        return f"Empleado #{getattr(empleado, 'pk', '?')}"


def log_crear_empleado(request, empleado):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["EMPLEADOS"],
        descripcion=f"Creó empleado {_empleado_label(empleado)} (id={getattr(empleado, 'pk', 'N/D')}).",
    )


def log_editar_empleado(request, empleado):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["EMPLEADOS"],
        descripcion=f"Editó empleado {_empleado_label(empleado)} (id={getattr(empleado, 'pk', 'N/D')}).",
    )


def log_baja_empleado(request, empleado, licencias_liberadas=0):
    detalle = f" Licencias liberadas: {licencias_liberadas}." if licencias_liberadas else ""
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["EMPLEADOS"],
        descripcion=f"Baja operativa de {_empleado_label(empleado)}.{detalle}",
    )


def log_reactivar_empleado(request, empleado):
    log_event(
        request=request,
        accion=ACCIONES["REACTIVAR"],
        modulo=MODULOS["EMPLEADOS"],
        descripcion=f"Reactivó empleado {_empleado_label(empleado)} (id={getattr(empleado, 'pk', 'N/D')}).",
    )
