from django import forms

from empleados.models import Cargo

from ...models import AreaUsuario


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['area_usuario', 'nombre', 'descripcion', 'activo']
        labels = {
            'area_usuario': 'Área',
            'nombre': 'Nombre del cargo',
            'descripcion': 'Descripción',
            'activo': 'Activo',
        }
        widgets = {
            'area_usuario': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Analista'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area_usuario'].queryset = AreaUsuario.objects.filter(activo=True).order_by('nombre')
