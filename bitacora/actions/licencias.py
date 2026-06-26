from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event


def _licencia_label(licencia):
    # `Licencia.__str__` ya devuelve algo útil ("Tipo - Empresa").
    try:
        return str(licencia)
    except Exception:
        return f"Licencia #{getattr(licencia, 'pk', '?')}"


def log_creacion_licencias(request, licencia_base, cantidad=1):
    tipo = getattr(getattr(licencia_base, 'tipo', None), 'nombre', None) or 'N/D'
    tenant = getattr(getattr(licencia_base, 'tenant', None), 'nombre', None) or 'N/D'
    empresa = getattr(getattr(licencia_base, 'empresa', None), 'nombre', None)
    proveedor = getattr(getattr(licencia_base, 'proveedor', None), 'nombre', None)

    partes = [f"Se crearon {cantidad} licencia(s) de '{tipo}'", f"Tenant: {tenant}"]
    if empresa:
        partes.append(f"Empresa: {empresa}")
    if proveedor:
        partes.append(f"Proveedor: {proveedor}")

    log_event(
        request=request,
        accion=ACCIONES["CREAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=". ".join(partes),
    )


def log_editar_licencia(request, licencia):
    log_event(
        request=request,
        accion=ACCIONES["EDITAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=(
            f"Se editaron parámetros de {_licencia_label(licencia)} "
            f"(id={getattr(licencia, 'pk', 'N/D')})."
        ),
    )


def log_eliminar_licencia(request, licencia_label, licencia_id=None):
    extra = f" (id={licencia_id})" if licencia_id is not None else ""
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"Se eliminó {_licencia_label(licencia_label)}{extra}.",
    )


def log_asignacion_licencia(request, licencia, empleado):
    emp_label = getattr(empleado, 'nombre_completo', None) or str(empleado)
    log_event(
        request=request,
        accion=ACCIONES["ASIGNAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"{_licencia_label(licencia)} asignada a {emp_label}.",
    )


def log_liberar_licencia(request, licencia, empleados=None, cantidad=None):
    empleados = empleados or []
    emp_txt = ", ".join(empleados[:3])
    if len(empleados) > 3:
        emp_txt += f" (+{len(empleados) - 3} más)"

    suf = []
    if cantidad is not None:
        suf.append(f"Registros: {cantidad}")
    if emp_txt:
        suf.append(f"Empleados: {emp_txt}")

    detalle = f" ({'; '.join(suf)})" if suf else ""
    log_event(
        request=request,
        accion=ACCIONES["LIBERAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"Se liberó {_licencia_label(licencia)}{detalle}.",
    )


def log_eliminar_licencias_masivo(request, cantidad):
    log_event(
        request=request,
        accion=ACCIONES["ELIMINAR"],
        modulo=MODULOS["LICENCIAS"],
        descripcion=f"Eliminación masiva: {cantidad} licencia(s) eliminada(s).",
    )


def log_exportar_excel(request, tenant_label=None):
    detalle = f" ({tenant_label})" if tenant_label else ""
    log_event(
        request=request,
        accion=ACCIONES["EXPORTAR"],
        modulo=MODULOS["REPORTES"],
        descripcion=f"Exportó reporte Excel{detalle}.",
    )


def log_exportar_pdf(request, tenant_label=None):
    detalle = f" ({tenant_label})" if tenant_label else ""
    log_event(
        request=request,
        accion=ACCIONES["EXPORTAR"],
        modulo=MODULOS["REPORTES"],
        descripcion=f"Exportó reporte PDF{detalle}.",
    )


def log_exportar_csv(request, tenant_label=None):
    detalle = f" ({tenant_label})" if tenant_label else ""
    log_event(
        request=request,
        accion=ACCIONES["EXPORTAR"],
        modulo=MODULOS["REPORTES"],
        descripcion=f"Exportó reporte CSV{detalle}.",
    )
