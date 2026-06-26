# Generated manually for commercial invoice delivery.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licencias', '0013_merge_20260626_0002'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='email_facturacion',
            field=models.EmailField(
                blank=True,
                help_text='Correo donde se enviaran facturas y documentos comerciales.',
                max_length=254,
            ),
        ),
    ]
