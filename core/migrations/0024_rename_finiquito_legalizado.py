from django.db import migrations


def fusionar_finiquito(apps, schema_editor):
    TipoDocumento = apps.get_model('core', 'TipoDocumento')
    Documento = apps.get_model('core', 'Documento')

    try:
        viejo = TipoDocumento.objects.get(nombre='Finiquito de Trabajo')
    except TipoDocumento.DoesNotExist:
        return  # Ya fue renombrado o no existe

    nuevo, created = TipoDocumento.objects.get_or_create(
        nombre='Finiquito Legalizado',
        defaults={
            'nivel': viejo.nivel,
            'obligatorio': viejo.obligatorio,
            'dias_validez': viejo.dias_validez,
            'activo': viejo.activo,
        }
    )

    if not created:
        # Ya existía "Finiquito Legalizado" — reasignar documentos y borrar el viejo
        Documento.objects.filter(tipo_documento=viejo).update(tipo_documento=nuevo)
        viejo.delete()
    else:
        # Solo se creó como renombrado, no había duplicado
        viejo.delete()


def revertir(apps, schema_editor):
    TipoDocumento = apps.get_model('core', 'TipoDocumento')
    try:
        obj = TipoDocumento.objects.get(nombre='Finiquito Legalizado')
        obj.nombre = 'Finiquito de Trabajo'
        obj.save()
    except TipoDocumento.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_contrato_borrador'),
    ]

    operations = [
        migrations.RunPython(fusionar_finiquito, revertir),
    ]
