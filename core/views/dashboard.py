from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Prefetch
from datetime import timedelta
from ..models import (Trabajador, Obra, Contrato, TipoDocumento, Documento,
                      Strike, Traslado, get_checklist_trabajador, get_checklist_contrato,
                      LicenciaMedica)


@login_required
def dashboard(request):
    hoy = timezone.now().date()

    # ── KPIs ──────────────────────────────────────────────────────────────
    total_trabajadores = Trabajador.objects.filter(activo=True).count()
    obras_activas = Obra.objects.filter(activo=True, estado='Activa').count()
    contratos_pendientes_firma = Contrato.objects.filter(
        activo=True, estado='Pendiente de Firma'
    ).count()
    _fin_contratos = Contrato.objects.filter(activo=True, estado__in=['Finalizado', 'Finiquitado'])
    _fin_ids = list(_fin_contratos.values_list('pk', flat=True))
    _tipo_fin_ids = list(TipoDocumento.objects.filter(nombre='Finiquito Legalizado', activo=True).values_list('pk', flat=True))
    _con_finiquito = set(
        Documento.objects.filter(contrato_id__in=_fin_ids, tipo_documento_id__in=_tipo_fin_ids, activo=True)
        .values_list('contrato_id', flat=True)
    )
    finiquitos_pendientes = sum(1 for pk in _fin_ids if pk not in _con_finiquito)
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

    # ── Carpeta de obra + panel de alertas por obra ───────────────────────
    tipos_obra = list(TipoDocumento.objects.filter(nivel='Obra', obligatorio=True, activo=True))
    obras_activas_qs = list(Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada']).order_by('nombre'))

    # Batch: docs subidos por obra
    _subidos_por_obra = {}
    for tipo_pk, obra_pk in Documento.objects.filter(
        obra__in=obras_activas_qs, activo=True
    ).values_list('tipo_documento_id', 'obra_id'):
        _subidos_por_obra.setdefault(obra_pk, set()).add(tipo_pk)

    # Batch: contratos terminados (Finalizado / Finiquitado)
    _contratos_term = list(Contrato.objects.filter(
        obra__in=obras_activas_qs, estado__in=['Finalizado', 'Finiquitado'], activo=True,
    ).only('pk', 'obra_id'))
    _term_ids = [c.pk for c in _contratos_term]
    _con_fin_ids = set(
        Documento.objects.filter(
            contrato_id__in=_term_ids, tipo_documento_id__in=_tipo_fin_ids, activo=True
        ).values_list('contrato_id', flat=True)
    )

    # Batch: contratos vigentes con fecha
    _vigentes = list(Contrato.objects.filter(
        obra__in=obras_activas_qs, estado='Vigente', activo=True,
    ).only('pk', 'obra_id', 'fecha_termino_estimada'))

    # Batch: re-contrataciones con anterior pendiente
    _rec = list(Contrato.objects.filter(
        obra__in=obras_activas_qs, es_recontratacion=True, activo=True,
    ).only('obra_id', 'contrato_anterior_id'))
    _all_ant_ids = [r.contrato_anterior_id for r in _rec if r.contrato_anterior_id]
    _ants_con_fin = set(
        Documento.objects.filter(
            contrato_id__in=_all_ant_ids, tipo_documento_id__in=_tipo_fin_ids, activo=True
        ).values_list('contrato_id', flat=True)
    )

    obras_estado = []
    obras_alertas = []
    for obra in obras_activas_qs:
        subidos = _subidos_por_obra.get(obra.pk, set())
        faltantes = [t for t in tipos_obra if t.pk not in subidos]
        if faltantes:
            obras_estado.append({'obra': obra, 'faltantes': faltantes})

        dias_cierre = (obra.fecha_termino_estimada - hoy).days if obra.fecha_termino_estimada else None
        term_obra = {c.pk for c in _contratos_term if c.obra_id == obra.pk}
        n_fin_pend = sum(1 for pk in term_obra if pk not in _con_fin_ids)
        vig_obra = [c for c in _vigentes if c.obra_id == obra.pk]
        n_vencidos = sum(1 for c in vig_obra if c.fecha_termino_estimada and c.fecha_termino_estimada < hoy)
        n_proximos = sum(1 for c in vig_obra if c.fecha_termino_estimada and 0 <= (c.fecha_termino_estimada - hoy).days <= 10)
        n_docs = len(faltantes)
        rec_ants = [r.contrato_anterior_id for r in _rec if r.obra_id == obra.pk and r.contrato_anterior_id]
        n_rec_pend = sum(1 for ant_id in rec_ants if ant_id not in _ants_con_fin)

        tiene_cualquier_alerta = bool(
            n_fin_pend or n_vencidos or n_proximos or n_docs or n_rec_pend
            or (dias_cierre is not None and dias_cierre <= 30)
        )
        if tiene_cualquier_alerta:
            obras_alertas.append({
                'obra': obra,
                'dias_cierre': dias_cierre,
                'n_finiquitos_pend': n_fin_pend,
                'n_vencidos': n_vencidos,
                'n_proximos': n_proximos,
                'n_docs_faltantes': n_docs,
                'n_recontrataciones_pend': n_rec_pend,
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

    # ── Alertas ERP: Pendiente de Firma > 15 días ────────────────────────
    contratos_pdf_antiguos = Contrato.objects.filter(
        activo=True, estado='Pendiente de Firma',
        fecha_inicio__lte=hoy - timedelta(days=15)
    ).select_related('trabajador', 'obra').order_by('fecha_inicio')

    # ── Alertas ERP: En Licencia > 30 días ───────────────────────────────
    contratos_licencia_larga = Contrato.objects.filter(
        activo=True, estado='En Licencia',
        fecha_inicio_licencia__lte=hoy - timedelta(days=30)
    ).select_related('trabajador', 'obra').order_by('fecha_inicio_licencia')

    # ── Contratos vencidos sin renovar (término estimado < hoy, estado Vigente) ─
    contratos_vencidos_sin_renovar = Contrato.objects.filter(
        activo=True, estado='Vigente',
        fecha_termino_estimada__lt=hoy
    ).select_related('trabajador', 'obra').order_by('fecha_termino_estimada')

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
        'obras_alertas': obras_alertas,
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
        # Alertas ERP
        'contratos_pdf_antiguos': contratos_pdf_antiguos,
        'contratos_licencia_larga': contratos_licencia_larga,
        'contratos_vencidos_sin_renovar': contratos_vencidos_sin_renovar,
    }
    return render(request, 'dashboard/index.html', context)
