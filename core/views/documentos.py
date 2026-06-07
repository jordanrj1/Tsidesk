import io, zipfile, os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from ..models import (Documento, Trabajador, Obra, Contrato, TipoDocumento,
                      Especialidad, get_checklist_trabajador)


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

    # Checklist en vivo: agrupa por RUT para no repetir si el trabajador está en varias obras
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
                    'trabajador': contrato.trabajador,
                    'obra': contrato.obra,
                    'especialidad': contrato.especialidad,
                    'tipo_documento': item['tipo'],
                    'contrato': contrato,
                    'estado_doc': item['estado'],
                    'doc': item['doc'],  # El doc vencido (si existe)
                })

    obras = Obra.objects.filter(activo=True)
    especialidades = Especialidad.objects.filter(activo=True)

    context = {
        'pendientes': pendientes,
        'obras': obras,
        'especialidades': especialidades,
        'obra_id': obra_id,
        'especialidad_id': especialidad_id,
        'total': len(pendientes),
    }
    return render(request, 'documentos/pendientes.html', context)


@login_required
def documento_download(request, pk):
    doc = get_object_or_404(Documento, pk=pk, activo=True)
    response = HttpResponse(doc.archivo, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.nombre_archivo}"'
    return response


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
    """Centro de documentos: todos los documentos con filtros cruzados."""
    from django.db.models import Q

    obra_id = request.GET.get('obra_id', '')
    especialidad_id = request.GET.get('especialidad_id', '')
    tipo_id = request.GET.get('tipo_id', '')
    estado_filter = request.GET.get('estado', '')
    q = request.GET.get('q', '')  # search by worker name/rut

    qs = Documento.objects.filter(activo=True).select_related(
        'tipo_documento', 'contrato', 'contrato__obra',
        'contrato__trabajador', 'contrato__especialidad'
    ).order_by('-fecha_carga')

    if q:
        qs = qs.filter(
            Q(trabajador_rut__icontains=q) |
            Q(contrato__trabajador__nombres__icontains=q) |
            Q(contrato__trabajador__apellidos__icontains=q)
        )
    if tipo_id:
        qs = qs.filter(tipo_documento_id=tipo_id)
    if obra_id:
        qs = qs.filter(
            Q(obra_id=obra_id) | Q(contrato__obra_id=obra_id)
        )
    if especialidad_id:
        qs = qs.filter(contrato__especialidad_id=especialidad_id)

    # Aplicar filtro de estado
    docs_list = list(qs[:200])
    if estado_filter:
        docs_list = [d for d in docs_list if d.estado_visual == estado_filter]

    from ..models import Obra, Especialidad, TipoDocumento
    context = {
        'documentos': docs_list,
        'obras': Obra.objects.filter(activo=True),
        'especialidades': Especialidad.objects.filter(activo=True),
        'tipos': TipoDocumento.objects.filter(activo=True),
        'obra_id': obra_id,
        'especialidad_id': especialidad_id,
        'tipo_id': tipo_id,
        'estado_filter': estado_filter,
        'q': q,
        'total': len(docs_list),
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
