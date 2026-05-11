"""Formulario de Unidad (CU08)."""

from django import forms

from ...infrastructure.models import Unidad


class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['area', 'nombre']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select select2-busqueda'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la unidad'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get('area')
        nombre = (cleaned_data.get('nombre') or '').strip()
        if area and nombre:
            qs = Unidad.objects.filter(area=area, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe una unidad con este nombre dentro del area seleccionada.')
        return cleaned_data
