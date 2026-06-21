from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_descuentos_fechas_y_pago'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propuestalicencia',
            name='estado',
            field=models.CharField(
                choices=[
                    ('BORRADOR',  'Borrador'),
                    ('PENDIENTE', 'Pendiente'),
                    ('APROBADA',  'Aprobada'),
                    ('RECHAZADA', 'Rechazada'),
                    ('FACTURADA', 'Facturada'),
                    ('ANULADA',   'Anulada'),
                ],
                default='BORRADOR',
                max_length=15,
            ),
        ),
    ]
