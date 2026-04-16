from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('toggle/<int:user_id>/', views.toggle_usuario, name='toggle_usuario'),
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/detalle/<int:group_id>/', views.detalle_rol, name='detalle_rol'),
    path('roles/editar/<int:group_id>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:group_id>/', views.eliminar_rol, name='eliminar_rol'),
    path('cargos/', views.lista_cargos, name='lista_cargos'),
    path('cargos/crear/', views.crear_cargo, name='crear_cargo'),
    path('cargos/editar/<int:cargo_id>/', views.editar_cargo, name='editar_cargo'),
    path('cargos/eliminar/<int:cargo_id>/', views.eliminar_cargo, name='eliminar_cargo'),
]
