"""
Agrega campos opcionales de precio a la instancia Licencia.

Hasta ahora los precios vivian solo en `TipoLicencia` (catalogo).
Esta migracion permite registrar el costo real de cada compra puntual
sin tocar el catalogo, manteniendo compatibilidad: si los campos quedan
en NULL, el sistema sigue usando los precios del catalogo (ver
properties `precio_unitario_efectivo` y `precio_venta_efectivo`).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licencias', '0010_inventario_trazabilidad'),
    ]

    operations = [
        migrations.AddField(
            model_name='licencia',
            name='precio_unitario',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Precio al que se compro esta licencia. Si se deja vacio, usa el del catalogo.',
                max_digits=12,
                null=True,
                verbose_name='Precio unitario (compra)',
            ),
        ),
        migrations.AddField(
            model_name='licencia',
            name='precio_venta',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Precio sugerido para venta. Si se deja vacio, usa el del catalogo.',
                max_digits=12,
                null=True,
                verbose_name='Precio de venta',
            ),
        ),
    ]
