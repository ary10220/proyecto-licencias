"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from licencias import views

urlpatterns = [
    # Administración de Django
    path('admin/', admin.site.urls),

    # Autenticación y Sesiones
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Recuperación de contraseña
    path('reset_password/', auth_views.PasswordResetView.as_view(
    template_name="registration/password_reset_form.html",
    email_template_name="registration/password_reset_email.txt",      # Respaldo de texto
    html_email_template_name="registration/password_reset_email.html", # El diseño naranja
    subject_template_name="registration/password_reset_subject.txt"    # El asunto
    ), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),

    # Dashboard y Vistas Principales
    path('', views.inicio, name='home'),
    path('inicio/', views.inicio, name='inicio'),
    path('dashboard/', views.dashboard, name='dashboard_general'),
    path('dashboard/<int:tenant_id>/', views.dashboard, name='dashboard_tenant'),

    # Sincronización y Exportación de Datos
    path('sincronizar/', views.sincronizar_m365, name='sincronizar'),
    path('exportar/', views.exportar_excel, name='exportar_general'),
    path('exportar/<int:tenant_id>/', views.exportar_excel, name='exportar_tenant'),

    # Módulo de Licencias
    path('licencia/nueva/', views.crear_licencia, name='crear_licencia'),
    path('licencia/<int:licencia_id>/editar/', views.editar_licencia, name='editar_licencia'),
    path('licencia/<int:licencia_id>/eliminar/', views.eliminar_licencia, name='eliminar_licencia'),
    path('licencias/eliminar-masivo/', views.eliminar_licencias_masivo, name='eliminar_licencias_masivo'),
    path('licencia/<int:licencia_id>/asignar/', views.asignar_licencia, name='asignar_licencia'),
    path('licencia/<int:licencia_id>/liberar/', views.liberar_licencia, name='liberar_licencia'),
    # para token
    path('desbloqueo-seguro/', views.validar_token_bloqueo, name='validar_token_bloqueo'),

    # Módulo de Empleados
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleado/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleado/<int:empleado_id>/baja/', views.baja_empleado, name='baja_empleado'),
    path('empleado/<int:empleado_id>/reactivar/', views.reactivar_empleado, name='reactivar_empleado'),

    # Módulo de Organización (Estructura Jerárquica)
    path('organizacion/', views.organizacion, name='organizacion'),
    path('organizacion/division/<int:pk>/editar/', views.editar_division, name='editar_division'),
    path('organizacion/division/<int:pk>/eliminar/', views.eliminar_division, name='eliminar_division'),
    path('organizacion/area/<int:pk>/editar/', views.editar_area, name='editar_area'),
    path('organizacion/area/<int:pk>/eliminar/', views.eliminar_area, name='eliminar_area'),
    path('organizacion/unidad/<int:pk>/editar/', views.editar_unidad, name='editar_unidad'),
    path('organizacion/unidad/<int:pk>/eliminar/', views.eliminar_unidad, name='eliminar_unidad'),

    # Módulo de Configuración (Catálogos y Paramétricas)
    path('configuracion/', views.configuracion, name='configuracion'),
    path('configuracion/tenant/<int:pk>/editar/', views.editar_tenant, name='editar_tenant'),
    path('configuracion/tenant/<int:pk>/eliminar/', views.eliminar_tenant, name='eliminar_tenant'),
    path('configuracion/empresa/<int:pk>/editar/', views.editar_empresa, name='editar_empresa'),
    path('configuracion/empresa/<int:pk>/eliminar/', views.eliminar_empresa, name='eliminar_empresa'),
    path('configuracion/proveedor/<int:pk>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('configuracion/proveedor/<int:pk>/eliminar/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('configuracion/software/<int:pk>/editar/', views.editar_tipo_licencia, name='editar_tipo_licencia'),
    path('configuracion/software/<int:pk>/eliminar/', views.eliminar_tipo_licencia, name='eliminar_tipo_licencia'),
    
    path('bitacora/', include('bitacora.urls')),
    path('user/', include('user.urls')),

    # Endpoints de API / AJAX
    path('ajax/cargar-empresas/', views.cargar_empresas, name='ajax_cargar_empresas'),
    path('ajax/cargar-divisiones/', views.cargar_divisiones, name='ajax_cargar_divisiones'),
    path('ajax/cargar-areas/', views.cargar_areas, name='ajax_cargar_areas'),
    path('ajax/cargar-unidades/', views.cargar_unidades, name='ajax_cargar_unidades'),
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
