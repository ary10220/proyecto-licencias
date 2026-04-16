import json
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth import login
from axes.utils import reset
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction



from empleados.models import Empleado, GerenciaDivision, GerenciaArea, Unidad
from .models import Licencia, Asignacion, Tenant, Empresa, Proveedor, TipoLicencia
from .forms import (
    EmpleadoForm, GerenciaDivisionForm, GerenciaAreaForm, UnidadForm, 
    TenantForm, EmpresaForm, ProveedorForm, TipoLicenciaForm, LicenciaForm
)

# ==========================================
# MÓDULO DE EXPORTACIÓN Y REPORTES
# ==========================================

@login_required
def exportar_excel(request, tenant_id=None):
    """
    Genera un reporte consolidado en formato Excel (.xlsx) de los activos de software.
    Implementa OpenPyXL para el formateo directo del buffer de memoria sin escritura en disco.
    """
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
    username = request.session.get('usuario_bloqueado_nombre')
    
    if not username:
        return redirect('login')

    if request.method == 'POST':
        token_ingresado = request.POST.get('token')
        token_real = cache.get(f'token_desbloqueo_{username}')

        if token_real and token_ingresado == token_real:
            user = User.objects.get(username=username)
            reset(username=username) # Limpia el bloqueo de Axes
            
            # LOGIN AUTOMÁTICO
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            cache.delete(f'token_desbloqueo_{username}')
            del request.session['usuario_bloqueado_nombre']
            
            messages.success(request, "Acceso concedido mediante token de seguridad.")
            return redirect('dashboard_general')
        else:
            messages.error(request, "Código incorrecto o expirado.")

    return render(request, 'registration/desbloqueo_token.html')
# ==========================================
# MÓDULO PRINCIPAL (DASHBOARD Y KPIS)
# ==========================================

@login_required
def dashboard(request, tenant_id=None):
    """
    Controlador principal de la vista gerencial. 
    Calcula KPIs operativos (Asignaciones, Disponibilidad, Riesgo de Vencimiento)
    mediante iteración única para minimizar la carga transaccional en la base de datos.
    """
    tenants = Tenant.objects.all()
    
    if tenant_id:
        tenant_seleccionado = get_object_or_404(Tenant, pk=tenant_id)
        licencias = Licencia.objects.filter(tenant=tenant_seleccionado).select_related('tipo', 'empresa', 'proveedor', 'tenant')
        titulo = f"Licencias de {tenant_seleccionado.nombre}"
    else:
        tenant_seleccionado = None
        licencias = Licencia.objects.all().select_related('tipo', 'empresa', 'proveedor', 'tenant')
        titulo = "Todas las Licencias"

    empleados = Empleado.objects.filter(activo=True).order_by('nombre_completo')

    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)

    # Cálculo algorítmico de KPIs
    total_licencias = licencias.count()
    ocupadas = 0
    disponibles = 0
    vencidas = 0
    por_vencer = 0

    for lic in licencias:
        if lic.usuario_activo:
            ocupadas += 1
            
        # Evaluación de riesgos y caducidad
        if lic.fecha_vencimiento < hoy:
            vencidas += 1
        elif lic.fecha_vencimiento <= limite_30_dias:
            por_vencer += 1
            
        # Disponibilidad neta
        if not lic.usuario_activo and lic.fecha_vencimiento >= hoy:
            disponibles += 1

    form_licencia = LicenciaForm()
    
    context = {
        'tenants': tenants,
        'tenant_seleccionado': tenant_seleccionado,
        'licencias': licencias,
        'empleados': empleados,
        'titulo': titulo,
        
        # Métricas de telemetría
        'kpi_total': total_licencias,
        'kpi_ocupadas': ocupadas,
        'kpi_disponibles': disponibles,
        'kpi_vencidas': vencidas,
        'kpi_por_vencer': por_vencer,
        
        'hoy': hoy,
        'limite_30_dias': limite_30_dias,
        'form_licencia': form_licencia,
    }
    return render(request, 'dashboard.html', context)


# ==========================================
# MÓDULO DE TRANSACCIONES DE LICENCIAS
# ==========================================

@login_required
def asignar_licencia(request, licencia_id):
    """
    Ejecuta la transacción de vinculación entre un activo de software y un colaborador.
    Implementa validaciones de control de duplicidad y concurrencia.
    """
    if request.method == 'POST':
        licencia = get_object_or_404(Licencia, pk=licencia_id)
        empleado_id = request.POST.get('empleado_id')
        empleado = get_object_or_404(Empleado, pk=empleado_id)

        # Prevención de condición de carrera (Race Condition)
        if licencia.usuario_activo:
            messages.error(request, f"Violación de concurrencia: La licencia ya fue asignado a {licencia.usuario_activo.empleado.nombre_completo}.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))

        # Control de duplicidad de licenciamiento por usuario
        tiene_duplicada = Asignacion.objects.filter(
            empleado=empleado,
            licencia__tipo=licencia.tipo,
            activo=True
        ).exists()

        if tiene_duplicada:
            messages.warning(request, f"Regla de negocio: {empleado.nombre_completo} ya posee una instancia de '{licencia.tipo.nombre}' activa.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))

        Asignacion.objects.create(
            licencia=licencia,
            empleado=empleado,
            activo=True
        )
        messages.success(request, f"Transacción exitosa: Licencia asignada a {empleado.nombre_completo}.")
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))


@login_required
def liberar_licencia(request, licencia_id):
    """
    Revoca el acceso a un activo de software, clausurando la asignación activa
    y generando el registro en el historial de auditoría.
    """
    licencia = get_object_or_404(Licencia, pk=licencia_id)
    asignaciones_activas = licencia.asignaciones.filter(activo=True)
    
    if asignaciones_activas.exists():
        count = 0
        for asignacion in asignaciones_activas:
            asignacion.activo = False
            if not asignacion.fecha_retiro:
                asignacion.fecha_retiro = timezone.now()
            asignacion.save() 
            count += 1
            
        messages.success(request, f"Activo revocado. Se consolidaron {count} registros en la bitácora de auditoría.")
    else:
        messages.warning(request, "El activo no presentaba asignaciones activas.")
    
    return redirect('dashboard_general')


# ==========================================
# MÓDULO DE GESTIÓN DE IDENTIDADES (EMPLEADOS)
# ==========================================

@login_required
def lista_empleados(request):
    """Gestor principal del directorio de identidades y altas de personal."""
    empleados = Empleado.objects.all().select_related('empresa', 'area', 'division').order_by('nombre_completo')
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
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
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
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
    """
    Inhabilita operativamente a un colaborador y ejecuta la política de
    revocación automática de todos sus activos de software vinculados.
    """
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # 1. Inhabilitación de la identidad
    empleado.activo = False
    empleado.save()
    
    # Importación local para mitigación de dependencias circulares
    from .models import Asignacion 
    asignaciones_activas = Asignacion.objects.filter(empleado=empleado, activo=True)
    
    # 2. Revocación en lote de activos asignados
    licencias_liberadas = 0
    for asignacion in asignaciones_activas:
        asignacion.activo = False
        asignacion.fecha_retiro = timezone.now()
        asignacion.observaciones = f"Revocación automatizada por baja operativa el {timezone.now().strftime('%d/%m/%Y')}."
        asignacion.save()
        licencias_liberadas += 1
        
    mensaje = f"Baja operativa procesada para {empleado.nombre_completo}."
    if licencias_liberadas > 0:
        mensaje += f" Se liberaron {licencias_liberadas} activos vinculados."
        
    messages.success(request, mensaje)
    return redirect('lista_empleados')


@login_required
def reactivar_empleado(request, empleado_id):
    """Restablece el estado operativo de una identidad previamente inhabilitada."""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.activo = True
    empleado.save()
    
    messages.success(request, f"Identidad operativa restablecida: {empleado.nombre_completo}.")
    return redirect('lista_empleados')


# ==========================================
# MÓDULO DE ESTRUCTURA ORGANIZACIONAL
# ==========================================

@login_required
def organizacion(request):
    """
    Controlador del catálogo de estructura organizacional.
    Gestiona la visualización jerárquica y el alta de Divisiones, Áreas y Unidades.
    """
    # Optimización de consultas jerárquicas (Prevención de N+1 Queries)
    divisiones = GerenciaDivision.objects.all().select_related('empresa').order_by('empresa__nombre', 'nombre')
    areas = GerenciaArea.objects.all().select_related('empresa', 'division').order_by('empresa__nombre', 'nombre')
    unidades = Unidad.objects.all().select_related('area').order_by('area__nombre', 'nombre')

    form_division = GerenciaDivisionForm()
    form_area = GerenciaAreaForm()
    form_unidad = UnidadForm()

    if request.method == 'POST':
        # Enrutamiento de peticiones POST basado en el identificador del payload
        tipo = request.POST.get('tipo_formulario') 

        if tipo == 'division':
            form_division = GerenciaDivisionForm(request.POST)
            if form_division.is_valid():
                form_division.save()
                messages.success(request, "Entidad organizacional (División) registrada.")
                return redirect('organizacion')

        elif tipo == 'area':
            form_area = GerenciaAreaForm(request.POST)
            if form_area.is_valid():
                form_area.save()
                messages.success(request, "Entidad organizacional (Área) registrada.")
                return redirect('organizacion')

        elif tipo == 'unidad':
            form_unidad = UnidadForm(request.POST)
            if form_unidad.is_valid():
                form_unidad.save()
                messages.success(request, "Entidad organizacional (Unidad) registrada.")
                return redirect('organizacion')

    context = {
        'divisiones': divisiones,
        'areas': areas,
        'unidades': unidades,
        'form_division': form_division,
        'form_area': form_area,
        'form_unidad': form_unidad,
        'titulo': 'Estructura Organizacional'
    }
    return render(request, 'organizacion.html', context)


# ==========================================
# ENDPOINTS ASÍNCRONOS (AJAX / CASCADAS)
# ==========================================

def cargar_unidades(request):
    """Endpoint API para listado dinámico de Unidades filtradas por Área."""
    area_id = request.GET.get('area_id')
    unidades = Unidad.objects.filter(area_id=area_id).order_by('nombre') if area_id else Unidad.objects.none()
    return JsonResponse(list(unidades.values('id', 'nombre')), safe=False)


def cargar_areas(request):
    """Endpoint API para listado dinámico de Áreas formateadas para Select2."""
    empresa_id = request.GET.get('empresa_id')
    areas_list = []
    
    if empresa_id:
        areas = GerenciaArea.objects.filter(empresa_id=empresa_id).order_by('nombre')
        for area in areas:
            codigo = area.codigo if area.codigo else "S/C"
            areas_list.append({'id': area.id, 'texto': f"{codigo} - {area.nombre}"})
            
    return JsonResponse(areas_list, safe=False)


def cargar_divisiones(request):
    """Endpoint API para listado dinámico de Divisiones filtradas por Empresa."""
    empresa_id = request.GET.get('empresa_id')
    divisiones_list = []
    
    if empresa_id:
        divisiones = GerenciaDivision.objects.filter(empresa_id=empresa_id).order_by('codigo')
        for div in divisiones:
            divisiones_list.append({'id': div.id, 'texto': f"{div.codigo} - {div.nombre}"})
            
    return JsonResponse(divisiones_list, safe=False)


def cargar_empresas(request):
    """Endpoint API para despliegue en cascada: Tenant -> Empresa."""
    tenant_id = request.GET.get('tenant_id')
    empresas = Empresa.objects.filter(tenant_id=tenant_id).order_by('nombre') if tenant_id else Empresa.objects.none()
    return JsonResponse(list(empresas.values('id', 'nombre')), safe=False)


# ==========================================
# MÓDULO DE CONFIGURACIÓN GLOBAL (CATÁLOGOS)
# ==========================================

@login_required
def configuracion(request):
    """
    Panel de administración de catálogos paramétricos.
    Gestiona altas de Tenants, Empresas, Proveedores y SKUs de Licencias.
    """
    tenants = Tenant.objects.all().order_by('nombre')
    empresas = Empresa.objects.all().select_related('tenant').order_by('tenant__nombre', 'nombre')
    proveedores = Proveedor.objects.all().order_by('nombre')
    tipos_licencia = TipoLicencia.objects.all().order_by('fabricante', 'nombre')

    form_tenant = TenantForm()
    form_empresa = EmpresaForm()
    form_proveedor = ProveedorForm()
    form_tipo = TipoLicenciaForm()

    if request.method == 'POST':
        tipo = request.POST.get('tipo_formulario') 

        if tipo == 'tenant':
            form_tenant = TenantForm(request.POST)
            if form_tenant.is_valid():
                form_tenant.save()
                messages.success(request, "Grupo corporativo (Tenant) aprovisionado.")
                return redirect('configuracion')

        elif tipo == 'empresa':
            form_empresa = EmpresaForm(request.POST)
            if form_empresa.is_valid():
                form_empresa.save()
                messages.success(request, "Razón social aprovisionada.")
                return redirect('configuracion')

        elif tipo == 'proveedor':
            form_proveedor = ProveedorForm(request.POST)
            if form_proveedor.is_valid():
                form_proveedor.save()
                messages.success(request, "Socio comercial (Proveedor) registrado.")
                return redirect('configuracion')

        elif tipo == 'tipo_licencia':
            form_tipo = TipoLicenciaForm(request.POST)
            if form_tipo.is_valid():
                form_tipo.save()
                messages.success(request, "SKU de licencia ingresado al catálogo.")
                return redirect('configuracion')

    context = {
        'tenants': tenants,
        'empresas': empresas,
        'proveedores': proveedores,
        'tipos_licencia': tipos_licencia,
        'form_tenant': form_tenant,
        'form_empresa': form_empresa,
        'form_proveedor': form_proveedor,
        'form_tipo': form_tipo,
        'titulo': 'Parametrización Global'
    }
    return render(request, 'configuracion.html', context)


# ==========================================
# CONTROLADORES DE EDICIÓN DE CATÁLOGOS
# ==========================================

@login_required
def editar_licencia(request, licencia_id):
    """Actualización de atributos físicos de un activo de software."""
    licencia = get_object_or_404(Licencia, id=licencia_id)
    
    if request.method == 'POST':
        form = LicenciaForm(request.POST, instance=licencia)
        if form.is_valid():
            form.save()
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
    return render(request, 'editar_licencia.html', context)


@login_required
def editar_division(request, pk):
    division = get_object_or_404(GerenciaDivision, pk=pk)
    if request.method == 'POST':
        form = GerenciaDivisionForm(request.POST, instance=division)
        if form.is_valid():
            form.save()
            messages.success(request, "Estructura divisional actualizada.")
            return redirect('organizacion')
    else:
        form = GerenciaDivisionForm(instance=division)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar División: {division.codigo}'})


@login_required
def editar_area(request, pk):
    area = get_object_or_404(GerenciaArea, pk=pk)
    if request.method == 'POST':
        form = GerenciaAreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, "Metadatos del área operativa actualizados.")
            return redirect('organizacion')
    else:
        form = GerenciaAreaForm(instance=area)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar Área: {area.codigo}'})


@login_required
def editar_unidad(request, pk):
    unidad = get_object_or_404(Unidad, pk=pk)
    if request.method == 'POST':
        form = UnidadForm(request.POST, instance=unidad)
        if form.is_valid():
            form.save()
            messages.success(request, "Parámetros de la unidad modificados.")
            return redirect('organizacion')
    else:
        form = UnidadForm(instance=unidad)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar Unidad: {unidad.nombre}'})


@login_required
def editar_tenant(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Propiedades del Tenant corporativo actualizadas.")
            return redirect('configuracion')
    else:
        form = TenantForm(instance=tenant)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Propiedades de Tenant: {tenant.nombre}'})
# ==========================================
# EDICIÓN DE PARÁMETROS GLOBALES (TI)
# ==========================================

@login_required
def editar_empresa(request, pk):
    """Modificación de metadatos de una razón social (Empresa)."""
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Razón social actualizada exitosamente.")
            return redirect('configuracion')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar Empresa: {empresa.nombre}'})


@login_required
def editar_proveedor(request, pk):
    """Modificación de parámetros de un socio comercial."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, "Datos de proveedor comercial actualizados.")
            return redirect('configuracion')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar Proveedor: {proveedor.nombre}'})


@login_required
def editar_tipo_licencia(request, pk):
    """Edición del catálogo de SKUs de software."""
    tipo = get_object_or_404(TipoLicencia, pk=pk)
    if request.method == 'POST':
        form = TipoLicenciaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Especificaciones de SKU de software actualizadas.")
            return redirect('configuracion')
    else:
        form = TipoLicenciaForm(instance=tipo)
    return render(request, 'editar_catalogo.html', {'form': form, 'titulo': f'Editar Software: {tipo.nombre}'})


# ==========================================
# MÓDULO DE ELIMINACIÓN Y PURGA DE DATOS
# ==========================================

@login_required
def eliminar_division(request, pk):
    get_object_or_404(GerenciaDivision, pk=pk).delete()
    messages.success(request, "Entidad divisional purgada del sistema.")
    return redirect('organizacion')

@login_required
def eliminar_area(request, pk):
    get_object_or_404(GerenciaArea, pk=pk).delete()
    messages.success(request, "Área operativa purgada del sistema.")
    return redirect('organizacion')

@login_required
def eliminar_unidad(request, pk):
    get_object_or_404(Unidad, pk=pk).delete()
    messages.success(request, "Unidad purgada del sistema.")
    return redirect('organizacion')

@login_required
def eliminar_tenant(request, pk):
    get_object_or_404(Tenant, pk=pk).delete()
    messages.success(request, "Grupo corporativo purgado del ecosistema.")
    return redirect('configuracion')

@login_required
def eliminar_empresa(request, pk):
    get_object_or_404(Empresa, pk=pk).delete()
    messages.success(request, "Razón social purgada del catálogo.")
    return redirect('configuracion')

@login_required
def eliminar_proveedor(request, pk):
    get_object_or_404(Proveedor, pk=pk).delete()
    messages.success(request, "Proveedor retirado del catálogo.")
    return redirect('configuracion')

@login_required
def eliminar_tipo_licencia(request, pk):
    get_object_or_404(TipoLicencia, pk=pk).delete()
    messages.success(request, "SKU de software retirado del catálogo global.")
    return redirect('configuracion')

@login_required
def eliminar_licencia(request, licencia_id):
    """Destrucción física del registro de activo de software y sus dependencias."""
    licencia = get_object_or_404(Licencia, id=licencia_id)
    nombre_licencia = licencia.tipo.nombre
    licencia.delete()
    
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
            
            if cantidad > 1:
                messages.success(request, f"Aprovisionamiento masivo exitoso: {cantidad} instancias de '{licencia_base.tipo.nombre}' registradas.")
            else:
                messages.success(request, "Activo de software ingresado al inventario exitosamente.")
                
            return redirect('dashboard_general')
            
        else:
            messages.error(request, "Fallo de validación estructural. Verifique los parámetros de entrada.")
            
    return redirect('dashboard_general')


# ==========================================
# MOTOR DE SINCRONIZACIÓN AUTOMATIZADA M365
# ==========================================

@login_required
def sincronizar_m365(request):
    """
    Motor de ingesta y conciliación de datos contra el proveedor M365.
    Procesa múltiples hojas de cálculo vía DataFrames y ejecuta actualización
    transaccional garantizando el principio ACID en la base de datos.
    """
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        excel_file = request.FILES['archivo_excel']
        
        try:
            # 1. Extracción de datos en memoria mediante motor OpenPyXL
            diccionario_hojas = pd.read_excel(excel_file, engine='openpyxl', sheet_name=None)
            df = pd.concat(diccionario_hojas.values(), ignore_index=True)
            df.columns = df.columns.str.strip()

            creados, actualizados, asignadas, liberadas, sin_stock = 0, 0, 0, 0, 0

            # 2. Diccionario de enrutamiento de dominios corporativos
            mapa_dominios = {
                'avicolasofia.com': 'AVICOLASOFIA',
                'mamayatech.com': 'MAMAYATECH',
                'indatta.com': 'INDATTA',
                'agrosofiaservicios.com': 'AGROSOFIA'
            }

            # 3. Diccionario de homologación de SKUs (M365 vs Sistema Interno)
            mapa_licencias = {
                'ENTERPRISEPACK': 'E3',                             
                'SPE_F1': 'F3',                                     
                'O365_BUSINESS_PREMIUM': 'ESTANDAR',                
                'Office_365_E3_(no_Teams)': 'E3 (SIN TEAMS)',       
                'Office_365_E1_(no_Teams)': 'E1 (SIN TEAMS)',       
                'Microsoft_Teams_Enterprise_New': 'TEAMS ENTERPRISE',
                'PROJECTPROFESSIONAL': 'PROJECT',                   
                'POWER_BI_PRO': 'POWER BI',                         
                'VISIOCLIENT': 'VISIO PLAN 2',                      
                'EXCHANGESTANDARD': 'EXCHANGE ONLINE (PLAN 1)'      
            }

            # 4. Bloque Transaccional Atómico (Evita inconsistencias ante errores críticos)
            with transaction.atomic():
                for index, row in df.iterrows():
                    correo = str(row.get('Nombre principal de usuario', '')).strip().lower()
                    nombre = str(row.get('Nombre para mostrar', '')).strip()
                    tiene_lic = str(row.get('Tiene licencia', '')).strip().upper() == 'VERDADERO'
                    skus_str = str(row.get('AssignedProductSkus', '')).strip()

                    # Limpieza de registros inválidos
                    if pd.isna(correo) or not correo or '@' not in correo:
                        continue

                    # Resolución de dependencias corporativas
                    dominio = correo.split('@')[1]
                    nombre_empresa = mapa_dominios.get(dominio, 'MAMAYATECH')
                    empresa_obj = Empresa.objects.filter(nombre__icontains=nombre_empresa).first()
                    
                    if not empresa_obj: 
                        continue
                        
                    area_por_defecto = GerenciaArea.objects.filter(empresa=empresa_obj).first()

                    # Consolidación de Identidades Operativas
                    empleado, creado = Empleado.objects.get_or_create(
                        email_principal=correo,
                        defaults={
                            'nombre_completo': nombre,
                            'ci': correo.split('@')[0],
                            'empresa': empresa_obj,
                            'area': area_por_defecto,
                            'activo': tiene_lic
                        }
                    )

                    if creado: 
                        creados += 1
                    else:
                        if empleado.activo != tiene_lic:
                            empleado.activo = tiene_lic
                            empleado.save(update_fields=['activo'])
                        actualizados += 1

                    # Parseo estructural de SKUs compuestos
                    skus_lista = skus_str.split('+') if skus_str else []
                    skus_principales = []
                    skus_extra = [] 

                    for sku in skus_lista:
                        sku = sku.strip()
                        if sku in mapa_licencias:
                            skus_principales.append(sku)
                        elif sku:
                            skus_extra.append(sku)

                    nombres_licencias_excel = [mapa_licencias[s] for s in skus_principales]
                    nombres_manejados = list(mapa_licencias.values())

                    # Políticas de retención: Se revocan únicamente las licencias gestionadas en la conciliación actual
                    asignaciones_actuales = Asignacion.objects.filter(empleado=empleado, activo=True)
                    
                    for asig in asignaciones_actuales:
                        nombre_bd = asig.licencia.tipo.nombre.upper()
                        es_gestionada = any(nm.upper() in nombre_bd for nm in nombres_manejados)
                        
                        if es_gestionada:
                            viene_en_excel = any(nm.upper() in nombre_bd for nm in nombres_licencias_excel)
                            if not viene_en_excel or not tiene_lic:
                                asig.activo = False
                                asig.fecha_retiro = timezone.now()
                                asig.save()
                                liberadas += 1

                    # Aprovisionamiento dinámico de activos
                    texto_extra = f"Complementos M365: {', '.join(skus_extra)}" if skus_extra else ""

                    if tiene_lic:
                        for sku_principal in skus_principales:
                            nombre_lic_bd = mapa_licencias[sku_principal]
                            
                            tiene_esta_licencia = Asignacion.objects.filter(
                                empleado=empleado, 
                                licencia__tipo__nombre__icontains=nombre_lic_bd, 
                                activo=True
                            ).exists()

                            if not tiene_esta_licencia:
                                licencia_libre = Licencia.objects.filter(
                                    tipo__nombre__icontains=nombre_lic_bd,
                                    empresa=empresa_obj
                                ).exclude(asignaciones__activo=True).first()

                                if licencia_libre:
                                    Asignacion.objects.create(
                                        licencia=licencia_libre,
                                        empleado=empleado,
                                        observaciones=texto_extra
                                    )
                                    asignadas += 1
                                else:
                                    sin_stock += 1 
                            else:
                                # Sincronización de adiciones de bajo nivel (Add-ons)
                                asig_actual = Asignacion.objects.filter(
                                    empleado=empleado, 
                                    licencia__tipo__nombre__icontains=nombre_lic_bd, 
                                    activo=True
                                ).first()
                                if asig_actual and skus_extra:
                                    asig_actual.observaciones = texto_extra
                                    asig_actual.save(update_fields=['observaciones'])

            # ==========================================
            # DIAGNÓSTICO FINAL DE SINCRONIZACIÓN
            # ==========================================
            msg = f"Conciliación Finalizada: {creados} altas, {actualizados} validadas. {asignadas} asignaciones generadas, {liberadas} revocadas."
            if sin_stock > 0:
                msg += f" RIESGO DETECTADO: Déficit de inventario. Faltan {sin_stock} activos en pool corporativo."
                messages.warning(request, msg)
            else:
                messages.success(request, msg)
                
        except Exception as e:
            messages.error(request, f"Error crítico en Pipeline de Datos. Traceback: {str(e)}")

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
                messages.success(request, f"¡Limpieza completada! Se eliminaron {cantidad} licencias permanentemente.")
            else:
                messages.warning(request, "No se seleccionó ninguna licencia para borrar.")
                
        except Exception as e:
            messages.error(request, f"Ocurrió un error al intentar borrar las licencias: {str(e)}")

    return redirect('dashboard_general')