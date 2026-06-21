from django.urls import path

from . import views

app_name = 'asistente'

urlpatterns = [
    path('chat/', views.asistente_chat, name='chat'),
    path('ayuda/', views.asistente_ayuda, name='ayuda'),
    path('filtros/', views.asistente_filtros, name='filtros'),
]
