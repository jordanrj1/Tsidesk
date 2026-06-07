from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import (
    Trabajador, Contrato, Documento, Strike, HistorialListaNegra,
    BodegaObra, HistorialMaterial, CierreMensual, LogAuditoria
)
import json
from decimal import Decimal
from datetime import date, datetime


def serialize_value(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if hasattr(v, 'name'):  # FileField, ImageField
        return str(v.name) if v else None
    if isinstance(v, (int, float, str, bool, type(None))):
        return v
    return str(v)


def model_to_dict_simple(instance):
    data = {}
    for field in instance._meta.fields:
        # Use attname (e.g. obra_id) to get the raw FK value, not the related object
        data[field.attname] = serialize_value(getattr(instance, field.attname))
    return data


_pre_save_data = {}


def register_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _pre_save_data[f"{sender.__name__}_{instance.pk}"] = model_to_dict_simple(old)
        except sender.DoesNotExist:
            pass


def register_post_save(sender, instance, created, **kwargs):
    key = f"{sender.__name__}_{instance.pk}"
    old_data = _pre_save_data.pop(key, None)
    new_data = model_to_dict_simple(instance)
    accion = 'CREATE' if created else 'UPDATE'
    detalle = {'nuevo': new_data}
    if old_data:
        detalle['anterior'] = old_data

    LogAuditoria.objects.create(
        usuario='sistema',
        accion=accion,
        tabla_afectada=sender.__name__,
        registro_id=str(instance.pk),
        detalle_cambio=detalle,
    )


AUDITADOS = [Trabajador, Contrato, Documento, Strike, HistorialListaNegra,
             BodegaObra, HistorialMaterial, CierreMensual]

for model_class in AUDITADOS:
    pre_save.connect(register_pre_save, sender=model_class)
    post_save.connect(register_post_save, sender=model_class)
