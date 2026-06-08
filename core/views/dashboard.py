from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Prefetch
from datetime import timedelta
from ..models import (Trabajador, Obra, Contrato, TipoDocumento, Documento,
                      Strike, Traslado, get_checklist_trabajador, get_checklist_contrato)


@login_required
def dashboard(request):
    hoy = timezone.now().date()

    # ── KPIs ──────────────────────────────────────────────────────────────
    total_trabajadores = Trabajador.objects.filter(activo=True).count()
    obras_activas = Obra.objects.filter(activo=True, estado='Activa').count()
    contratos_pendientes_firma = Contrato.objects.filter(
        activo=True, estado='Pendiente de Firma'
    ).count()
    contratos_finalizados = Contrato.objects.filter(activo=True, estado='Finalizado')
    finiquitos_pendientes = sum(
        1 for c in contratos_finalizados
        if not Documento.objects.filter(
            contrato=c, tipo_documento__nombre__icontains='finiquito', activo=True
        ).exists()
    )
    obras_proximas_cierre = Obra.objects.filter(
        activo=True, estado='Activa',
        fecha_termino_estimada__lte=hoy + timedelta(days=30),
        fecha_termino_estimada__gte=hoy
    ).count()

    # ── Alertas: contratos por vencer (≤15 días) ─────────────────────────
    alertas_contratos = Contrato.objects.filter(
        activo=True, estado='Vigente',
        fecha_termino_estimada__lte=hoy + timedelta(days=15),
        fecha_termino_estimada__gte=hoy
    ).select_related('trabajador', 'obra', 'especialidad').order_by('fecha_termino_estimada')

    contratos_por_vencer_count = alertas_contratos.count()

    # ── Carpeta de obra: docs obligatorios faltantes por obra activa ─────
    tipos_obra = list(TipoDocumento.objects.filter(nivel='Obra', obligatorio=True, activo=True))
    obras_estado = []
    for obra in Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada']).order_by('nombre'):
        subidos = set(
            Documento.objects.filter(obra=obra, activo=True)
            .values_list('tipo_documento_id', flat=True)
        )
        faltantes = [t for t in tipos_obra if t.pk not in subidos]
        if faltantes:
            obras_estado.append({
                'obra': obra,
                'faltantes': faltantes,
            })

    # ── Disciplina ────────────────────────────────────────────────────────
    alertas_disciplina = []
    for t in Trabajador.objects.filter(activo=True, en_lista_negra=False):
        if t.strikes_activos >= 3:
            contratos_t = Contrato.objects.filter(
                trabajador=t, estado='Vigente', activo=True
            ).select_related('obra')
            alertas_disciplina.append({
                'trabajador': t,
                'strikes_count': t.strikes_activos,
                'contratos': contratos_t,
            })

    # ── Trabajadores activos en 2+ obras simultáneas ─────────────────────
    ruts_multi = (
        Contrato.objects
        .filter(activo=True, estado__in=['Vigente', 'Pendiente de Firma'])
        .values('trabajador')
        .annotate(n_obras=Count('obra', distinct=True))
        .filter(n_obras__gte=2)
        .values_list('trabajador', flat=True)
    )
    trabajadores_multi_obra = list(
        Trabajador.objects.filter(rut__in=ruts_multi).prefetch_related(
            Prefetch(
                'contratos',
                queryset=Contrato.objects.filter(
                    activo=True, estado__in=['Vigente', 'Pendiente de Firma']
                ).select_related('obra'),
                to_attr='contratos_activos',
            )
        ).order_by('nombres', 'apellidos')
    )

    # ── Traslados con finiquito pendiente ─────────────────────────────────
    traslados_pendientes_finiquito = Traslado.objects.filter(
        tipo_traslado='CON_FINIQUITO',
        finiquito_pendiente=True,
        activo=True
    ).select_related('trabajador', 'obra_origen', 'obra_destino').order_by('-creado_el')[:10]

    # ── Vencimientos próximos — 3 umbrales ───────────────────────────────
    # Documentos
    docs_venc_2 = list(Documento.objects.filter(
        activo=True,
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=2)
    ).select_related('tipo_documento', 'contrato__trabajador', 'contrato__obra').order_by('fecha_vencimiento'))

    docs_venc_7 = list(Documento.objects.filter(
        activo=True,
        fecha_vencimiento__gt=hoy + timedelta(days=2),
        fecha_vencimiento__lte=hoy + timedelta(days=7)
    ).select_related('tipo_documento', 'contrato__trabajador', 'contrato__obra').order_by('fecha_vencimiento'))

    docs_venc_15 = list(Documento.objects.filter(
        activo=True,
        fecha_vencimiento__gt=hoy + timedelta(days=7),
        fecha_vencimiento__lte=hoy + timedelta(days=15)
    ).select_related('tipo_documento', 'contrato__trabajador', 'contrato__obra').order_by('fecha_vencimiento'))

    # Contratos (por fecha_termino_estimada)
    contr_venc_2 = list(alertas_contratos.filter(fecha_termino_estimada__lte=hoy + timedelta(days=2)))
    contr_venc_7 = list(alertas_contratos.filter(
        fecha_termino_estimada__gt=hoy + timedelta(days=2),
        fecha_termino_estimada__lte=hoy + timedelta(days=7)
    ))
    contr_venc_15 = list(alertas_contratos.filter(
        fecha_termino_estimada__gt=hoy + timedelta(days=7),
        fecha_termino_estimada__lte=hoy + timedelta(days=15)
    ))

    context = {
        'hoy': hoy,
        'total_trabajadores': total_trabajadores,
        'obras_activas_count': obras_activas,
        'contratos_por_vencer_count': contratos_por_vencer_count,
        'contratos_pendientes_firma_count': contratos_pendientes_firma,
        'finiquitos_pendientes_count': finiquitos_pendientes,
        'obras_proximas_cierre_count': obras_proximas_cierre,
        # Alertas
        'alertas_contratos': alertas_contratos,
        'obras_estado': obras_estado,
        'alertas_disciplina': alertas_disciplina,
        'traslados_pendientes_finiquito': traslados_pendientes_finiquito,
        'trabajadores_multi_obra': trabajadores_multi_obra,
        # Vencimientos por umbral
        'docs_venc_2': docs_venc_2,
        'docs_venc_7': docs_venc_7,
        'docs_venc_15': docs_venc_15,
        'contr_venc_2': contr_venc_2,
        'contr_venc_7': contr_venc_7,
        'contr_venc_15': contr_venc_15,
    }
    return render(request, 'dashboard/index.html', context)
