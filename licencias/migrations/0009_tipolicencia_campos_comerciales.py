from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('licencias', '0008_empresa_activo_tenant_activo'),
    ]

    operations = [
        # === Proveedor: campos comerciales completos ===
        migrations.AddField(
            model_name='proveedor',
            name='razon_social',
            field=models.CharField(blank=True, help_text='Razon social legal.', max_length=160),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='nit',
            field=models.CharField(blank=True, help_text='NIT / RUC / identificacion fiscal.', max_length=40),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='email',
            field=models.EmailField(blank=True, help_text='Correo comercial.', max_length=254),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='direccion',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='sitio_web',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='observaciones',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterModelOptions(
            name='proveedor',
            options={'ordering': ['nombre'], 'verbose_name_plural': 'Proveedores'},
        ),
        migrations.AlterField(
            model_name='proveedor',
            name='contacto',
            field=models.CharField(blank=True, help_text='Persona de contacto principal.', max_length=100, null=True),
        ),

        # === TipoLicencia: catalogo comercial completo ===
        migrations.AddField(
            model_name='tipolicencia',
            name='codigo',
            field=models.CharField(blank=True, db_index=True, help_text='SKU o codigo interno. Ej: M365-BB, ADBE-CC. Opcional.', max_length=30),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='descripcion',
            field=models.TextField(blank=True, default='', help_text='Descripcion comercial visible en cotizaciones.'),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='precio_compra',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Precio al que se compra al proveedor (referencia interna).', max_digits=12),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='precio_venta',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Precio sugerido al cliente. Usado por cotizaciones y facturas.', max_digits=12),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='moneda',
            field=models.CharField(choices=[('BOB', 'Bolivianos (BOB)'), ('USD', 'Dolares (USD)'), ('EUR', 'Euros (EUR)')], default='BOB', max_length=3),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='proveedor_default',
            field=models.ForeignKey(blank=True, help_text='Proveedor sugerido al crear cotizacion (no obligatorio).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tipos_licencia', to='licencias.proveedor'),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='stock_minimo',
            field=models.PositiveIntegerField(default=0, help_text='Stock minimo de licencias antes de alertar (logico, no fisico).'),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='observaciones',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='tipolicencia',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='tipolicencia',
            name='nombre',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterModelOptions(
            name='tipolicencia',
            options={'ordering': ['fabricante', 'nombre']},
        ),

        # === Asignacion: estado del ciclo de vida ===
        migrations.AddField(
            model_name='asignacion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('ASIGNADA', 'Asignada'),
                    ('LIBERADA', 'Liberada'),
                    ('SUSPENDIDA', 'Suspendida'),
                    ('VENCIDA', 'Vencida'),
                ],
                default='ASIGNADA',
                max_length=12,
            ),
        ),
    ]
