from django.db import migrations, models


def crear_tipo_doc_finiquito(apps, schema_editor):
    TipoDocumento = apps.get_model('core', 'TipoDocumento')
    TipoDocumento.objects.get_or_create(
        nombre='Finiquito de Trabajo',
        defaults={'nivel': 'Contrato', 'obligatorio': False, 'dias_validez': None, 'activo': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_cierre_unique_licencia_institucion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contrato',
            name='estado',
            field=models.CharField(
                max_length=30,
                default='Pendiente de Firma',
                choices=[
                    ('Pendiente de Firma', 'Pendiente de Firma'),
                    ('Vigente', 'Vigente'),
                    ('En Licencia', 'En Licencia'),
                    ('Reactivado', 'Reactivado'),
                    ('Finalizado', 'Finalizado'),
                    ('Finiquitado', 'Finiquitado'),
                    ('Rescindido', 'Rescindido'),
                    ('Trasladado', 'Trasladado'),
                ],
            ),
        ),
        migrations.RunPython(crear_tipo_doc_finiquito, migrations.RunPython.noop),
    ]
