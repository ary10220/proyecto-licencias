from django import forms
from django.contrib.auth.models import Group, Permission


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
            'user.view_areausuario',
            'user.add_areausuario',
            'user.change_areausuario',
            'user.delete_areausuario',
        ],
    },
]


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        label="Permisos del rol",
        queryset=Permission.objects.select_related('content_type').all().order_by(
            'content_type__app_label',
            'content_type__model',
            'codename',
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        labels = {
            'name': 'Nombre del rol',
        }
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej: Auditor, Operador, Supervisor'}
            ),
        }
