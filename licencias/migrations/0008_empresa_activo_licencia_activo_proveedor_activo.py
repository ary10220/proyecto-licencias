# Migracion historica de compatibilidad.
#
# Esta rama antigua agregaba campos `activo` que ya quedaron cubiertos por
# 0008_empresa_activo_tenant_activo y 0009_tipolicencia_campos_comerciales.
# Mantenerla como no-op evita que Django intente crear columnas duplicadas en
# bases existentes, pero conserva el nombre para instalaciones que la vean en
# el grafo de migraciones.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licencias', '0009_tipolicencia_campos_comerciales'),
    ]

    operations = []
