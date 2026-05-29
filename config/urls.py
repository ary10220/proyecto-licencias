"""
URL configuration for config project.

Despues de la migracion a `gestion_global`:
  - /configuracion/ y todas sus subrutas migradas se REMOVIERON.
  - /gestion-global/<feature>/ es la nueva entrada (CU07/08/10/11/12).
  - Proveedor y TipoLicencia se quedan en `licencias/` (no son CU del CICLO 2).
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from licencias import views
from licencias.auth_views import AxesAwarePasswordResetConfirmView
from user.interfaces.views.password import ForcedPasswordChangeView
from config.error_handlers import custom_permission_denied


urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticacion
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Recuperacion de contrasena
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
    ), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html"
    ), name="password_reset_done"),
    path('reset/<uidb64>/<token>/',
         AxesAwarePasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html"
    ), name="password_reset_complete"),
    path('password_change/', ForcedPasswordChangeView.as_view(), name="password_change"),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html"
    ), name="password_change_done"),

    # Dashboard
    path('', views.inicio, name='home'),
    path('inicio/', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard_general'),
    path('dashboard/<int:tenant_id>/', views.dashboard, name='dashboard_tenant'),
    path('licencias/', views.gestionar_licencias, name='gestionar_licencias'),
    path('licencias/tenant/<int:tenant_id>/', views.gestionar_licencias, name='gestionar_licencias_tenant'),

    # Sincronizacion / Reportes
    path('sincronizar/', views.sincronizar_m365, name='sincronizar'),
    path('exportar/', views.exportar_excel, name='exportar_general'),
    path('exportar/<int:tenant_id>/', views.exportar_excel, name='exportar_tenant'),

    # Modulo de Licencias
    path('licencia/nueva/', views.crear_licencia, name='crear_licencia'),
    path('licencia/<int:licencia_id>/editar/', views.editar_licencia, name='editar_licencia'),
    path('licencia/<int:licencia_id>/eliminar/', views.eliminar_licencia, name='eliminar_licencia'),
    path('licencias/eliminar-masivo/', views.eliminar_licencias_masivo, name='eliminar_licencias_masivo'),
    path('licencia/<int:licencia_id>/asignar/', views.asignar_licencia, name='asignar_licencia'),
    path('licencia/<int:licencia_id>/liberar/', views.liberar_licencia, name='liberar_licencia'),
    path('licencias/asignaciones/', views.asignaciones_licencias, name='asignaciones_licencias'),
    path('licencias/asignaciones/masivo/', views.asignar_licencias_masivo, name='asignar_licencias_masivo'),
    path('licencias/asignaciones/<int:asignacion_id>/liberar/', views.liberar_asignacion, name='liberar_asignacion'),
    path('licencias/asignaciones/<int:asignacion_id>/eliminar/', views.eliminar_asignacion, name='eliminar_asignacion'),

    # Token de desbloqueo
    path('desbloqueo-seguro/', views.validar_token_bloqueo, name='validar_token_bloqueo'),
    path('solicitar-token/', views.enviar_token_bloqueo, name='enviar_token_bloqueo'),

    # Modulo de Empleados (CU09 -- futura migracion separada)
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleado/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleado/<int:empleado_id>/baja/', views.baja_empleado, name='baja_empleado'),
    path('empleado/<int:empleado_id>/reactivar/', views.reactivar_empleado, name='reactivar_empleado'),

    # Catalogo de licenciamiento (Proveedor + TipoLicencia siguen en licencias/)
    path('catalogo-licencias/', views.catalogo_licencias, name='catalogo_licencias'),
    path('licencias/asignaciones/nueva/', views.nueva_asignacion, name='nueva_asignacion'),
    path('licencias/ajax/licencias-disponibles/', views.ajax_licencias_disponibles, name='ajax_licencias_disponibles'),
    path('licencias/ajax/empleados-empresa/',    views.ajax_empleados_empresa,    name='ajax_empleados_empresa'),
    path('licencias/panel/',        views.licencias_dashboard,    name='licencias_dashboard'),
    path('catalogo-licencias/proveedor/<int:pk>/editar/',
         views.editar_proveedor, name='editar_proveedor'),
    path('catalogo-licencias/proveedor/<int:pk>/eliminar/',
         views.eliminar_proveedor, name='eliminar_proveedor'),
    path('catalogo-licencias/software/<int:pk>/editar/',
         views.editar_tipo_licencia, name='editar_tipo_licencia'),
    path('catalogo-licencias/software/<int:pk>/eliminar/',
         views.eliminar_tipo_licencia, name='eliminar_tipo_licencia'),
    
    # Modulo comercial: cotizaciones / propuestas / facturacion
    path('facturacion/', include('facturacion.interfaces.urls')),

    # ============================================================
    # GESTION GLOBAL (CU07/08/10/11/12) -- nuevo modulo
    # ============================================================
    path('gestion-global/', include('gestion_global.interfaces.urls', namespace='gestion_global')),

    # Apps modulares
    path('bitacora/', include('bitacora.interfaces.urls')),
    path('user/', include('user.interfaces.urls')),

    # Endpoints AJAX (cascada Tenant -> Empresa -> Division -> Area -> Unidad)
    path('ajax/cargar-empresas/', views.cargar_empresas, name='ajax_cargar_empresas'),
    path('ajax/cargar-empleados/', views.cargar_empleados, name='ajax_cargar_empleados'),
    path('ajax/cargar-divisiones/', views.cargar_divisiones, name='ajax_cargar_divisiones'),
    path('ajax/cargar-areas/', views.cargar_areas, name='ajax_cargar_areas'),
    path('ajax/cargar-unidades/', views.cargar_unidades, name='ajax_cargar_unidades'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = custom_permission_denied
