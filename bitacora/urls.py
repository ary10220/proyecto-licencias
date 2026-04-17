from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_bitacora, name='lista_bitacora'),
]