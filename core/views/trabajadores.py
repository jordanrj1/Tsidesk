import json, zipfile, io, os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q
from ..models import (Trabajador, Contrato, Documento, Strike,
                      HistorialListaNegra, TipoDocumento, LogAuditoria, Traslado,
                      get_checklist_trabajador, get_checklist_contrato, get_alertas_cruzadas)
from ..forms import (TrabajadorForm, TrabajadorEditForm, StrikeForm, StrikeEditForm,
                     ListaNegraIngresoForm, ListaNegraSalidaForm, DocumentoForm)


@login_required
def trabajadores_list(request):
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    lista_negra = request.GET.get('lista_negra', '')
    obra_id = request.GET.get('obra_id', '')

    qs = Trabajador.objects.filter(activo=True).order_by('nombres', 'apellidos')
    if q:
        qs = qs.filter(
            Q(nombres__icontains=q) | Q(apellidos__icontains=q) |
            Q(rut__icontains=q) | Q(telefono__icontains=q) | Q(correo__icontains=q)
        )
    if obra_id:
        ruts_en_obra = Contrato.objects.filter(
            obra_id=obra_id, activo=True
        ).values_list('trabajador_id', flat=True)
        qs = qs.filter(rut__in=ruts_en_obra)
    if estado == 'activo':
        qs = qs.filter(contratos__estado='Vigente', contratos__activo=True).distinct()
    elif estado == 'sin_contrato':
        rutss_con_contrato = Contrato.objects.filter(
            estado='Vigente', activo=True).values_list('trabajador_id', flat=True)
        qs = qs.exclude(rut__in=rutss_con_contrato)
    if lista_negra == '1':
        qs = qs.filter(en_lista_negra=True)

    # Progreso documental por trabajador
    tipos_obligatorios = list(TipoDocumento.objects.filter(activo=True, nivel='Trabajador', obligatorio=True))
    total_tipos = len(tipos_obligatorios)
    progreso_dict = {}
    hoy = timezone.now().date()
    for t in qs:
        ok = 0
        for tipo in tipos_obligatorios:
            doc = Documento.objects.filter(
                tipo_documento=tipo, trabajador_rut=t.rut, activo=True
            ).order_by('-fecha_carga').first()
            if doc and not doc.esta_vencido:
                ok += 1
        progreso_dict[t.rut] = {'ok': ok, 'total': total_tipos}

    # Trabajadores con traslados con finiquito pendiente
    ruts_con_alerta_traslado = set(
        Traslado.objects.filter(
            tipo_traslado='CON_FINIQUITO',
            finiquito_pendiente=True,
            activo=True
        ).values_list('trabajador_id', flat=True)
    )

    from ..models import Obra
    context = {
        'trabajadores': qs,
        'q': q,
        'estado': estado,
        'lista_negra': lista_negra,
        'obra_id': obra_id,
        'obras': Obra.objects.filter(activo=True).order_by('nombre'),
        'progreso_dict': progreso_dict,
        'total_tipos': total_tipos,
        'ruts_con_alerta_traslado': ruts_con_alerta_traslado,
    }
    return render(request, 'trabajadores/list.html', context)


@login_required
def trabajador_create(request):
    if request.method == 'POST':
        form = TrabajadorForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save()
            _audit(request, 'CREATE', 'Trabajador', t.rut, {'nuevo': t.rut})
            messages.success(request, f'Trabajador {t.nombre_completo} registrado exitosamente.')
            # "Guardar y Crear Contrato" redirige directo al formulario de contrato
            if 'crear_contrato' in request.POST:
                return redirect(f'/contratos/nuevo/?trabajador_rut={t.rut}')
            return redirect('trabajador_detail', rut=t.rut)
    else:
        form = TrabajadorForm()
    return render(request, 'trabajadores/form.html', {'form': form, 'titulo': 'Nuevo Trabajador'})


@login_required
def trabajador_check_rut(request):
    """AJAX: verifica si un RUT ya existe y retorna estado (lista negra, activo, etc.)."""
    rut = request.GET.get('rut', '').strip()
    if not rut:
        return JsonResponse({'existe': False})
    try:
        t = Trabajador.objects.get(rut=rut, activo=True)
        return JsonResponse({
            'existe': True,
            'nombre': t.nombre_completo,
            'en_lista_negra': t.en_lista_negra,
            'contratos_vigentes': t.contratos_vigentes.count(),
            'url_ficha': f'/trabajadores/{t.rut}/',
            'url_contrato': f'/contratos/nuevo/?trabajador_rut={t.rut}',
        })
    except Trabajador.DoesNotExist:
        return JsonResponse({'existe': False})


@login_required
def trabajador_detail(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    contratos = trabajador.contratos.filter(activo=True).select_related('obra', 'especialidad').order_by('-creado_el')
    strikes = trabajador.strikes.filter(activo=True).order_by('-fecha_incidente')
    historial_negra = trabajador.historial_lista_negra.order_by('-fecha_registro')

    # Checklist en vivo: cálculo dinámico, no tabla almacenada
    checklist_trabajador = get_checklist_trabajador(rut)

    # Alerta de recontratación: si hay contrato nuevo y docs vencidos/pendientes
    tiene_alerta_docs = any(
        item['estado'] in ('pendiente', 'vencido')
        for item in checklist_trabajador
        if item['tipo'].obligatorio
    )

    contratos_con_docs = []
    for contrato in contratos:
        checklist_contrato = get_checklist_contrato(contrato)
        resumen = {'sin_cargar': 0, 'vencido': 0, 'proximo': 0}
        for ci in checklist_contrato:
            if ci['estado'] == 'pendiente':
                resumen['sin_cargar'] += 1
            elif ci['estado'] == 'vencido':
                resumen['vencido'] += 1
            elif ci['estado'] == 'proximo':
                resumen['proximo'] += 1
        contratos_con_docs.append({
            'contrato': contrato,
            'checklist': checklist_contrato,
            'resumen': resumen,
        })

    resumen_personal = {'sin_cargar': 0, 'vencido': 0, 'proximo': 0}
    for item in checklist_trabajador:
        if item['estado'] == 'pendiente':
            resumen_personal['sin_cargar'] += 1
        elif item['estado'] == 'vencido':
            resumen_personal['vencido'] += 1
        elif item['estado'] == 'proximo':
            resumen_personal['proximo'] += 1

    traslados = Traslado.objects.filter(
        trabajador=trabajador, activo=True
    ).select_related('obra_origen', 'obra_destino', 'contrato_origen', 'contrato_destino').order_by('-creado_el')
    alertas_cruzadas = get_alertas_cruzadas(rut)

    contratos_vigentes_count = sum(1 for c in contratos if c.estado == 'Vigente')
    docs_alerta_count = sum(
        1 for item in checklist_trabajador
        if item['estado'] in ('pendiente', 'vencido', 'proximo')
    )

    tab = request.GET.get('tab', 'contratos')
    context = {
        'trabajador': trabajador,
        'contratos': contratos,
        'contratos_con_docs': contratos_con_docs,
        'strikes': strikes,
        'historial_negra': historial_negra,
        'checklist_trabajador': checklist_trabajador,
        'tiene_alerta_docs': tiene_alerta_docs,
        'traslados': traslados,
        'alertas_cruzadas': alertas_cruzadas,
        'contratos_vigentes_count': contratos_vigentes_count,
        'docs_alerta_count': docs_alerta_count,
        'resumen_personal': resumen_personal,
        'tab': tab,
    }
    return render(request, 'trabajadores/detail.html', context)


@login_required
def trabajador_edit(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if request.method == 'POST':
        form = TrabajadorEditForm(request.POST, request.FILES, instance=trabajador)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ficha actualizada correctamente.')
            return redirect(next_url) if next_url else redirect('trabajador_detail', rut=rut)
    else:
        form = TrabajadorEditForm(instance=trabajador)
    return render(request, 'trabajadores/form.html', {
        'form': form, 'titulo': 'Editar Trabajador',
        'trabajador': trabajador, 'next_url': next_url,
    })


@login_required
def trabajador_upload_doc(request, rut):
    """Redirige a la carga guiada unificada preservando nivel y contrato_id."""
    from django.urls import reverse
    params = request.GET.urlencode()
    url = reverse('trabajador_upload_doc_masivo', args=[rut])
    return redirect(f'{url}?{params}' if params else url)


@login_required
def trabajador_add_strike(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    if request.method == 'POST':
        form = StrikeForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.trabajador = trabajador
            s.usuario_registro = request.user.username
            s.save()
            messages.success(request, f'Strike registrado para {trabajador.nombre_completo}.')
            return redirect('trabajador_detail', rut=rut)
    else:
        form = StrikeForm()
    return render(request, 'trabajadores/strike_form.html', {'form': form, 'trabajador': trabajador})


@login_required
def trabajador_lista_negra_ingreso(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    if request.method == 'POST':
        form = ListaNegraIngresoForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            trabajador.en_lista_negra = True
            trabajador.save()
            HistorialListaNegra.objects.create(
                trabajador=trabajador,
                accion='INGRESO',
                motivo=motivo,
                usuario_registro=request.user.username,
            )
            # Finalizar contratos vigentes
            Contrato.objects.filter(
                trabajador=trabajador, estado='Vigente', activo=True
            ).update(estado='Rescindido')
            messages.warning(request, f'{trabajador.nombre_completo} ingresado a Lista Negra.')
            return redirect('trabajador_detail', rut=rut)
    else:
        form = ListaNegraIngresoForm()
    contratos_vigentes = trabajador.contratos.filter(estado='Vigente', activo=True).select_related('obra')
    return render(request, 'trabajadores/lista_negra_ingreso.html', {
        'form': form,
        'trabajador': trabajador,
        'contratos_vigentes': contratos_vigentes,
    })


@login_required
def trabajador_lista_negra_salida(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    if request.method == 'POST':
        form = ListaNegraSalidaForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data['motivo']
            trabajador.en_lista_negra = False
            trabajador.save()
            HistorialListaNegra.objects.create(
                trabajador=trabajador,
                accion='SALIDA',
                motivo=motivo,
                usuario_registro=request.user.username,
            )
            messages.success(request, f'{trabajador.nombre_completo} removido de Lista Negra.')
            return redirect('trabajador_detail', rut=rut)
    else:
        form = ListaNegraSalidaForm()
    return render(request, 'trabajadores/lista_negra_salida.html', {'form': form, 'trabajador': trabajador})


@login_required
def trabajador_download_zip(request, rut):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    docs = Documento.objects.filter(
        Q(trabajador_rut=rut) | Q(contrato__trabajador__rut=rut),
        activo=True
    ).select_related('tipo_documento', 'contrato', 'contrato__obra')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.archivo and os.path.exists(doc.archivo.path):
                if doc.contrato:
                    folder = f"contratos/{doc.contrato.obra.nombre}/{doc.tipo_documento.nombre}"
                else:
                    folder = "documentos_personales"
                arcname = f"{folder}/{doc.nombre_archivo}"
                zf.write(doc.archivo.path, arcname)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="carpeta_{rut}.zip"'
    return response


@login_required
def trabajador_edit_strike(request, rut, pk):
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    strike = get_object_or_404(Strike, pk=pk, trabajador=trabajador)
    if request.method == 'POST':
        form = StrikeEditForm(request.POST, instance=strike)
        if form.is_valid():
            form.save()
            messages.success(request, 'Strike actualizado.')
            return redirect(f'/trabajadores/{rut}/?tab=strikes')
    else:
        form = StrikeEditForm(instance=strike)
    return render(request, 'trabajadores/strike_edit.html', {
        'form': form, 'trabajador': trabajador, 'strike': strike
    })


@login_required
def trabajador_toggle_strike(request, rut, pk):
    """Desactiva o reactiva un strike (soft delete)."""
    strike = get_object_or_404(Strike, pk=pk, trabajador__rut=rut)
    if request.method == 'POST':
        strike.activo = not strike.activo
        strike.save()
        accion = 'reactivado' if strike.activo else 'anulado'
        messages.info(request, f'Strike {accion}.')
    return redirect(f'/trabajadores/{rut}/?tab=strikes')


@login_required
def trabajador_upload_doc_masivo(request, rut):
    """Carga de documentos guiada: muestra los tipos esperados con campo de archivo por cada uno."""
    from ..models import Contrato
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    nivel = request.GET.get('nivel', 'Trabajador')
    contrato_id = request.GET.get('contrato_id')

    contrato_obj = None
    if contrato_id:
        try:
            contrato_obj = Contrato.objects.select_related('obra', 'especialidad').get(pk=contrato_id)
        except Contrato.DoesNotExist:
            contrato_id = None

    contratos_trabajador = Contrato.objects.filter(
        trabajador=trabajador, activo=True
    ).select_related('obra', 'especialidad').order_by('-creado_el')

    tipos = TipoDocumento.objects.filter(activo=True, nivel=nivel).order_by('nombre')

    # Estado actual de cada tipo para este contexto
    docs_existentes = {}
    for tipo in tipos:
        filtro = {'tipo_documento': tipo, 'activo': True}
        if nivel == 'Contrato' and contrato_obj:
            filtro['contrato'] = contrato_obj
        else:
            filtro['trabajador_rut'] = rut
        docs_existentes[tipo.pk] = Documento.objects.filter(**filtro).order_by('-fecha_carga').first()

    if request.method == 'POST':
        guardados = 0
        for tipo in tipos:
            archivo = request.FILES.get(f'archivo_{tipo.pk}')
            if not archivo:
                continue
            filtro = {'tipo_documento': tipo, 'activo': True}
            if nivel == 'Contrato' and contrato_obj:
                filtro['contrato'] = contrato_obj
            else:
                filtro['trabajador_rut'] = rut
            Documento.objects.filter(**filtro).update(activo=False)
            doc_kwargs = {
                'tipo_documento': tipo,
                'archivo': archivo,
                'usuario_carga': request.user.username,
            }
            if nivel == 'Contrato' and contrato_obj:
                doc_kwargs['contrato'] = contrato_obj
            else:
                doc_kwargs['trabajador_rut'] = rut
            Documento.objects.create(**doc_kwargs)
            guardados += 1

        if guardados and contrato_obj and contrato_obj.estado == 'Pendiente de Firma':
            contrato_obj.estado = 'Vigente'
            contrato_obj.save(update_fields=['estado'])
            messages.success(request, f'{guardados} documento(s) cargado(s). Contrato marcado como Vigente.')
        elif guardados:
            messages.success(request, f'{guardados} documento(s) cargado(s) exitosamente.')
        else:
            messages.warning(request, 'No se seleccionó ningún archivo.')
        return redirect(f'/trabajadores/{rut}/?tab=documentos')

    # Combinar tipo + doc_actual en una sola lista para simplificar el template
    tipos_con_doc = [
        {'tipo': tipo, 'doc_actual': docs_existentes.get(tipo.pk)}
        for tipo in tipos
    ]

    return render(request, 'trabajadores/upload_doc_masivo.html', {
        'trabajador': trabajador,
        'nivel': nivel,
        'contrato_id': contrato_id,
        'contrato_obj': contrato_obj,
        'contratos_trabajador': contratos_trabajador,
        'tipos_con_doc': tipos_con_doc,
    })


@login_required
def trabajador_delete(request, rut):
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para eliminar trabajadores.')
        return redirect('trabajadores_list')
    trabajador = get_object_or_404(Trabajador, rut=rut, activo=True)
    if request.method == 'POST':
        trabajador.activo = False
        trabajador.save(update_fields=['activo'])
        _audit(request, 'DELETE', 'Trabajador', rut, {'eliminado': rut})
        messages.success(request, f'Ficha de {trabajador.nombre_completo} desactivada. Sus contratos e historial se conservan.')
        return redirect('trabajadores_list')
    return redirect('trabajadores_list')


def _audit(request, accion, tabla, registro_id, detalle):
    LogAuditoria.objects.create(
        usuario=request.user.username,
        accion=accion,
        tabla_afectada=tabla,
        registro_id=str(registro_id),
        detalle_cambio=detalle,
    )
