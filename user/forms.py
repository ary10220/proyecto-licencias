from django import forms
from django.contrib.auth.models import User, Group, Permission
from empleados.models import Cargo
from .models import AREAS_USUARIO, PerfilUsuario


ROLE_PERMISSION_GROUPS = [
    {
        'titulo': 'Dashboard y Licencias',
        'descripcion': 'Permite ver el tablero, crear activos, editar licencias y gestionar asignaciones.',
        'permisos': [
            'licencias.view_licencia',
            'licencias.add_licencia',
            'licencias.change_licencia',
            'licencias.delete_licencia',
            'licencias.view_asignacion',
            'licencias.add_asignacion',
            'licencias.change_asignacion',
            'licencias.delete_asignacion',
        ],
    },
    {
        'titulo': 'Empleados',
        'descripcion': 'Controla el acceso al directorio de empleados y sus acciones operativas.',
        'permisos': [
            'empleados.view_empleado',
            'empleados.add_empleado',
            'empleados.change_empleado',
            'empleados.delete_empleado',
        ],
    },
    {
        'titulo': 'Áreas y Organización',
        'descripcion': 'Permite ver y administrar divisiones, áreas, unidades y cargos.',
        'permisos': [
            'empleados.view_gerenciadivision',
            'empleados.add_gerenciadivision',
            'empleados.change_gerenciadivision',
            'empleados.delete_gerenciadivision',
            'empleados.view_gerenciaarea',
            'empleados.add_gerenciaarea',
            'empleados.change_gerenciaarea',
            'empleados.delete_gerenciaarea',
            'empleados.view_unidad',
            'empleados.add_unidad',
            'empleados.change_unidad',
            'empleados.delete_unidad',
            'empleados.view_cargo',
            'empleados.add_cargo',
            'empleados.change_cargo',
            'empleados.delete_cargo',
        ],
    },
    {
        'titulo': 'Configuración',
        'descripcion': 'Controla empresas, tenants, proveedores y tipos de licencia.',
        'permisos': [
            'licencias.view_tenant',
            'licencias.add_tenant',
            'licencias.change_tenant',
            'licencias.delete_tenant',
            'licencias.view_empresa',
            'licencias.add_empresa',
            'licencias.change_empresa',
            'licencias.delete_empresa',
            'licencias.view_proveedor',
            'licencias.add_proveedor',
            'licencias.change_proveedor',
            'licencias.delete_proveedor',
            'licencias.view_tipolicencia',
            'licencias.add_tipolicencia',
            'licencias.change_tipolicencia',
            'licencias.delete_tipolicencia',
        ],
    },
    {
        'titulo': 'Bitácora',
        'descripcion': 'Permite revisar los eventos registrados por el sistema.',
        'permisos': [
            'bitacora.view_bitacora',
        ],
    },
    {
        'titulo': 'Usuarios y Roles',
        'descripcion': 'Permite consultar o administrar usuarios y roles del sistema.',
        'permisos': [
            'auth.view_user',
            'auth.add_user',
            'auth.change_user',
            'auth.delete_user',
            'auth.view_group',
            'auth.add_group',
            'auth.change_group',
            'auth.delete_group',
        ],
    },
]


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        label="Permisos del rol",
        queryset=Permission.objects.select_related('content_type').all().order_by(
            'content_type__app_label',
            'content_type__model',
            'codename'
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nombre del rol',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Auditor, Operador, Supervisor'}),
        }


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nombre', 'descripcion', 'activo']
        labels = {
            'nombre': 'Nombre del cargo',
            'descripcion': 'Descripción',
            'activo': 'Activo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Analista de Sistemas'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserForm(forms.ModelForm):
    area = forms.ChoiceField(
        label="Área",
        choices=[('', 'Sin área asignada'), *AREAS_USUARIO],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cargo = forms.ModelChoiceField(
        label="Cargo",
        queryset=Cargo.objects.filter(activo=True).order_by('nombre'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para conservar la actual',
            'autocomplete': 'new-password',
        }),
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        label="Roles / Grupos",
        queryset=Group.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'is_active', 'is_staff', 'is_superuser', 'groups'
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
        if self.instance.pk:
            perfil = getattr(self.instance, 'perfil', None)
            if perfil:
                self.fields['area'].initial = perfil.area
                self.fields['cargo'].initial = perfil.cargo
        else:
            self.fields['password'].widget.attrs['placeholder'] = 'Contraseña inicial del usuario'

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.pk and self.current_user and self.instance.pk == self.current_user.pk:
            if not cleaned_data.get('is_active'):
                self.add_error('is_active', 'No puedes desactivar tu propio usuario.')
            if not cleaned_data.get('is_staff'):
                self.add_error('is_staff', 'No puedes quitarte el acceso al admin desde tu propia cuenta.')
            if not cleaned_data.get('is_superuser'):
                self.add_error('is_superuser', 'No puedes quitarte el rol de superusuario desde tu propia cuenta.')

        if not self.instance.pk and not cleaned_data.get('password'):
            self.add_error('password', 'La contraseña es obligatoria al crear un usuario.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
            self.password_changed = True

        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get('groups', []))
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.area = self.cleaned_data.get('area')
            perfil.cargo = self.cleaned_data.get('cargo')
            perfil.save()

        return user
