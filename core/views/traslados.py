from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from ..models import Obra, Contrato, Trabajador, Traslado, Documento, get_alertas_cruzadas


@login_required
def obra_traslado_masivo(request, pk):
    """Página de traslado masivo de personal desde una obra."""
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    contratos = Contrato.objects.filter(
        obra=obra, estado='Vigente', activo=True
    ).select_related('trabajador', 'especialidad')
    obras_destino = Obra.objects.filter(activo=True, estado='Activa').exclude(pk=pk)
    hoy = timezone.now().date().isoformat()
    return render(request, 'obras/traslado_masivo.html', {
        'obra': obra,
        'contratos': contratos,
        'obras_destino': obras_destino,
        'hoy': hoy,
    })


@login_required
def obra_traslado_ejecutar(request, pk):
    """POST: ejecuta el traslado masivo de trabajadores seleccionados."""
    if request.method != 'POST':
        return redirect('obra_traslado_masivo', pk=pk)

    obra_origen = get_object_or_404(Obra, pk=pk, activo=True)
    contrato_ids = request.POST.getlist('contrato_ids')
    tipo_traslado = request.POST.get('tipo_traslado', 'SIN_FINIQUITO')
    obra_destino_id = request.POST.get('obra_destino_id', '')
    fecha_traslado_str = request.POST.get('fecha_traslado', '')
    observaciones = request.POST.get('observaciones', '')

    if not contrato_ids:
        messages.error(request, 'Debe seleccionar al menos un trabajador.')
        return redirect('obra_traslado_masivo', pk=pk)

    try:
        from datetime import date
        fecha_traslado = date.fromisoformat(fecha_traslado_str)
    except (ValueError, TypeError):
        messages.error(request, 'Fecha de traslado inválida.')
        return redirect('obra_traslado_masivo', pk=pk)

    obra_destino = None
    if obra_destino_id:
        obra_destino = get_object_or_404(Obra, pk=obra_destino_id, activo=True)

    contratos = Contrato.objects.filter(
        pk__in=contrato_ids, obra=obra_origen, estado='Vigente', activo=True
    ).select_related('trabajador', 'especialidad')

    trasladados = 0
    for contrato in contratos:
        traslado = Traslado(
            trabajador=contrato.trabajador,
            contrato_origen=contrato,
            obra_origen=obra_origen,
            obra_destino=obra_destino,
            tipo_traslado=tipo_traslado,
            fecha_traslado=fecha_traslado,
            observaciones=observaciones,
            usuario_registro=request.user.username,
        )

        if tipo_traslado == 'SIN_FINIQUITO':
            # Opción A: Cierra contrato como "Trasladado" y crea nuevo en obra destino
            contrato.estado = 'Trasladado'
            contrato.fecha_termino_real = fecha_traslado
            contrato.save()
            traslado.finiquito_pendiente = False
            traslado.save()

            if obra_destino:
                nuevo_contrato = Contrato.objects.create(
                    trabajador=contrato.trabajador,
                    obra=obra_destino,
                    especialidad=contrato.especialidad,
                    sueldo_base=contrato.sueldo_base,
                    tipo_contrato=contrato.tipo_contrato,
                    fecha_inicio=fecha_traslado,
                    estado='Vigente',
                )
                traslado.contrato_destino = nuevo_contrato
                traslado.save(update_fields=['contrato_destino'])

        else:  # CON_FINIQUITO
            # Opción B: Finaliza contrato (requiere finiquito) y crea nuevo
            contrato.estado = 'Finalizado'
            contrato.fecha_termino_real = fecha_traslado
            contrato.save()
            traslado.finiquito_pendiente = True
            traslado.save()

            if obra_destino:
                nuevo_contrato = Contrato.objects.create(
                    trabajador=contrato.trabajador,
                    obra=obra_destino,
                    especialidad=contrato.especialidad,
                    sueldo_base=contrato.sueldo_base,
                    tipo_contrato=contrato.tipo_contrato,
                    fecha_inicio=fecha_traslado,
                    estado='Pendiente de Firma',
                )
                traslado.contrato_destino = nuevo_contrato
                traslado.save(update_fields=['contrato_destino'])

        trasladados += 1

    tipo_str = "sin finiquito" if tipo_traslado == 'SIN_FINIQUITO' else "con finiquito (pendiente de finiquito)"
    messages.success(request, f'{trasladados} trabajador(es) trasladado(s) {tipo_str} a "{obra_destino.nombre if obra_destino else "sin asignación"}".')

    if tipo_traslado == 'CON_FINIQUITO':
        messages.warning(request, 'Recuerde cargar los finiquitos de los trabajadores trasladados en esta obra.')

    return redirect('obra_detail', pk=pk)


@login_required
def trabajador_alertas_cruzadas_ajax(request, rut):
    """AJAX: retorna alertas cruzadas de traslados pendientes para un trabajador."""
    alertas = get_alertas_cruzadas(rut)
    data = []
    for a in alertas:
        data.append({
            'tipo': a['tipo'],
            'mensaje': a['mensaje'],
            'obra_nombre': a['obra'].nombre,
            'obra_id': a['obra'].pk,
        })
    return JsonResponse({'alertas': data, 'total': len(data)})
