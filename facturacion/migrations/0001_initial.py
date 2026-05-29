# Generated manually after moving commercial models out of licencias.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('licencias', '0008_empresa_activo_tenant_activo'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropuestaLicencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=30, unique=True, verbose_name='Numero de propuesta')),
                ('fecha', models.DateField(default=django.utils.timezone.now)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('APROBADA', 'Aprobada'), ('RECHAZADA', 'Rechazada'), ('FACTURADA', 'Facturada')], default='PENDIENTE', max_length=15)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='propuestas_comerciales', to='licencias.empresa')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='licencias.tenant')),
            ],
            options={
                'verbose_name': 'Propuesta comercial',
                'verbose_name_plural': 'Propuestas comerciales',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.CreateModel(
            name='DetallePropuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('precio_unitario', models.DecimalField(decimal_places=2, default=0, help_text='Precio ofertado en la propuesta', max_digits=12)),
                ('propuesta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='facturacion.propuestalicencia')),
                ('tipo_licencia', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licencias.tipolicencia')),
            ],
            options={
                'verbose_name': 'Detalle de propuesta',
                'verbose_name_plural': 'Detalles de propuesta',
            },
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=30, unique=True)),
                ('fecha', models.DateField(default=django.utils.timezone.now)),
                ('razon_social', models.CharField(blank=True, max_length=160)),
                ('nit', models.CharField(blank=True, max_length=40)),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('EMITIDA', 'Emitida'), ('PAGADA', 'Pagada'), ('ANULADA', 'Anulada')], default='EMITIDA', max_length=15)),
                ('stock_generado', models.BooleanField(default=False)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturas_comerciales', to='licencias.empresa')),
                ('propuesta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='facturas', to='facturacion.propuestalicencia')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturas_compra', to='licencias.proveedor')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='licencias.tenant')),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.CreateModel(
            name='DetalleFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('precio_unitario', models.DecimalField(decimal_places=2, default=0, help_text='Precio por unidad de licencia', max_digits=12)),
                ('fecha_vencimiento', models.DateField()),
                ('factura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='facturacion.factura')),
                ('tipo_licencia', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='licencias.tipolicencia')),
            ],
            options={
                'verbose_name': 'Detalle de factura',
                'verbose_name_plural': 'Detalles de factura',
            },
        ),
    ]

