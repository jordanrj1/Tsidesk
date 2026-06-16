from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_contrato_es_recontratacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='fecha_extension',
            field=models.DateField(
                null=True, blank=True,
                help_text='Fecha de término extendida por Anexo de Contrato. No modifica la fecha original del contrato.',
            ),
        ),
    ]
