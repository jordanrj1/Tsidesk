import core.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_contrato_fecha_extension'),
    ]

    operations = [
        # Contrato fields (pending from previous sessions)
        migrations.AlterField(
            model_name='contrato',
            name='contrato_anterior',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recontrataciones',
                to='core.contrato',
            ),
        ),
        migrations.AlterField(
            model_name='contrato',
            name='fecha_extension',
            field=models.DateField(
                blank=True,
                help_text='Fecha extendida por Anexo de Contrato. No modifica la fecha original.',
                null=True,
            ),
        ),
        # Documento: archivo nullable (paper-first support)
        migrations.AlterField(
            model_name='documento',
            name='archivo',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=core.models.documento_upload_path,
            ),
        ),
        # Documento: flag pendiente de digitalización
        migrations.AddField(
            model_name='documento',
            name='pendiente_digitalizacion',
            field=models.BooleanField(
                default=False,
                help_text='El papel existe pero aún no se ha escaneado/subido el archivo.',
            ),
        ),
    ]
