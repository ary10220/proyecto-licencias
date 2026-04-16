from django.db import migrations


DEFAULT_AREAS = {
    'administracion': 'Administracion',
    'soporte': 'Soporte',
    'operaciones': 'Operaciones',
    'auditoria': 'Auditoria',
    'sistemas': 'Sistemas',
    'cliente': 'Cliente',
}


def seed_areas(apps, schema_editor):
    AreaUsuario = apps.get_model('user', 'AreaUsuario')
    PerfilUsuario = apps.get_model('user', 'PerfilUsuario')

    areas = {}
    for clave, nombre in DEFAULT_AREAS.items():
        area, _ = AreaUsuario.objects.get_or_create(
            nombre=nombre,
            defaults={'activo': True}
        )
        areas[clave] = area

    for perfil in PerfilUsuario.objects.filter(area_usuario__isnull=True).exclude(area__isnull=True).exclude(area=''):
        area = areas.get(perfil.area)
        if area:
            perfil.area_usuario = area
            perfil.save(update_fields=['area_usuario'])


def unseed_areas(apps, schema_editor):
    AreaUsuario = apps.get_model('user', 'AreaUsuario')
    AreaUsuario.objects.filter(nombre__in=DEFAULT_AREAS.values(), cargos__isnull=True, perfiles__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_areausuario_perfilusuario_area_usuario'),
    ]

    operations = [
        migrations.RunPython(seed_areas, unseed_areas),
    ]
