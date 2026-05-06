from django import forms
from django.contrib.auth.models import Group, User

from empleados.models import Cargo

from ...models import AreaUsuario, PerfilUsuario


class UserForm(forms.ModelForm):
    area_usuario = forms.ModelChoiceField(
        label="Área",
        queryset=AreaUsuario.objects.filter(activo=True).order_by('nombre'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cargo = forms.ModelChoiceField(
        label="Cargo",
        queryset=Cargo.objects.filter(activo=True).select_related('area_usuario').order_by('area_usuario__nombre', 'nombre'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    groups = forms.ModelMultipleChoiceField(
        label='Roles / Grupos',
        queryset=Group.objects.order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        ]
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'is_active': 'Activo',
            'is_staff': 'Acceso al admin',
            'is_superuser': 'Superusuario',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: jperez', 'autocomplete': 'off'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Perez', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'usuario@dominio.com', 'autocomplete': 'off'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        self.password_changed = False
        super().__init__(*args, **kwargs)

        self.fields['groups'].queryset = Group.objects.order_by('name')

        self.fields['username'].required = True
        self.fields['email'].required = True
        self.fields['email'].help_text = 'Obligatorio. Se usa para restablecer contraseña y notificaciones.'

        self.fields['area_usuario'].queryset = AreaUsuario.objects.filter(activo=True).order_by('nombre')
        self.fields['cargo'].queryset = Cargo.objects.filter(activo=True).select_related('area_usuario').order_by(
            'area_usuario__nombre',
            'nombre',
        )

        if self.instance.pk:
            perfil = getattr(self.instance, 'perfil', None)
            if perfil:
                self.fields['area_usuario'].initial = perfil.area_usuario
                self.fields['cargo'].initial = perfil.cargo

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise forms.ValidationError('El correo electrónico es obligatorio.')

        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')

        return email

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError('El usuario es obligatorio.')
        return username

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.pk and self.current_user and self.instance.pk == self.current_user.pk:
            if not cleaned_data.get('is_active'):
                self.add_error('is_active', 'No puedes desactivar tu propio usuario.')
            if not cleaned_data.get('is_staff'):
                self.add_error('is_staff', 'No puedes quitarte el acceso al admin desde tu propia cuenta.')
            if not cleaned_data.get('is_superuser'):
                self.add_error('is_superuser', 'No puedes quitarte el rol de superusuario desde tu propia cuenta.')

        area_usuario = cleaned_data.get('area_usuario')
        cargo = cleaned_data.get('cargo')
        if area_usuario and cargo and cargo.area_usuario and cargo.area_usuario != area_usuario:
            self.add_error('cargo', 'El cargo seleccionado no pertenece al área indicada.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        creating = user.pk is None
        if creating:
            user.set_password(user.username)

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('groups', []))
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.area_usuario = self.cleaned_data.get('area_usuario')
            perfil.area = ''
            perfil.cargo = self.cleaned_data.get('cargo')
            if creating:
                perfil.must_change_password = True
            perfil.save()

        return user
