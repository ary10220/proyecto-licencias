from django import forms
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSION_GROUPS = [
    {
        'titulo': 'Inicio y Dashboard',
        'descripcion': 'Controla el acceso al dashboard y a la operacion diaria de licencias y asignaciones.',
        'menu_help': 'Para que se vea este modulo en el menu, marca al menos un permiso de visualizacion de licencias o asignaciones.',
        'permisos': [
            'licencias.view_licencia',
            'licencias.view_asignacion',
            'licencias.add_licencia',
            'licencias.change_licencia',
            'licencias.delete_licencia',
            'licencias.add_asignacion',
            'licencias.change_asignacion',
            'licencias.delete_asignacion',
        ],
    },
    {
        'titulo': 'Empleados',
        'descripcion': 'Controla el acceso al directorio de empleados y sus acciones operativas.',
        'menu_help': 'Para que se vea este modulo en el menu, marca Ver Empleado.',
        'permisos': [
            'empleados.view_empleado',
            'empleados.add_empleado',
            'empleados.change_empleado',
            'empleados.delete_empleado',
        ],
    },
    {
        'titulo': 'Parametrizacion Global',
        'descripcion': 'Agrupa la configuracion maestra del sistema: tenants, empresas, proveedores, tipos de licencia, divisiones, areas y unidades.',
        'menu_help': 'Para que se vea este modulo en el menu, marca al menos un permiso Ver dentro de este bloque.',
        'permisos': [
            'licencias.view_tenant',
            'licencias.view_empresa',
            'licencias.view_proveedor',
            'licencias.view_tipolicencia',
            'empleados.view_gerenciadivision',
            'empleados.view_gerenciaarea',
            'empleados.view_unidad',
            'licencias.add_tenant',
            'licencias.change_tenant',
            'licencias.delete_tenant',
            'licencias.add_empresa',
            'licencias.change_empresa',
            'licencias.delete_empresa',
            'licencias.add_proveedor',
            'licencias.change_proveedor',
            'licencias.delete_proveedor',
            'licencias.add_tipolicencia',
            'licencias.change_tipolicencia',
            'licencias.delete_tipolicencia',
            'empleados.add_gerenciadivision',
            'empleados.change_gerenciadivision',
            'empleados.delete_gerenciadivision',
            'empleados.add_gerenciaarea',
            'empleados.change_gerenciaarea',
            'empleados.delete_gerenciaarea',
            'empleados.add_unidad',
            'empleados.change_unidad',
            'empleados.delete_unidad',
        ],
    },
    {
        'titulo': 'Facturacion y Comercial',
        'descripcion': 'Controla cotizaciones, propuestas, facturas y emision de documentos comerciales (cotizaciones aprobadas, contratos, PDFs).',
        'menu_help': 'Para que se vea este modulo en el menu, marca al menos Ver Cotizacion o Ver Factura.',
        'permisos': [
            'facturacion.view_propuestalicencia',
            'facturacion.view_factura',
            'facturacion.add_propuestalicencia',
            'facturacion.change_propuestalicencia',
            'facturacion.delete_propuestalicencia',
            'facturacion.add_factura',
            'facturacion.change_factura',
            'facturacion.delete_factura',
            'facturacion.view_detallepropuesta',
            'facturacion.add_detallepropuesta',
            'facturacion.change_detallepropuesta',
            'facturacion.delete_detallepropuesta',
            'facturacion.view_detallefactura',
            'facturacion.add_detallefactura',
            'facturacion.change_detallefactura',
            'facturacion.delete_detallefactura',
        ],
    },
    {
        'titulo': 'Gestion Global',
        'descripcion': 'Controla la administracion centralizada de empresas, tenants y estructura organizacional desde el modulo Gestion Global (vista profesional con tabs).',
        'menu_help': 'Para que se vea este modulo en el menu, marca al menos un permiso Ver dentro de este bloque.',
        'permisos': [
            'licencias.view_tenant',
            'licencias.view_empresa',
            'empleados.view_gerenciadivision',
            'empleados.view_gerenciaarea',
            'empleados.view_unidad',
            'licencias.add_tenant',
            'licencias.change_tenant',
            'licencias.delete_tenant',
            'licencias.add_empresa',
            'licencias.change_empresa',
            'licencias.delete_empresa',
            'empleados.add_gerenciadivision',
            'empleados.change_gerenciadivision',
            'empleados.delete_gerenciadivision',
            'empleados.add_gerenciaarea',
            'empleados.change_gerenciaarea',
            'empleados.delete_gerenciaarea',
            'empleados.add_unidad',
            'empleados.change_unidad',
            'empleados.delete_unidad',
        ],
    },
    {
        'titulo': 'Bitacora',
        'descripcion': 'Permite revisar los eventos registrados por el sistema (auditoria de acciones).',
        'menu_help': 'Para que se vea este modulo en el menu, marca Ver Bitacora.',
        'permisos': [
            'bitacora.view_bitacora',
        ],
    },
    {
        'titulo': 'Usuarios y Accesos',
        'descripcion': 'Controla usuarios, roles, areas de usuario y cargos internos usados en la administracion del sistema.',
        'menu_help': 'Para que se vea este modulo en el menu, marca al menos uno de estos permisos: Ver Usuario, Ver Rol, Ver Area de usuario o Ver Cargo.',
        'permisos': [
            'auth.view_user',
            'auth.view_group',
            'user.view_areausuario',
            'empleados.view_cargo',
            'auth.add_user',
            'auth.change_user',
            'auth.delete_user',
            'auth.add_group',
            'auth.change_group',
            'auth.delete_group',
            'user.add_areausuario',
            'user.change_areausuario',
            'user.delete_areausuario',
            'empleados.add_cargo',
            'empleados.change_cargo',
            'empleados.delete_cargo',
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
