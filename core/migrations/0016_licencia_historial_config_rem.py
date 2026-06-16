from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_contrato_licencia_fields'),
    ]

    operations = [
        # ── LicenciaMedica ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='LicenciaMedica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('numero_folio', models.CharField(blank=True, default='', max_length=50)),
                ('tipo', models.CharField(
                    choices=[
                        ('1', 'Tipo 1 — Enfermedad o accidente común'),
                        ('2', 'Tipo 2 — Accidente laboral / enfermedad profesional (ACHS/Mutual)'),
                        ('3', 'Tipo 3 — Prenatal'),
                        ('4', 'Tipo 4 — Postnatal / hijo menor 1 año'),
                        ('5', 'Tipo 5 — Accidente trabajo de otro trabajador'),
                        ('6', 'Tipo 6 — Enfermedad terminal / desahucio'),
                        ('7', 'Tipo 7 — Ley SANNA (hijo hasta 18 años)'),
                        ('otro', 'Otro'),
                    ], default='1', max_length=10
                )),
                ('organismo', models.CharField(
                    choices=[
                        ('FONASA', 'FONASA'), ('ISAPRE', 'ISAPRE'), ('ACHS', 'ACHS'),
                        ('Mutual de Seguridad', 'Mutual de Seguridad'), ('IST', 'IST'), ('Otro', 'Otro'),
                    ], default='FONASA', max_length=30
                )),
                ('diagnostico', models.TextField(blank=True, default='')),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('dias_autorizados', models.IntegerField(default=0)),
                ('estado', models.CharField(
                    choices=[
                        ('Presentada', 'Presentada'), ('En trámite', 'En trámite'),
                        ('Autorizada', 'Autorizada'), ('Rechazada', 'Rechazada'), ('Prorrogada', 'Prorrogada'),
                    ], default='Presentada', max_length=20
                )),
                ('empresa_pago_3_dias', models.BooleanField(default=False)),
                ('monto_subsidio_esperado', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('monto_subsidio_recibido', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('archivo_formulario', models.FileField(blank=True, null=True, upload_to=core.models.licencia_upload_path)),
                ('archivo_resolucion', models.FileField(blank=True, null=True, upload_to=core.models.licencia_upload_path)),
                ('archivo_alta', models.FileField(blank=True, null=True, upload_to=core.models.licencia_upload_path)),
                ('observaciones', models.TextField(blank=True, default='')),
                ('usuario_registro', models.CharField(max_length=150)),
                ('creado_el', models.DateTimeField(default=django.utils.timezone.now)),
                ('activo', models.BooleanField(default=True)),
                ('contrato', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name='licencias', to='core.contrato'
                )),
                ('obra', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                    related_name='licencias', to='core.obra'
                )),
                ('trabajador', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='licencias', to='core.trabajador', to_field='rut'
                )),
            ],
            options={'verbose_name': 'Licencia Médica', 'verbose_name_plural': 'Licencias Médicas', 'ordering': ['-fecha_inicio']},
        ),

        # ── ContratoHistorial ────────────────────────────────────────────────
        migrations.CreateModel(
            name='ContratoHistorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('estado_anterior', models.CharField(max_length=30)),
                ('estado_nuevo', models.CharField(max_length=30)),
                ('descripcion', models.TextField(blank=True, default='')),
                ('usuario', models.CharField(max_length=150)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('contrato', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historial', to='core.contrato'
                )),
            ],
            options={'verbose_name': 'Historial Contrato', 'verbose_name_plural': 'Historial Contratos', 'ordering': ['-fecha']},
        ),

        # ── ConfigRemuneraciones ─────────────────────────────────────────────
        migrations.CreateModel(
            name='ConfigRemuneraciones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('nombre', models.CharField(default='Configuración General', max_length=100)),
                ('vigente_desde', models.DateField()),
                ('tasa_afp_empleado', models.DecimalField(decimal_places=2, default=10.58, max_digits=5)),
                ('tasa_salud_empleado', models.DecimalField(decimal_places=2, default=7.00, max_digits=5)),
                ('tasa_cesantia_empleado_plazo_fijo', models.DecimalField(decimal_places=2, default=0.60, max_digits=5)),
                ('tasa_cesantia_empleado_indefinido', models.DecimalField(decimal_places=2, default=0.60, max_digits=5)),
                ('tasa_cesantia_empleador', models.DecimalField(decimal_places=2, default=2.40, max_digits=5)),
                ('tasa_mutual_accidentes', models.DecimalField(decimal_places=2, default=0.93, max_digits=5)),
                ('activo', models.BooleanField(default=True)),
                ('notas', models.TextField(blank=True, default='')),
            ],
            options={'verbose_name': 'Config. Remuneraciones', 'verbose_name_plural': 'Config. Remuneraciones', 'ordering': ['-vigente_desde']},
        ),
    ]
