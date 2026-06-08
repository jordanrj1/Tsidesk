from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_receptor_libre'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrato',
            name='fecha_inicio_licencia',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='fecha_fin_licencia',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contrato',
            name='obs_licencia',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='contrato',
            name='estado',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('Pendiente de Firma', 'Pendiente de Firma'),
                    ('Vigente', 'Vigente'),
                    ('En Licencia', 'En Licencia'),
                    ('Reactivado', 'Reactivado'),
                    ('Finalizado', 'Finalizado'),
                    ('Rescindido', 'Rescindido'),
                    ('Trasladado', 'Trasladado'),
                ],
                default='Pendiente de Firma',
            ),
        ),
        migrations.AlterField(
            model_name='documentogenerado',
            name='tipo',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('contrato_trabajo', 'Contrato de Trabajo'),
                    ('anexo_contrato', 'Anexo Contrato de Trabajo'),
                    ('finiquito', 'Finiquito de Trabajo'),
                    ('pacto_horas_extras', 'Pacto Horas Extraordinarias'),
                    ('acta_epp', 'Acta Entrega EPP'),
                    ('acta_reglamento', 'Acta Entrega Reglamento Interno'),
                    ('acta_reactivacion', 'Acta de Reactivación Post-Licencia'),
                ],
            ),
        ),
    ]
