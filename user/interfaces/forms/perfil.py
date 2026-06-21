from django import forms

from ...models import PerfilUsuario


class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['foto']
        labels = {
            'foto': 'Foto de perfil',
        }
        widgets = {
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

