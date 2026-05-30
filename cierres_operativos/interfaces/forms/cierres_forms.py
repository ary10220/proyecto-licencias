from django import forms
from cierres_operativos.models import PropuestaComercial
from empleados.models import Empleado

class GenerarNotaAlquilerForm(forms.Form):
    nro_nota = forms.CharField(
        max_length=50, 
        label="Número de Nota", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: NA-2026-001'})
    )
    fecha_vencimiento_pago = forms.DateField(
        label="Fecha de Vencimiento de Pago",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    # Lista de empleados activos para seleccionar a quién notificar en el DetalleNotifi
    empleados_notificar = forms.ModelMultipleChoiceField(
        queryset=Empleado.objects.filter(activo=True),
        label="Empleados a Notificar",
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Mantén presionado Ctrl para seleccionar varios."
    )