from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
    ]

    operations = [
        # ============ PropuestaLicencia ============
        migrations.AlterField(
            model_name='propuestalicencia',
            name='numero',
            field=models.CharField(blank=True, max_length=30, unique=True, verbose_name='Numero de propuesta'),
        ),
        migrations.AddField(
            model_name='propuestalicencia',
            name='descuento_porcentaje',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Descuento global en porcentaje aplicado al total de la cotizacion.', max_digits=5),
        ),
        migrations.AddField(
            model_name='propuestalicencia',
            name='descuento_monto',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Descuento global en monto fijo (se aplica DESPUES del descuento porcentual).', max_digits=12),
        ),
        migrations.AddField(
            model_name='propuestalicencia',
            name='impuesto_porcentaje',
            field=models.DecimalField(decimal_places=2, default=13, help_text='IVA o impuesto general aplicado al subtotal con descuentos. Default 13%.', max_digits=5),
        ),

        # ============ DetallePropuesta ============
        migrations.AddField(
            model_name='detallepropuesta',
            name='fecha_inicio_uso',
            field=models.DateField(blank=True, null=True, help_text='Inicio del periodo de uso/vigencia de la licencia.'),
        ),
        migrations.AddField(
            model_name='detallepropuesta',
            name='fecha_fin_uso',
            field=models.DateField(blank=True, null=True, help_text='Fin del periodo de uso/vigencia de la licencia.'),
        ),
        migrations.AddField(
            model_name='detallepropuesta',
            name='descuento_porcentaje',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Descuento porcentual aplicado a esta linea.', max_digits=5),
        ),
        migrations.AddField(
            model_name='detallepropuesta',
            name='descuento_monto',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Descuento fijo aplicado a esta linea (despues del porcentaje).', max_digits=12),
        ),
        migrations.AddField(
            model_name='detallepropuesta',
            name='observaciones',
            field=models.CharField(blank=True, max_length=200),
        ),

        # ============ Factura ============
        migrations.AlterField(
            model_name='factura',
            name='numero',
            field=models.CharField(blank=True, max_length=30, unique=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='direccion_fiscal',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='factura',
            name='metodo_pago',
            field=models.CharField(
                choices=[
                    ('CONTADO', 'Contado'),
                    ('CREDITO', 'Credito'),
                    ('TRANSFERENCIA', 'Transferencia'),
                    ('CHEQUE', 'Cheque'),
                    ('TARJETA', 'Tarjeta'),
                    ('OTRO', 'Otro'),
                ],
                default='CONTADO',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='factura',
            name='descuento_porcentaje',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='factura',
            name='descuento_monto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='factura',
            name='impuesto_porcentaje',
            field=models.DecimalField(decimal_places=2, default=13, max_digits=5),
        ),

        # ============ DetalleFactura ============
        migrations.AddField(
            model_name='detallefactura',
            name='fecha_inicio_uso',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='fecha_fin_uso',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='descuento_porcentaje',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='descuento_monto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='detallefactura',
            name='observaciones',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
