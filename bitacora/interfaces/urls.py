from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_bitacora, name="lista_bitacora"),
    path("evento/<int:evento_id>/", views.detalle_evento, name="detalle_bitacora"),
    path("api/opciones-filtros/", views.opciones_filtros, name="bitacora_opciones_filtros"),
]
