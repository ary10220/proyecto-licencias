from django.urls import path
from .views import GenerarNotaAlquilerView

app_name = 'cierres_operativos'

urlpatterns = [
    path('propuesta/<int:propuesta_id>/generar-nota/', GenerarNotaAlquilerView.as_view(), name='generar_nota_alquiler'),
]