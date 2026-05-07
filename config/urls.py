"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
    # Administracion de Django
    path('admin/', admin.site.urls),

    # Autenticacion y Sesiones
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

    # Vista custom: limpia el lockout de Axes despues de restablecer la
    # contrasena. Si no, el usuario queda atrapado en /desbloqueo-seguro/
    # tras cambiar su password porque Axes aun lo ve como bloqueado.
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

    # Dashboard y Vistas Principales
    path('', views.inicio, name='home'),
    path('inicio/', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard_general'),
    path('dashboard/<int:tenant_id>/', views.dashboard, name='dashboard_tenant'),

    # Sincronizacion y Exportacion de Datos
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

    # Token de desbloqueo
    path('desbloqueo-seguro/', views.validar_token_bloqueo, name='validar_token_bloqueo'),
    path('solicitar-token/', views.enviar_token_bloqueo, name='enviar_token_bloqueo'),

    # Modulo de Empleados
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleado/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleado/<int:empleado_id>/baja/', views.baja_empleado, name='baja_empleado'),
    path('empleado/<int:empleado_id>/reactivar/', views.reactivar_empleado, name='reactivar_empleado'),

    # ==========================================
    # Modulo de Configuracion (Catalogos y Parametricas)
    # ==========================================
    path('configuracion/', views.configuracion, name='configuracion'),

    # -- Tenants, Empresas, Proveedores y Licencias --
    path('configuracion/tenant/<int:pk>/editar/', views.editar_tenant, name='editar_tenant'),
    path('configuracion/tenant/<int:pk>/eliminar/', views.eliminar_tenant, name='eliminar_tenant'),
    path('configuracion/empresa/<int:pk>/editar/', views.editar_empresa, name='editar_empresa'),
    path('configuracion/empresa/<int:pk>/eliminar/', views.eliminar_empresa, name='eliminar_empresa'),
    path('configuracion/proveedor/<int:pk>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('configuracion/proveedor/<int:pk>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('configuracion/software/<int:pk>/editar/', views.editar_tipo_licencia, name='editar_tipo_licencia'),
    path('configuracion/software/<int:pk>/eliminar/', views.eliminar_tipo_licencia, name='eliminar_tipo_licencia'),

    # -- Divisiones, Areas y Unidades --
    path('configuracion/division/<int:pk>/editar/', views.editar_division, name='editar_division'),
    path('configuracion/division/<int:pk>/eliminar/', views.eliminar_division, name='eliminar_division'),
    path('configuracion/area/<int:pk>/editar/', views.editar_area, name='editar_area'),
    path('configuracion/area/<int:pk>/eliminar/', views.eliminar_area, name='eliminar_area'),
    path('configuracion/unidad/<int:pk>/editar/', views.editar_unidad, name='editar_unidad'),
    path('configuracion/unidad/<int:pk>/eliminar/', views.eliminar_unidad, name='eliminar_unidad'),

    # Apps modulares
    path('bitacora/', include('bitacora.interfaces.urls')),
    path('user/', include('user.interfaces.urls')),

    # Endpoints de API / AJAX
    path('ajax/cargar-empresas/', views.cargar_empresas, name='ajax_cargar_empresas'),
    path('ajax/cargar-divisiones/', views.cargar_divisiones, name='ajax_cargar_divisiones'),
    path('ajax/cargar-areas/', views.cargar_areas, name='ajax_cargar_areas'),
    path('ajax/cargar-unidades/', views.cargar_unidades, name='ajax_cargar_unidades'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = custom_permission_denied
