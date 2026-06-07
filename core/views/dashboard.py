from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from ..models import (Trabajador, Obra, Contrato, TipoDocumento, Documento,
                      Strike, BodegaObra, Traslado, get_checklist_trabajador)


@login_required
def dashboard(request):
    hoy = timezone.now().date()
    limite_vencimiento = hoy + timedelta(days=10)

    # KPIs rápidos
    total_trabajadores = Trabajador.objects.filter(activo=True).count()
    obras_activas = Obra.objects.filter(activo=True, estado='Activa').count()
    contratos_por_vencer = Contrato.objects.filter(
        activo=True, estado='Vigente',
        fecha_termino_estimada__lte=limite_vencimiento,
        fecha_termino_estimada__gte=hoy
    ).count()

    # KPI: Contratos pendientes de firma
    contratos_pendientes_firma = Contrato.objects.filter(
        activo=True, estado='Pendiente de Firma'
    ).count()

    # KPI: Finiquitos pendientes (contratos finalizados sin doc finiquito)
    contratos_finalizados = Contrato.objects.filter(activo=True, estado='Finalizado')
    finiquitos_pendientes = sum(
        1 for c in contratos_finalizados
        if not Documento.objects.filter(
            contrato=c, tipo_documento__nombre__icontains='finiquito', activo=True
        ).exists()
    )

    # KPI: Obras próximas a cierre (fecha_termino_estimada en ≤30 días)
    limite_30 = hoy + timedelta(days=30)
    obras_proximas_cierre = Obra.objects.filter(
        activo=True, estado='Activa',
        fecha_termino_estimada__lte=limite_30,
        fecha_termino_estimada__gte=hoy
    ).count()

    # Alertas: contratos por vencer (≤10 días)
    alertas_contratos = Contrato.objects.filter(
        activo=True, estado='Vigente',
        fecha_termino_estimada__lte=limite_vencimiento,
        fecha_termino_estimada__gte=hoy
    ).select_related('trabajador', 'obra', 'especialidad').order_by('fecha_termino_estimada')

    # Alertas: documentos faltantes O vencidos para trabajadores activos
    alertas_documentos = []
    ruts_procesados = set()
    for contrato in Contrato.objects.filter(activo=True, estado='Vigente').select_related('trabajador', 'obra'):
        rut = contrato.trabajador.rut
        if rut in ruts_procesados:
            continue
        ruts_procesados.add(rut)
        checklist = get_checklist_trabajador(rut)
        for item in checklist:
            if not item['tipo'].obligatorio:
                continue
            if item['estado'] in ('pendiente', 'vencido'):
                alertas_documentos.append({
                    'trabajador': contrato.trabajador,
                    'obra': contrato.obra,
                    'tipo_documento': item['tipo'],
                    'contrato': contrato,
                    'estado_doc': item['estado'],
                    'doc': item['doc'],
                })

    # Alertas: bajo stock crítico
    alertas_stock = BodegaObra.objects.filter(
        obra__activo=True, obra__estado='Activa'
    ).select_related('obra', 'material')
    alertas_stock = [b for b in alertas_stock if b.bajo_stock]

    # Alertas: riesgo disciplinario (≥3 strikes)
    alertas_disciplina = []
    for t in Trabajador.objects.filter(activo=True, en_lista_negra=False):
        if t.strikes_activos >= 3:
            obras_activas_t = Contrato.objects.filter(
                trabajador=t, estado='Vigente', activo=True
            ).select_related('obra')
            alertas_disciplina.append({
                'trabajador': t,
                'strikes_count': t.strikes_activos,
                'contratos': obras_activas_t,
            })

    # Próximos vencimientos (15 días)
    limite_15 = hoy + timedelta(days=15)
    proximos_vencimientos = Contrato.objects.filter(
        activo=True, estado='Vigente',
        fecha_termino_estimada__lte=limite_15,
        fecha_termino_estimada__gte=hoy
    ).select_related('trabajador', 'obra').order_by('fecha_termino_estimada')

    # Documentos que vencen esta semana
    limite_7 = hoy + timedelta(days=7)
    docs_vencen_semana = Documento.objects.filter(
        activo=True,
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite_7
    ).select_related('tipo_documento').order_by('fecha_vencimiento')[:15]

    # Traslados con finiquito pendiente
    traslados_pendientes_finiquito = Traslado.objects.filter(
        tipo_traslado='CON_FINIQUITO',
        finiquito_pendiente=True,
        activo=True
    ).select_related('trabajador', 'obra_origen', 'obra_destino').order_by('-creado_el')[:10]

    context = {
        'total_trabajadores': total_trabajadores,
        'obras_activas_count': obras_activas,
        'contratos_por_vencer_count': contratos_por_vencer,
        'contratos_pendientes_firma_count': contratos_pendientes_firma,
        'finiquitos_pendientes_count': finiquitos_pendientes,
        'obras_proximas_cierre_count': obras_proximas_cierre,
        'alertas_contratos': alertas_contratos,
        'alertas_documentos': alertas_documentos[:20],
        'alertas_stock': alertas_stock,
        'alertas_disciplina': alertas_disciplina,
        'proximos_vencimientos': proximos_vencimientos,
        'docs_vencen_semana': docs_vencen_semana,
        'traslados_pendientes_finiquito': traslados_pendientes_finiquito,
        'hoy': hoy,
    }
    return render(request, 'dashboard/index.html', context)
