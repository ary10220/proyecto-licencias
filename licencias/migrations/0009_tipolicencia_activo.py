# Migracion historica de compatibilidad.
#
# El campo TipoLicencia.activo ya lo agrega 0009_tipolicencia_campos_comerciales.
# Esta migracion queda sin operaciones para no duplicar columnas.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licencias', '0008_empresa_activo_licencia_activo_proveedor_activo'),
    ]

    operations = []
