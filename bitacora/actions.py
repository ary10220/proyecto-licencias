from .services import log_event
from .constants import ACCIONES, MODULOS


def log_creacion_licencia(request, licencia):
    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"Se creó licencia {licencia.nombre}"
    )


def log_asignacion_licencia(request, licencia, empleado):
    log_event(
        request=request,
        accion=ACCIONES["ASIGNAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"Licencia {licencia.nombre} asignada a {empleado.nombre}"
    )


def log_baja_empleado(request, empleado):
    log_event(
        request=request,
        accion=ACCIONES["BAJA"],
        modulo=MODULOS["EMPLEADOS"],
        descripcion=f"Empleado {empleado.nombre} dado de baja"
    )