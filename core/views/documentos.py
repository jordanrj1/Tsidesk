import io, zipfile, os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from ..models import (Documento, Trabajador, Obra, Contrato, TipoDocumento,
                      Especialidad, get_checklist_trabajador, get_checklist_contrato)


@login_required
def documentos_pendientes(request):
    obra_id = request.GET.get('obra_id', '')
    especialidad_id = request.GET.get('especialidad_id', '')

    contratos_activos = Contrato.objects.filter(
        estado='Vigente', activo=True
    ).select_related('trabajador', 'obra', 'especialidad')

    if obra_id:
        contratos_activos = contratos_activos.filter(obra_id=obra_id)
    if especialidad_id:
        contratos_activos = contratos_activos.filter(especialidad_id=especialidad_id)

    # Agrupar pendientes por trabajador
    grupos = {}  # {rut: {trabajador, obras_set, docs_personales, docs_contrato}}
    for contrato in contratos_activos:
        rut = contrato.trabajador.rut
        if rut not in grupos:
            grupos[rut] = {
                'trabajador': contrato.trabajador,
                'obras': set(),
                'docs_personales': [],
                'docs_contrato': [],
            }
        grupos[rut]['obras'].add(contrato.obra.nombre)

        # Documentos personales (deduplicados por tipo)
        checklist_personal = get_checklist_trabajador(rut)
        vistos_personal = {d['tipo'].pk for d in grupos[rut]['docs_personales']}
        for item in checklist_personal:
            if not item['tipo'].obligatorio:
                continue
            if item['estado'] not in ('pendiente', 'vencido'):
                continue
            if item['tipo'].pk not in vistos_personal:
                vistos_personal.add(item['tipo'].pk)
                grupos[rut]['docs_personales'].append({
                    'tipo': item['tipo'],
                    'estado': item['estado'],
                    'doc': item['doc'],
                })

        # Documentos de contrato/obra
        checklist_contrato = get_checklist_contrato(contrato)
        for item in checklist_contrato:
            if not item['tipo'].obligatorio:
                continue
            if item['estado'] not in ('pendiente', 'vencido'):
                continue
            grupos[rut]['docs_contrato'].append({
                'tipo': item['tipo'],
                'estado': item['estado'],
                'doc': item['doc'],
                'obra': contrato.obra,
                'contrato': contrato,
            })

    grupos_list = sorted(grupos.values(), key=lambda g: g['trabajador'].apellidos)
    total = sum(len(g['docs_personales']) + len(g['docs_contrato']) for g in grupos_list)

    obras = Obra.objects.filter(activo=True)
    especialidades = Especialidad.objects.filter(activo=True)

    context = {
        'grupos': grupos_list,
        'obras': obras,
        'especialidades': especialidades,
        'obra_id': obra_id,
        'especialidad_id': especialidad_id,
        'total': total,
        'total_trabajadores': len(grupos_list),
    }
    return render(request, 'documentos/pendientes.html', context)


@login_required
def documento_download(request, pk):
    doc = get_object_or_404(Documento, pk=pk)
    response = HttpResponse(doc.archivo, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.nombre_archivo}"'
    return response


@login_required
def documento_preview_papelera(request, pk):
    """Sirve el archivo inline para previsualización en nueva pestaña (papelera)."""
    import mimetypes
    from django.views.decorators.clickjacking import xframe_options_exempt
    doc = get_object_or_404(Documento, pk=pk)
    content_type, _ = mimetypes.guess_type(doc.archivo.name)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(doc.archivo.read(), content_type=content_type)
    nombre = os.path.basename(doc.archivo.name)
    response['Content-Disposition'] = f'inline; filename="{nombre}"'
    return response


@login_required
def documento_delete(request, pk):
    doc = get_object_or_404(Documento, pk=pk, activo=True)
    if request.method == 'POST':
        doc.activo = False
        doc.save()
        from django.contrib import messages
        messages.success(request, f'Documento "{doc.tipo_documento.nombre}" movido a la papelera.')
    return redirect('documentos_central')


@login_required
def documento_upload_rapido(request):
    """Upload de un documento específico desde cualquier pantalla (modal), redirige a 'next'."""
    from django.contrib import messages
    from ..models import TipoDocumento, Trabajador, Contrato
    from ..forms import DocumentoForm

    next_url = request.POST.get('next') or request.GET.get('next') or 'documentos_pendientes'

    if request.method == 'POST':
        trabajador_rut = request.POST.get('trabajador_rut', '').strip()
        tipo_id = request.POST.get('tipo_documento_id')
        contrato_id = request.POST.get('contrato_id')
        archivo = request.FILES.get('archivo')
        fecha_vencimiento = request.POST.get('fecha_vencimiento') or None

        try:
            tipo = TipoDocumento.objects.get(pk=tipo_id, activo=True)
        except TipoDocumento.DoesNotExist:
            messages.error(request, 'Tipo de documento no válido.')
            return redirect(next_url)

        if not archivo:
            messages.error(request, 'Debes seleccionar un archivo.')
            return redirect(next_url)

        doc = Documento(
            tipo_documento=tipo,
            trabajador_rut=trabajador_rut if tipo.nivel == 'Trabajador' else None,
            usuario_carga=request.user.username,
            archivo=archivo,
        )
        if fecha_vencimiento:
            from datetime import date
            try:
                doc.fecha_vencimiento = date.fromisoformat(fecha_vencimiento)
            except ValueError:
                pass

        if contrato_id and tipo.nivel == 'Contrato':
            try:
                contrato_obj = Contrato.objects.get(pk=contrato_id)
                doc.contrato = contrato_obj
                doc.trabajador_rut = contrato_obj.trabajador.rut
            except Contrato.DoesNotExist:
                pass

        doc.save()
        messages.success(request, f'"{tipo.nombre}" cargado correctamente.')

    return redirect(next_url)


@login_required
def papelera_documentos(request):
    from django.contrib import messages as msg_module
    qs = Documento.objects.filter(activo=False).select_related(
        'tipo_documento', 'obra', 'contrato', 'contrato__trabajador', 'contrato__obra'
    ).order_by('-fecha_carga')

    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(
            Q(trabajador_rut__icontains=q) |
            Q(contrato__trabajador__nombres__icontains=q) |
            Q(contrato__trabajador__apellidos__icontains=q) |
            Q(tipo_documento__nombre__icontains=q)
        )

    return render(request, 'documentos/papelera.html', {'documentos': qs, 'q': q})


@login_required
def documento_restore(request, pk):
    from django.contrib import messages
    doc = get_object_or_404(Documento, pk=pk, activo=False)
    if request.method == 'POST':
        doc.activo = True
        doc.save()
        messages.success(request, f'Documento "{doc.tipo_documento.nombre}" restaurado correctamente.')
    return redirect('papelera_documentos')


@login_required
def documento_hard_delete(request, pk):
    from django.contrib import messages
    if not request.user.is_superuser:
        messages.error(request, 'Solo el administrador puede eliminar documentos permanentemente.')
        return redirect('papelera_documentos')
    doc = get_object_or_404(Documento, pk=pk, activo=False)
    if request.method == 'POST':
        nombre_tipo = doc.tipo_documento.nombre
        if doc.archivo:
            try:
                if os.path.exists(doc.archivo.path):
                    os.remove(doc.archivo.path)
            except Exception:
                pass
        doc.delete()
        messages.success(request, f'Documento "{nombre_tipo}" eliminado permanentemente.')
    return redirect('papelera_documentos')


@login_required
def documentos_batch_download(request):
    """Descarga selectiva: recibe lista de IDs y genera un ZIP con esos documentos."""
    if request.method == 'POST':
        pks = request.POST.getlist('doc_ids')
    else:
        pks = request.GET.getlist('doc_ids')

    if not pks:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, 'No se seleccionaron documentos.')
        return redirect('documentos_pendientes')

    docs = Documento.objects.filter(pk__in=pks, activo=True).select_related('tipo_documento', 'contrato')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.archivo and os.path.exists(doc.archivo.path):
                ref = doc.trabajador_rut or (f"contrato{doc.contrato_id}" if doc.contrato_id else "obra")
                nombre = f"{ref}_{doc.tipo_documento.nombre}_{doc.nombre_archivo}"
                zf.write(doc.archivo.path, nombre)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="documentos_seleccionados.zip"'
    return response


@login_required
def documentos_central(request):
    """Archivo de documentos: búsqueda agrupada por obra, vacía hasta aplicar filtro."""
    from django.db.models import Q

    obra_id     = request.GET.get('obra_id', '')
    tipo_id     = request.GET.get('tipo_id', '')
    estado_filter = request.GET.get('estado', '')
    q           = request.GET.get('q', '')
    has_filter  = bool(q or obra_id or tipo_id or estado_filter)

    grupos_activas  = []   # [{obra, docs}]
    grupos_cerradas = []
    sin_obra_docs   = []
    total = 0

    if has_filter:
        qs = Documento.objects.filter(activo=True).select_related(
            'tipo_documento', 'obra',
            'contrato', 'contrato__obra',
            'contrato__trabajador', 'contrato__especialidad',
        ).order_by('-fecha_carga')

        if q:
            from ..models import Trabajador as TrabajadorModel
            ruts_match = list(
                TrabajadorModel.objects.filter(
                    Q(nombres__icontains=q) | Q(apellidos__icontains=q)
                ).values_list('rut', flat=True)
            )
            qs = qs.filter(
                Q(trabajador_rut__icontains=q) |
                Q(trabajador_rut__in=ruts_match) |
                Q(contrato__trabajador__nombres__icontains=q) |
                Q(contrato__trabajador__apellidos__icontains=q) |
                Q(tipo_documento__nombre__icontains=q)
            ).distinct()
        if tipo_id:
            qs = qs.filter(tipo_documento_id=tipo_id)
        if obra_id:
            qs = qs.filter(Q(obra_id=obra_id) | Q(contrato__obra_id=obra_id))

        docs_list = list(qs[:300])

        # Deduplicar: solo el doc más reciente por tipo por trabajador/contrato
        # qs viene ordenado por -fecha_carga, así que el primero por clave es el más reciente
        seen = {}
        for doc in docs_list:
            key = (doc.contrato_id or doc.trabajador_rut, doc.tipo_documento_id)
            if key not in seen:
                seen[key] = doc
        docs_list = list(seen.values())

        if estado_filter:
            docs_list = [d for d in docs_list if d.estado_visual == estado_filter]

        # Enriquecer docs personales (sin contrato) con objeto Trabajador
        ruts_personal = {d.trabajador_rut for d in docs_list if d.trabajador_rut and not d.contrato}
        if ruts_personal:
            from ..models import Trabajador as TrabajadorModel
            trab_map = {t.rut: t for t in TrabajadorModel.objects.filter(rut__in=ruts_personal)}
        else:
            trab_map = {}
        for doc in docs_list:
            doc.trab_personal = trab_map.get(doc.trabajador_rut) if (doc.trabajador_rut and not doc.contrato) else None

        # Agrupar por obra; distinguir activas vs cerradas
        _activas  = {}   # obra.pk -> {obra, docs}
        _cerradas = {}
        ACTIVOS = {'Activa', 'Pausada'}
        for doc in docs_list:
            obra_obj = doc.obra or (doc.contrato.obra if doc.contrato else None)
            if obra_obj:
                bucket = _activas if obra_obj.estado in ACTIVOS else _cerradas
                if obra_obj.pk not in bucket:
                    bucket[obra_obj.pk] = {'obra': obra_obj, 'docs': []}
                bucket[obra_obj.pk]['docs'].append(doc)
            else:
                sin_obra_docs.append(doc)

        grupos_activas  = sorted(_activas.values(),  key=lambda x: x['obra'].nombre)
        grupos_cerradas = sorted(_cerradas.values(), key=lambda x: x['obra'].nombre)
        total = len(docs_list)

    from ..models import Obra, TipoDocumento
    context = {
        'has_filter':      has_filter,
        'grupos_activas':  grupos_activas,
        'grupos_cerradas': grupos_cerradas,
        'sin_obra_docs':   sin_obra_docs,
        'obras': Obra.objects.order_by('nombre'),   # activas + cerradas para el selector
        'tipos': TipoDocumento.objects.filter(activo=True).order_by('nombre'),
        'obra_id':      obra_id,
        'tipo_id':      tipo_id,
        'estado_filter': estado_filter,
        'q':    q,
        'total': total,
    }
    return render(request, 'documentos/central.html', context)


@login_required
def documentos_exportar_excel(request):
    """Exporta la lista de documentos pendientes/vencidos a Excel."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return HttpResponse('openpyxl no disponible.', status=500)

    obra_id = request.GET.get('obra_id', '')
    especialidad_id = request.GET.get('especialidad_id', '')

    contratos_activos = Contrato.objects.filter(
        estado='Vigente', activo=True
    ).select_related('trabajador', 'obra', 'especialidad')
    if obra_id:
        contratos_activos = contratos_activos.filter(obra_id=obra_id)
    if especialidad_id:
        contratos_activos = contratos_activos.filter(especialidad_id=especialidad_id)

    pendientes = []
    ruts_procesados = set()
    for contrato in contratos_activos:
        rut = contrato.trabajador.rut
        if rut in ruts_procesados:
            continue
        ruts_procesados.add(rut)
        checklist = get_checklist_trabajador(rut)
        for item in checklist:
            if not item['tipo'].obligatorio:
                continue
            if item['estado'] in ('pendiente', 'vencido'):
                pendientes.append({
                    'nombre': contrato.trabajador.nombre_completo,
                    'rut': rut,
                    'obra': contrato.obra.nombre,
                    'especialidad': contrato.especialidad.nombre,
                    'documento': item['tipo'].nombre,
                    'estado': item['estado'].upper(),
                    'vencimiento': item['doc'].fecha_vencimiento.strftime('%d/%m/%Y') if item['doc'] and item['doc'].fecha_vencimiento else '',
                })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Documentos Pendientes'

    headers = ['Trabajador', 'RUT', 'Obra', 'Especialidad', 'Documento', 'Estado', 'Venció']
    header_fill = PatternFill(start_color='1F2937', end_color='1F2937', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    fill_vencido = PatternFill(start_color='FEE2E2', end_color='FEE2E2', fill_type='solid')
    fill_pendiente = PatternFill(start_color='FEF9C3', end_color='FEF9C3', fill_type='solid')

    for row, p in enumerate(pendientes, 2):
        ws.cell(row=row, column=1, value=p['nombre'])
        ws.cell(row=row, column=2, value=p['rut'])
        ws.cell(row=row, column=3, value=p['obra'])
        ws.cell(row=row, column=4, value=p['especialidad'])
        ws.cell(row=row, column=5, value=p['documento'])
        ws.cell(row=row, column=6, value=p['estado'])
        ws.cell(row=row, column=7, value=p['vencimiento'])
        fill = fill_vencido if p['estado'] == 'VENCIDO' else fill_pendiente
        for col in range(1, 8):
            ws.cell(row=row, column=col).fill = fill

    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="documentos_pendientes.xlsx"'
    return response
