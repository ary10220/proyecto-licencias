"""
URLs del modulo `gestion_global`. Namespace: 'gestion_global'.

Rutas por feature (CRUD): lista, crear, editar, eliminar.
"""

from django.urls import path
from . import views

app_name = 'gestion_global'

urlpatterns = [
    # Default: redirige a empresas (entrada del modulo)
    path('', views.lista_empresas, name='index'),

    # CU07 - Empresas
    path('empresas/',                      views.lista_empresas,    name='lista_empresas'),
    path('empresas/crear/',                views.crear_empresa,     name='crear_empresa'),
    path('empresas/editar/<int:pk>/',      views.editar_empresa,    name='editar_empresa'),
    path('empresas/eliminar/<int:pk>/',    views.eliminar_empresa,  name='eliminar_empresa'),
    path('empresas/reactivar/<int:pk>/',   views.reactivar_empresa, name='reactivar_empresa'),

    # CU12 - Tenants
    path('tenants/',                       views.lista_tenants,     name='lista_tenants'),
    path('tenants/crear/',                 views.crear_tenant,      name='crear_tenant'),
    path('tenants/editar/<int:pk>/',       views.editar_tenant,     name='editar_tenant'),
    path('tenants/eliminar/<int:pk>/',     views.eliminar_tenant,   name='eliminar_tenant'),
    path('tenants/reactivar/<int:pk>/',    views.reactivar_tenant,  name='reactivar_tenant'),

    # CU10 - Areas
    path('areas/',                         views.lista_areas,       name='lista_areas'),
    path('areas/crear/',                   views.crear_area,        name='crear_area'),
    path('areas/editar/<int:pk>/',         views.editar_area,       name='editar_area'),
    path('areas/eliminar/<int:pk>/',       views.eliminar_area,     name='eliminar_area'),
    path('areas/reactivar/<int:pk>/',      views.reactivar_area,    name='reactivar_area'),

    # CU11 - Divisiones
    path('divisiones/',                    views.lista_divisiones,  name='lista_divisiones'),
    path('divisiones/crear/',              views.crear_division,    name='crear_division'),
    path('divisiones/editar/<int:pk>/',    views.editar_division,   name='editar_division'),
    path('divisiones/eliminar/<int:pk>/',  views.eliminar_division, name='eliminar_division'),
    path('divisiones/reactivar/<int:pk>/', views.reactivar_division,name='reactivar_division'),

    # CU08 - Unidades
    path('unidades/',                      views.lista_unidades,    name='lista_unidades'),
    path('unidades/crear/',                views.crear_unidad,      name='crear_unidad'),
    path('unidades/editar/<int:pk>/',      views.editar_unidad,     name='editar_unidad'),
    path('unidades/eliminar/<int:pk>/',    views.eliminar_unidad,   name='eliminar_unidad'),
    path('unidades/reactivar/<int:pk>/',   views.reactivar_unidad,  name='reactivar_unidad'),
]
