import json
import openpyxl
from openpyxl.styles import Font, PatternFill
from datetime import timedelta
import random
 
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth import login
from axes.utils import reset
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from empleados.models import Empleado, GerenciaDivision, GerenciaArea, Unidad
from .models import Licencia, Asignacion, Tenant, Empresa, Proveedor, TipoLicencia
from .forms import (
    EmpleadoForm, GerenciaDivisionForm, GerenciaAreaForm, UnidadForm,
    TenantForm, EmpresaForm, ProveedorForm, TipoLicenciaForm, LicenciaForm
)
from .services.asignacion import (
    asignar_licencia as svc_asignar,
    liberar_licencia as svc_liberar,
)
from .services.empleados import dar_baja_empleado as svc_baja_empleado
from .selectors import obtener_kpis_dashboard
from .services.exceptions import (
    LicenciaNoEncontradaError,
    EmpleadoNoEncontradoError,
    LicenciaYaAsignadaError,
    EmpleadoYaTieneTipoError,
    AsignacionInactivaError,
    EmpleadoYaInactivoError,
)
from django.http import Http404
from bitacora.actions import (
    log_creacion_licencias,
    log_crear_empleado,
    log_division_crear,
    log_area_crear,
    log_unidad_crear,
    log_empresa_crear,
    log_proveedor_crear,
    log_tenant_crear,
    log_tipo_licencia_crear,
    log_editar_licencia,
    log_editar_empleado,
    log_eliminar_licencia,
    log_eliminar_licencias_masivo,
    log_exportar_excel,
    log_reactivar_empleado,
    log_division_editar,
    log_division_eliminar,
    log_area_editar,
    log_area_eliminar,
    log_unidad_editar,
    log_unidad_eliminar,
    log_tenant_editar,
    log_tenant_eliminar,
    log_empresa_editar,
    log_empresa_eliminar,
    log_proveedor_editar,
    log_proveedor_eliminar,
    log_tipo_licencia_editar,
    log_tipo_licencia_eliminar,
)

def exigir_permiso(request, permiso):
    if not request.user.has_perm(permiso):
        raise PermissionDenied


def exigir_algun_permiso(request, permisos):
    if not any(request.user.has_perm(permiso) for permiso in permisos):
        raise PermissionDenied

CONFIG_TAB_BY_TYPE = {
    'empresa': 'empresas',
    'division': 'divisiones',
    'area': 'areas',
    'unidad': 'unidades',
    'tenant': 'tenants',
    'proveedor': 'proveedores',
    'tipo_licencia': 'tipos',
}


def _config_tab_from_request(request, default='empresas'):
    return request.POST.get('active_tab') or request.GET.get('tab') or default


def _redirect_config_tab(tab_name):
    return redirect(f"{reverse('configuracion')}?tab={tab_name}")

# ==========================================
# MÓDULO DE EXPORTACIÓN Y REPORTES
# ==========================================

@login_required
def exportar_excel(request, tenant_id=None):
    """
    Genera un reporte consolidado en formato Excel (.xlsx) de los activos de software.
    Implementa OpenPyXL para el formateo directo del buffer de memoria sin escritura en disco.
    """
    exigir_permiso(request, 'licencias.view_licencia')
    tenant_label = None
    if tenant_id:
        tenant_label = Tenant.objects.filter(pk=tenant_id).values_list('nombre', flat=True).first()
    log_exportar_excel(request, tenant_label=tenant_label)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte Completo"

    headers = [
        'Tipo Licencia', 'Fabricante', 'Proveedor', 'Tenant', 'Empresa Dueña', 
        'Estado', 'Usuario Asignado', 'Email Usuario', 'Centro de Costos', 
        'Gerencia/Área', 'División', 'Unidad', 'Fecha Asignación', 'Fecha Vencimiento'
    ]
    ws.append(headers)

    # Estilos de la cabecera
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="DF6E12", end_color="DF6E12", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Optimización de consultas usando select_related para evitar el problema N+1
    if tenant_id:
        licencias = Licencia.objects.filter(tenant_id=tenant_id).select_related('tipo', 'empresa', 'tenant', 'proveedor')
    else:
        licencias = Licencia.objects.all().select_related('tipo', 'empresa', 'tenant', 'proveedor')

    for lic in licencias:
        asignacion = lic.usuario_activo
        
        # Variables por defecto para registros sin asignación
        usuario_nombre = "DISPONIBLE"
        email_usuario = "-"
        centro_costos = "-"
        area_code = "-"
        division_code = "-"
        unidad_nombre = "-"
        fecha_asignacion_str = "-"

        if asignacion:
            emp = asignacion.empleado
            
            # Refresco del ORM para garantizar la captura de campos cacheados en memoria
            try:
                emp.refresh_from_db()
            except Exception:
                pass 

            usuario_nombre = emp.nombre_completo
            email_usuario = getattr(emp, 'email_principal', getattr(emp, 'email', '-')) or "-"
            centro_costos = emp.centro_de_costos if emp.centro_de_costos else "-"
            
            if asignacion.fecha_asignacion:
                fecha_asignacion_str = asignacion.fecha_asignacion.strftime('%d/%m/%Y')

            # Extracción de estructura organizacional
            if emp.area: area_code = emp.area.codigo
            if emp.division: division_code = emp.division.codigo
            if hasattr(emp, 'unidad') and emp.unidad: unidad_nombre = emp.unidad.nombre

        ws.append([
            lic.tipo.nombre,
            lic.tipo.fabricante,
            lic.proveedor.nombre if lic.proveedor else "Directo",
            lic.tenant.nombre,
            lic.empresa.nombre if lic.empresa else "-",
            lic.estado,
            usuario_nombre,
            email_usuario,
            centro_costos,
            area_code,
            division_code,
            unidad_nombre,
            fecha_asignacion_str, 
            lic.fecha_vencimiento,
        ])

    # Autoajuste dinámico de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length: 
                    max_length = len(str(cell.value))
            except Exception: 
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    fecha = timezone.now().strftime('%d-%m-%Y')
    response['Content-Disposition'] = f'attachment; filename="Reporte_Licencias_{fecha}.xlsx"'
    wb.save(response)
    
    return response
# ==========================================
# MÓDULO token
# ==========================================

def validar_token_bloqueo(request):
    """
    Pantalla de desbloqueo tras 3 intentos fallidos.

    Si el signal `preparar_desbloqueo` dejo el flag `enviar_token_pendiente`
    en sesion (caso normal: el browser acaba de seguir el redirect tras el
    lockout), aqui se dispara el envio automatico del token en contexto de
    vista normal (donde send_mail funciona igual que en el reenvio manual).
    """
    from .services import enviar_token_desbloqueo

    username = request.session.get('usuario_bloqueado_nombre')
    if not username:
        return redirect('login')

    # Auto-envio diferido desde el signal: solo en GET y solo si el flag
    # esta presente. Se ejecuta una sola vez (limpia el flag si tuvo exito).
    if request.method == 'GET' and request.session.get('enviar_token_pendiente'):
        user = User.objects.filter(username=username).first()
        if user:
            ok, info = enviar_token_desbloqueo(user=user, source="autosend")
            if ok:
                request.session.pop('enviar_token_pendiente', None)
                request.session.modified = True
                messages.info(request, info)
            else:
                # Si fallo, dejamos el flag para que el siguiente refresh
                # reintente, y avisamos al usuario que puede reenviar.
                messages.warning(
                    request,
                    f"{info} Pulsa 'Reenviar codigo' para intentarlo nuevamente.",
                )

    if request.method == 'POST':
        token_ingresado = request.POST.get('token')
        token_real = cache.get(f'token_desbloqueo_{username}')

        if token_real and token_ingresado == token_real:
            user = User.objects.get(username=username)
            # Limpia el bloqueo de Axes (username + ip). Nota: la función `reset` usa `ip`, no `ip_address`.
            reset(username=username, ip=request.META.get('REMOTE_ADDR'))

            # LOGIN AUTOMÁTICO
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            cache.delete(f'token_desbloqueo_{username}')
            request.session.pop('usuario_bloqueado_nombre', None)
            request.session.pop('enviar_token_pendiente', None)

            messages.success(request, "Acceso concedido mediante token de seguridad.")
            return redirect('dashboard_general')
        else:
            messages.error(request, "Código incorrecto o expirado.")

    return render(request, 'registration/desbloqueo_token.html')


def enviar_token_bloqueo(request):
    """
    Envia (bajo demanda) un token de desbloqueo al correo del usuario bloqueado por Axes.
    Se usa desde la pantalla /desbloqueo-seguro/ para evitar spam y correos duplicados.

    La logica de envio vive en `licencias.services.desbloqueo`. Esta vista
    solo orquesta: valida sesion, llama al service y traduce el resultado a
    `messages` para el usuario.
    """
    from .services import enviar_token_desbloqueo

    username = request.session.get('usuario_bloqueado_nombre')
    if not username:
        return redirect('login')

    if request.method != 'POST':
        return redirect('validar_token_bloqueo')

    user = User.objects.filter(username=username).first()
    if not user:
        messages.error(request, "No se pudo enviar el código: usuario no encontrado.")
        return redirect('validar_token_bloqueo')

    ok, info = enviar_token_desbloqueo(user=user, source="manual")
    if ok:
        messages.success(request, info)
    else:
        # info ya viene formateado por el service ("No se pudo enviar...",
        # "Se envio recientemente...", etc.).
        messages.warning(request, info)
    return redirect('validar_token_bloqueo')
# ==========================================
# MÓDULO PRINCIPAL (DASHBOARD Y KPIS)
# ==========================================

@login_required
def inicio(request):
    """Pantalla de bienvenida y resumen rapido de la plataforma."""
    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)

    puede_ver_licencias = request.user.has_perm('licencias.view_licencia')
    puede_ver_empleados = request.user.has_perm('empleados.view_empleado')
    puede_ver_bitacora = request.user.has_perm('bitacora.view_bitacora')

    licencias = Licencia.objects.all()
    asignaciones_activas = Asignacion.objects.filter(activo=True)

    context = {
        'tenants': Tenant.objects.all(),
        'titulo': 'Inicio',
        'hoy': hoy,
        'puede_ver_licencias': puede_ver_licencias,
        'puede_ver_empleados': puede_ver_empleados,
        'puede_ver_bitacora': puede_ver_bitacora,
        'total_licencias': licencias.count() if puede_ver_licencias else 0,
        'licencias_asignadas': asignaciones_activas.count() if puede_ver_licencias else 0,
        'licencias_disponibles': licencias.exclude(asignaciones__activo=True).filter(fecha_vencimiento__gte=hoy).count() if puede_ver_licencias else 0,
        'licencias_por_vencer': licencias.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite_30_dias).count() if puede_ver_licencias else 0,
        'empleados_activos': Empleado.objects.filter(activo=True).count() if puede_ver_empleados else 0,
        'empresas_registradas': Empresa.objects.count() if request.user.has_perm('licencias.view_empresa') else 0,
        'ultimas_asignaciones': asignaciones_activas.select_related('licencia__tipo', 'empleado').order_by('-fecha_asignacion')[:4] if puede_ver_licencias else [],
    }
    return render(request, 'licencias/inicio.html', context)


@login_required
def dashboard(request, tenant_id=None):
    """Vista gerencial de licencias. KPIs vía selector agregado (1 query)."""
    exigir_permiso(request, 'licencias.view_licencia')
    tenants = Tenant.objects.all()

    if tenant_id:
        tenant_seleccionado = get_object_or_404(Tenant, pk=tenant_id)
        licencias = Licencia.objects.filter(tenant=tenant_seleccionado).select_related(
            'tipo', 'empresa', 'proveedor', 'tenant'
        )
        titulo = f"Licencias de {tenant_seleccionado.nombre}"
    else:
        tenant_seleccionado = None
        licencias = Licencia.objects.all().select_related(
            'tipo', 'empresa', 'proveedor', 'tenant'
        )
        titulo = "Todas las Licencias"

    empleados = Empleado.objects.filter(activo=True).order_by('nombre_completo')
    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)
    form_licencia = LicenciaForm()

    kpis = obtener_kpis_dashboard(tenant=tenant_seleccionado)

    context = {
        'tenants': tenants,
        'tenant_seleccionado': tenant_seleccionado,
        'licencias': licencias,
        'empleados': empleados,
        'titulo': titulo,
        'kpi_total': kpis['total'],
        'kpi_ocupadas': kpis['ocupadas'],
        'kpi_disponibles': kpis['disponibles'],
        'kpi_vencidas': kpis['vencidas'],
        'kpi_por_vencer': kpis['por_vencer'],
        'hoy': hoy,
        'limite_30_dias': limite_30_dias,
        'form_licencia': form_licencia,
    }
    return render(request, 'licencias/dashboard.html', context)


# ==========================================
# MÓDULO DE TRANSACCIONES DE LICENCIAS
# ==========================================

@login_required
def asignar_licencia(request, licencia_id):
    """Vincula una licencia a un empleado. Delega reglas de negocio al service."""
    exigir_permiso(request, 'licencias.add_asignacion')
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))

    empleado_id = request.POST.get('empleado_id')
    try:
        asignacion = svc_asignar(licencia_id, empleado_id, request)
    except (LicenciaNoEncontradaError, EmpleadoNoEncontradoError) as e:
        raise Http404(str(e))
    except LicenciaYaAsignadaError as e:
        messages.error(
            request,
            f"Violación de concurrencia: la licencia ya fue asignada a {e.empleado_actual_nombre}."
        )
    except EmpleadoYaTieneTipoError as e:
        messages.warning(
            request,
            f"Regla de negocio: {e.empleado_nombre} ya posee una instancia de '{e.tipo_nombre}' activa."
        )
    else:
        messages.success(
            request,
            f"Transacción exitosa: Licencia asignada a {asignacion.empleado.nombre_completo}."
        )

    return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))


@login_required
def liberar_licencia(request, licencia_id):
    """Revoca la asignación activa de una licencia. Delega al service."""
    exigir_permiso(request, 'licencias.change_asignacion')
    licencia = get_object_or_404(Licencia, pk=licencia_id)
    asignacion_activa = licencia.asignaciones.filter(activo=True).first()

    if asignacion_activa is None:
        messages.warning(request, "El activo no presentaba asignaciones activas.")
        return redirect('dashboard_general')

    motivo = request.POST.get('motivo', '')
    try:
        svc_liberar(asignacion_activa.id, motivo, request)
    except AsignacionInactivaError:
        messages.warning(request, "La asignación ya no estaba activa.")
    else:
        messages.success(
            request,
            "Activo revocado. Se consolidó el registro en la bitácora de auditoría."
        )

    return redirect('dashboard_general')


# ==========================================
# MÓDULO DE GESTIÓN DE IDENTIDADES (EMPLEADOS)
# ==========================================

@login_required
def lista_empleados(request):
    """Gestor principal del directorio de identidades y altas de personal."""
    if request.method == 'POST':
        exigir_permiso(request, 'empleados.add_empleado')
    else:
        exigir_permiso(request, 'empleados.view_empleado')
    empleados = Empleado.objects.all().select_related('empresa', 'area', 'division').order_by('nombre_completo')
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            empleado_creado = form.save()
            log_crear_empleado(request, empleado_creado)
            messages.success(request, "Registro de identidad completado con éxito.")
            return redirect('lista_empleados')
        else:
            messages.error(request, "Fallo de validación: Verifique conflictos de CI o Correo Electrónico.")
    else:
        form = EmpleadoForm()

    context = {
        'empleados': empleados,
        'form': form,
        'titulo': 'Directorio de Identidades'
    }
    return render(request, 'empleados.html', context)


@login_required
def editar_empleado(request, empleado_id):
    """Actualización de metadata operativa de una identidad existente."""
    exigir_permiso(request, 'empleados.change_empleado')
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            empleado_actualizado = form.save()
            log_editar_empleado(request, empleado_actualizado)
            messages.success(request, f"Metadata de {empleado.nombre_completo} actualizada correctamente.")
            return redirect('lista_empleados')
    else:
        form = EmpleadoForm(instance=empleado)

    context = {
        'form': form,
        'empleado': empleado,
        'titulo': f'Editar Identidad: {empleado.nombre_completo}'
    }
    return render(request, 'editar_empleado.html', context)
# ==========================================
# MÓDULO DE CICLO DE VIDA DEL EMPLEADO
# ==========================================

@login_required
def baja_empleado(request, empleado_id):
    """Inhabilita empleado y revoca licencias en cascada. Delega al service."""
    exigir_permiso(request, 'empleados.change_empleado')
    try:
        result = svc_baja_empleado(empleado_id, request)
    except EmpleadoNoEncontradoError as e:
        raise Http404(str(e))
    except EmpleadoYaInactivoError as e:
        messages.warning(request, f"{e.empleado_nombre} ya se encontraba inactivo.")
        return redirect('lista_empleados')

    empleado = result['empleado']
    n = result['licencias_liberadas']
    msg = f"Baja operativa procesada para {empleado.nombre_completo}."
    if n > 0:
        msg += f" Se liberaron {n} activos vinculados."
    messages.success(request, msg)
    return redirect('lista_empleados')


@login_required
def reactivar_empleado(request, empleado_id):
    """Restablece el estado operativo de una identidad previamente inhabilitada."""
    exigir_permiso(request, 'empleados.change_empleado')
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.activo = True
    empleado.save()
    
    log_reactivar_empleado(request, empleado)
    messages.success(request, f"Identidad operativa restablecida: {empleado.nombre_completo}.")
    return redirect('lista_empleados')

# ==========================================
# ENDPOINTS ASÍNCRONOS (AJAX / CASCADAS)
# ==========================================

@login_required
def cargar_unidades(request):
    """Endpoint API para listado dinámico de Unidades filtradas por Área."""
    exigir_permiso(request, 'empleados.view_unidad')
    area_id = request.GET.get('area_id')
    unidades = Unidad.objects.filter(area_id=area_id).order_by('nombre') if area_id else Unidad.objects.none()
    return JsonResponse(list(unidades.values('id', 'nombre')), safe=False)


@login_required
def cargar_areas(request):
    """Endpoint API para listado dinámico de Áreas formateadas para Select2."""
    exigir_permiso(request, 'empleados.view_gerenciaarea')
    empresa_id = request.GET.get('empresa_id')
    areas_list = []
    
    if empresa_id:
        areas = GerenciaArea.objects.filter(empresa_id=empresa_id).order_by('nombre')
        for area in areas:
            codigo = area.codigo if area.codigo else "S/C"
            areas_list.append({'id': area.id, 'texto': f"{codigo} - {area.nombre}"})
            
    return JsonResponse(areas_list, safe=False)


@login_required
def cargar_divisiones(request):
    """Endpoint API para listado dinámico de Divisiones filtradas por Empresa."""
    exigir_permiso(request, 'empleados.view_gerenciadivision')
    empresa_id = request.GET.get('empresa_id')
    divisiones_list = []
    
    if empresa_id:
        divisiones = GerenciaDivision.objects.filter(empresa_id=empresa_id).order_by('codigo')
        for div in divisiones:
            divisiones_list.append({'id': div.id, 'texto': f"{div.codigo} - {div.nombre}"})
            
    return JsonResponse(divisiones_list, safe=False)


@login_required
def cargar_empresas(request):
    """Endpoint API para despliegue en cascada: Tenant -> Empresa."""
    exigir_permiso(request, 'licencias.view_empresa')
    tenant_id = request.GET.get('tenant_id')
    empresas = Empresa.objects.filter(tenant_id=tenant_id).order_by('nombre') if tenant_id else Empresa.objects.none()
    return JsonResponse(list(empresas.values('id', 'nombre')), safe=False)


# ==========================================
# MÓDULO DE CONFIGURACIÓN GLOBAL UNIFICADO
# ==========================================

@login_required
def configuracion(request):
    """
    Panel de administración de catálogos paramétricos unificado.
    Gestiona altas de Tenants, Empresas, Proveedores, SKUs de Licencias, Divisiones, Áreas y Unidades.
    """
    # 1. UNIFICACIÓN DE PERMISOS
    if request.method == 'POST':
        permisos_creacion = {
            'tenant': 'licencias.add_tenant',
            'empresa': 'licencias.add_empresa',
            'proveedor': 'licencias.add_proveedor',
            'tipo_licencia': 'licencias.add_tipolicencia',
            'division': 'empleados.add_gerenciadivision',
            'area': 'empleados.add_gerenciaarea',
            'unidad': 'empleados.add_unidad',
        }
        exigir_permiso(request, permisos_creacion.get(request.POST.get('tipo_formulario'), 'licencias.view_empresa'))
    else:
        exigir_algun_permiso(request, [
            'licencias.view_tenant',
            'licencias.view_empresa',
            'licencias.view_proveedor',
            'licencias.view_tipolicencia',
            'empleados.view_gerenciadivision',
            'empleados.view_gerenciaarea',
            'empleados.view_unidad',
        ])

    # 2. UNIFICACIÓN DE CONSULTAS (PREVENCIÓN N+1)
    tenants = Tenant.objects.all().order_by('nombre')
    empresas = Empresa.objects.all().select_related('tenant').order_by('tenant__nombre', 'nombre')
    proveedores = Proveedor.objects.all().order_by('nombre')
    tipos_licencia = TipoLicencia.objects.all().order_by('fabricante', 'nombre')
    divisiones = GerenciaDivision.objects.all().select_related('empresa').order_by('empresa__nombre', 'nombre')
    areas = GerenciaArea.objects.all().select_related('empresa', 'division').order_by('empresa__nombre', 'nombre')
    unidades = Unidad.objects.all().select_related('area').order_by('area__nombre', 'nombre')

    # 3. UNIFICACIÓN DE FORMULARIOS
    form_tenant = TenantForm()
    form_empresa = EmpresaForm()
    form_proveedor = ProveedorForm()
    form_tipo = TipoLicenciaForm()
    form_division = GerenciaDivisionForm()
    form_area = GerenciaAreaForm()
    form_unidad = UnidadForm()

    # 4. PROCESAMIENTO DE TODOS LOS MÉTODOS POST
    if request.method == 'POST':
        tipo = request.POST.get('tipo_formulario') 

        if tipo == 'tenant':
            form_tenant = TenantForm(request.POST)
            if form_tenant.is_valid():
                tenant = form_tenant.save()
                log_tenant_crear(request, tenant)
                messages.success(request, "Grupo corporativo (Tenant) aprovisionado.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'empresa':
            form_empresa = EmpresaForm(request.POST)
            if form_empresa.is_valid():
                empresa = form_empresa.save()
                log_empresa_crear(request, empresa)
                messages.success(request, "Razón social aprovisionada.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'proveedor':
            form_proveedor = ProveedorForm(request.POST)
            if form_proveedor.is_valid():
                proveedor = form_proveedor.save()
                log_proveedor_crear(request, proveedor)
                messages.success(request, "Socio comercial (Proveedor) registrado.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'tipo_licencia':
            form_tipo = TipoLicenciaForm(request.POST)
            if form_tipo.is_valid():
                tipo_lic = form_tipo.save()
                log_tipo_licencia_crear(request, tipo_lic)
                messages.success(request, "SKU de licencia ingresado al catálogo.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'division':
            form_division = GerenciaDivisionForm(request.POST)
            if form_division.is_valid():
                division = form_division.save()
                log_division_crear(request, division)
                messages.success(request, "Entidad organizacional (División) registrada.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'area':
            form_area = GerenciaAreaForm(request.POST)
            if form_area.is_valid():
                area = form_area.save()
                log_area_crear(request, area)
                messages.success(request, "Entidad organizacional (Área) registrada.")
                return _redirect_config_tab(active_tab)

        elif tipo == 'unidad':
            form_unidad = UnidadForm(request.POST)
            if form_unidad.is_valid():
                unidad = form_unidad.save()
                log_unidad_crear(request, unidad)
                messages.success(request, "Entidad organizacional (Unidad) registrada.")
                return _redirect_config_tab(active_tab)

    # 5. DICCIONARIO DE CONTEXTO FINAL
    context = {
        'tenants': tenants,
        'empresas': empresas,
        'proveedores': proveedores,
        'tipos_licencia': tipos_licencia,
        'divisiones': divisiones,
        'areas': areas,
        'unidades': unidades,
        'form_tenant': form_tenant,
        'form_empresa': form_empresa,
        'form_proveedor': form_proveedor,
        'form_tipo': form_tipo,
        'form_division': form_division,
        'form_area': form_area,
        'form_unidad': form_unidad,
        'titulo': 'Parametrización Global'
    }
    return render(request, 'licencias/configuracion.html', context)

# ==========================================
# CONTROLADORES DE EDICIÓN DE CATÁLOGOS
# ==========================================

@login_required
def editar_licencia(request, licencia_id):
    """Actualización de atributos físicos de un activo de software."""
    exigir_permiso(request, 'licencias.change_licencia')
    licencia = get_object_or_404(Licencia, id=licencia_id)
    
    if request.method == 'POST':
        form = LicenciaForm(request.POST, instance=licencia)
        if form.is_valid():
            form.save()
            log_editar_licencia(request, licencia)
            messages.success(request, f"Parámetros del activo {licencia.tipo.nombre} actualizados.")
            return redirect('dashboard_general') 
        else:
            messages.error(request, "Error de validación en la actualización del activo.")
    else:
        form = LicenciaForm(instance=licencia)
        
    context = {
        'form': form,
        'licencia': licencia,
        'titulo': f'Edición de Activo: {licencia.tipo.nombre}'
    }
    return render(request, 'licencias/editar_licencia.html', context)


@login_required
def editar_division(request, pk):
    exigir_permiso(request, 'empleados.change_gerenciadivision')
    division = get_object_or_404(GerenciaDivision, pk=pk)
    if request.method == 'POST':
        form = GerenciaDivisionForm(request.POST, instance=division)
        if form.is_valid():
            form.save()
            log_division_editar(request, division)
            messages.success(request, "Estructura divisional actualizada.")
            return _redirect_config_tab('divisiones')
    else:
        form = GerenciaDivisionForm(instance=division)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar División: {division.codigo}'})


@login_required
def editar_area(request, pk):
    exigir_permiso(request, 'empleados.change_gerenciaarea')
    area = get_object_or_404(GerenciaArea, pk=pk)
    if request.method == 'POST':
        form = GerenciaAreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            log_area_editar(request, area)
            messages.success(request, "Metadatos del área operativa actualizados.")
            return _redirect_config_tab(active_tab)
    else:
        form = GerenciaAreaForm(instance=area)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar Área: {area.codigo}'})


@login_required
def editar_unidad(request, pk):
    exigir_permiso(request, 'empleados.change_unidad')
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == 'POST':
        form = UnidadForm(request.POST, instance=unidad)
        if form.is_valid():
            form.save()
            log_unidad_editar(request, unidad)
            messages.success(request, "Parámetros de la unidad modificados.")
            return _redirect_config_tab(active_tab)
    else:
        form = UnidadForm(instance=unidad)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar Unidad: {unidad.nombre}', 'active_tab': 'unidades'})


@login_required
def editar_tenant(request, pk):
    exigir_permiso(request, 'licencias.change_tenant')
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            log_tenant_editar(request, tenant)
            messages.success(request, "Propiedades del Tenant corporativo actualizadas.")
            return _redirect_config_tab('tenants')
    else:
        form = TenantForm(instance=tenant)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Propiedades de Tenant: {tenant.nombre}', 'active_tab': 'tenants'})
# ==========================================
# EDICIÓN DE PARÁMETROS GLOBALES (TI)
# ==========================================

@login_required
def editar_empresa(request, pk):
    """Modificación de metadatos de una razón social (Empresa)."""
    exigir_permiso(request, 'licencias.change_empresa')
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            log_empresa_editar(request, empresa)
            messages.success(request, "Razón social actualizada exitosamente.")
            return _redirect_config_tab(active_tab)
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar Empresa: {empresa.nombre}', 'active_tab': 'empresas'})


@login_required
def editar_proveedor(request, pk):
    """Modificación de parámetros de un socio comercial."""
    exigir_permiso(request, 'licencias.change_proveedor')
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            log_proveedor_editar(request, proveedor)
            messages.success(request, "Datos de proveedor comercial actualizados.")
            return _redirect_config_tab('proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar Proveedor: {proveedor.nombre}', 'active_tab': 'proveedores'})


@login_required
def editar_tipo_licencia(request, pk):
    """Edición del catálogo de SKUs de software."""
    exigir_permiso(request, 'licencias.change_tipolicencia')
    tipo = get_object_or_404(TipoLicencia, pk=pk)
    if request.method == 'POST':
        form = TipoLicenciaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            log_tipo_licencia_editar(request, tipo)
            messages.success(request, "Especificaciones de SKU de software actualizadas.")
            return _redirect_config_tab('tipos')
    else:
        form = TipoLicenciaForm(instance=tipo)
    return render(request, 'licencias/editar_catalogo.html', {'form': form, 'titulo': f'Editar Software: {tipo.nombre}', 'active_tab': 'tipos'})


# ==========================================
# MÓDULO DE ELIMINACIÓN Y PURGA DE DATOS
# ==========================================

@login_required
def eliminar_division(request, pk):
    exigir_permiso(request, 'empleados.delete_gerenciadivision')
    _obj = get_object_or_404(GerenciaDivision, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_division_eliminar(request, _label)
    messages.success(request, "Entidad divisional purgada del sistema.")
    return _redirect_config_tab('divisiones')

@login_required
def eliminar_area(request, pk):
    exigir_permiso(request, 'empleados.delete_gerenciaarea')
    _obj = get_object_or_404(GerenciaArea, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_area_eliminar(request, _label)
    messages.success(request, "Área operativa purgada del sistema.")
    return _redirect_config_tab(active_tab)

@login_required
def eliminar_unidad(request, pk):
    exigir_permiso(request, 'empleados.delete_unidad')
    _obj = get_object_or_404(Unidad, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_unidad_eliminar(request, _label)
    messages.success(request, "Unidad purgada del sistema.")
    return _redirect_config_tab('unidades')

@login_required
def eliminar_tenant(request, pk):
    exigir_permiso(request, 'licencias.delete_tenant')
    _obj = get_object_or_404(Tenant, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_tenant_eliminar(request, _label)
    messages.success(request, "Grupo corporativo purgado del ecosistema.")
    return _redirect_config_tab('tenants')

@login_required
def eliminar_empresa(request, pk):
    exigir_permiso(request, 'licencias.delete_empresa')
    _obj = get_object_or_404(Empresa, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_empresa_eliminar(request, _label)
    messages.success(request, "Razón social purgada del catálogo.")
    return _redirect_config_tab(active_tab)

@login_required
def eliminar_proveedor(request, pk):
    exigir_permiso(request, 'licencias.delete_proveedor')
    _obj = get_object_or_404(Proveedor, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_proveedor_eliminar(request, _label)
    messages.success(request, "Proveedor retirado del catálogo.")
    return _redirect_config_tab(active_tab)

@login_required
def eliminar_tipo_licencia(request, pk):
    exigir_permiso(request, 'licencias.delete_tipolicencia')
    _obj = get_object_or_404(TipoLicencia, pk=pk)
    _label = str(_obj)
    _obj.delete()
    log_tipo_licencia_eliminar(request, _label)
    messages.success(request, "SKU de software retirado del catálogo global.")
    return _redirect_config_tab(active_tab)

@login_required
def eliminar_licencia(request, licencia_id):
    """Destrucción física del registro de activo de software y sus dependencias."""
    licencia = get_object_or_404(Licencia, id=licencia_id)
    exigir_permiso(request, 'licencias.delete_licencia')
    nombre_licencia = licencia.tipo.nombre
    licencia_label = str(licencia)
    licencia_pk = licencia.pk
    licencia.delete()
    
    log_eliminar_licencia(request, licencia_label, licencia_id=licencia_pk)
    messages.success(request, f"El activo {nombre_licencia} ha sido eliminado permanentemente del inventario.")
    return redirect('dashboard_general')


# ==========================================
# MÓDULO DE APROVISIONAMIENTO DE INVENTARIO
# ==========================================

@login_required
def crear_licencia(request):
    """
    Controlador para la ingesta manual de nuevos activos de software.
    Implementa inserción masiva (Bulk Create) para optimizar transacciones I/O
    y minimizar la latencia en la base de datos durante cargas de alto volumen.
    """
    exigir_permiso(request, 'licencias.add_licencia')
    if request.method == 'POST':
        form = LicenciaForm(request.POST)
        
        # 1. Captura del volumen de instancias a aprovisionar
        cantidad = int(request.POST.get('cantidad_masiva', 1))
        
        if form.is_valid():
            licencia_base = form.save(commit=False)
            nuevas_licencias = []
            
            # 2. Generación del lote de activos en memoria RAM
            for _ in range(cantidad):
                nueva_lic = Licencia(
                    tipo=licencia_base.tipo,
                    empresa=licencia_base.empresa,
                    tenant=licencia_base.tenant,
                    proveedor=licencia_base.proveedor,
                    fecha_compra=licencia_base.fecha_compra,
                    fecha_vencimiento=licencia_base.fecha_vencimiento
                )
                nuevas_licencias.append(nueva_lic)
            
            # 3. Ejecución de Bulk Create (Transacción optimizada)
            Licencia.objects.bulk_create(nuevas_licencias)
            log_creacion_licencias(request, licencia_base, cantidad=cantidad)
            
            if cantidad > 1:
                messages.success(request, f"Aprovisionamiento masivo exitoso: {cantidad} instancias de '{licencia_base.tipo.nombre}' registradas.")
            else:
                messages.success(request, "Activo de software ingresado al inventario exitosamente.")
                
            return redirect('dashboard_general')
            
        else:
            messages.error(request, "Fallo de validación estructural. Verifique los parámetros de entrada.")
            
    return redirect('dashboard_general')


# ==========================================
# BORRADO MASIVO DE LICENCIAS
# ==========================================
@login_required
def eliminar_licencias_masivo(request):
    if request.method == 'POST':
        # Recibimos el texto con los IDs (ejemplo: '["1", "5", "12"]')
        ids_json = request.POST.get('ids_licencias', '[]')
        
        try:
            # Lo convertimos a una lista real de Python
            ids = json.loads(ids_json)
            
            if ids:
                # Magia de Django: Buscamos todas las licencias que estén en esa lista y las borramos de golpe
                cantidad, _ = Licencia.objects.filter(id__in=ids).delete()
                if cantidad:
                    log_eliminar_licencias_masivo(request, cantidad)
                messages.success(request, f"¡Limpieza completada! Se eliminaron {cantidad} licencias permanentemente.")
            else:
                messages.warning(request, "No se seleccionó ninguna licencia para borrar.")
                
        except Exception as e:
            messages.error(request, f"Ocurrió un error al intentar borrar las licencias: {str(e)}")

    return redirect('dashboard_general')
