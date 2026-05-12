"""Formulario de Unidad (CU08)."""

from django import forms
from django.db.models import Q

from ...infrastructure.models import GerenciaArea, Unidad


class UnidadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        area_qs = GerenciaArea.objects.filter(activo=True)
        if self.instance.pk and self.instance.area_id:
            area_qs = GerenciaArea.objects.filter(Q(activo=True) | Q(pk=self.instance.area_id))
        self.fields['area'].queryset = area_qs.select_related('empresa').order_by('empresa__nombre', 'nombre')

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
        if area and not area.activo:
            self.add_error('area', 'No se puede asociar una unidad a un area inactiva.')
        if area and nombre:
            qs = Unidad.objects.filter(area=area, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('nombre', 'Ya existe una unidad con este nombre dentro del area seleccionada.')
        return cleaned_data
