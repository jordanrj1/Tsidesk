from django.contrib import admin
from .models import (
    TipoDocumento, Especialidad, CatalogoMaterial,
    Trabajador, Obra, Contrato, Documento, Strike,
    HistorialListaNegra, BodegaObra, HistorialMaterial,
    CierreMensual, LogAuditoria
)

admin.site.register(TipoDocumento)
admin.site.register(Especialidad)
admin.site.register(CatalogoMaterial)
admin.site.register(Trabajador)
admin.site.register(Obra)
admin.site.register(Contrato)
admin.site.register(Documento)
admin.site.register(Strike)
admin.site.register(HistorialListaNegra)
admin.site.register(BodegaObra)
admin.site.register(HistorialMaterial)
admin.site.register(CierreMensual)
admin.site.register(LogAuditoria)
