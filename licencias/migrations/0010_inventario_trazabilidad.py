from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0003_estados_borrador_anulada'),
        ('licencias', '0009_tipolicencia_campos_comerciales'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipolicencia',
            name='duracion_dias',
            field=models.PositiveIntegerField(default=365, help_text='Duracion sugerida de la licencia en dias.'),
        ),
        migrations.AddField(
            model_name='licencia',
            name='estado_operativo',
            field=models.CharField(
                choices=[
                    ('DISPONIBLE', 'Disponible'),
                    ('ASIGNADA', 'Asignada'),
                    ('VENCIDA', 'Vencida'),
                    ('SUSPENDIDA', 'Suspendida'),
                    ('PENDIENTE_ACTIVACION', 'Pendiente de activacion'),
                    ('REVOCADA', 'Revocada'),
                ],
                db_index=True,
                default='DISPONIBLE',
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name='licencia',
            name='origen',
            field=models.CharField(
                choices=[
                    ('MANUAL', 'Registro manual'),
                    ('FACTURA', 'Facturacion'),
                    ('SYNC', 'Sincronizacion'),
                ],
                db_index=True,
                default='MANUAL',
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name='licencia',
            name='factura_origen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='licencias_generadas',
                to='facturacion.factura',
            ),
        ),
        migrations.AddField(
            model_name='licencia',
            name='detalle_factura_origen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='licencias_generadas',
                to='facturacion.detallefactura',
            ),
        ),
        migrations.AddField(
            model_name='licencia',
            name='fecha_inicio',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='licencia',
            name='observaciones',
            field=models.TextField(blank=True),
        ),
    ]
