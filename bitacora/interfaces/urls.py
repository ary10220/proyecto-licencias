from django.urls import path

from .views.bitacora import lista_bitacora

urlpatterns = [
    path("", lista_bitacora, name="lista_bitacora"),
]

