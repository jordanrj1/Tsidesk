import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_contrato_finiquitado_tipo_doc_finiquito'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='es_recontratacion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='contrato',
            name='contrato_anterior',
            field=models.ForeignKey(
                'self',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recontrataciones',
            ),
        ),
    ]
