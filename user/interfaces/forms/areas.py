from django import forms

from ...models import AreaUsuario


class AreaUsuarioForm(forms.ModelForm):
    cargos_iniciales = forms.CharField(
        label="Cargos del área",
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ej:\nAdministrador de Sistemas\nAnalista de Soporte\nAuditor Interno',
            }
        ),
        help_text="Opcional. Escribe un cargo por línea para crearlos como dependencias de esta área.",
    )

    class Meta:
        model = AreaUsuario
        fields = ['nombre', 'descripcion', 'activo']
        labels = {
            'nombre': 'Nombre del área',
            'descripcion': 'Descripción',
            'activo': 'Activa',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Operaciones'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
