import io, zipfile, os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q
from ..models import (Obra, Contrato, Documento, CierreMensual,
                      BodegaObra, CatalogoMaterial, TipoDocumento)
from ..forms import ObraForm


@login_required
def obras_list(request):
    from datetime import timedelta
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    proximas_cierre = request.GET.get('proximas_cierre', '')
    qs = Obra.objects.filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(constructora_mandante__icontains=q))
    if estado:
        qs = qs.filter(estado=estado)
    if proximas_cierre:
        hoy = timezone.now().date()
        limite_30 = hoy + timedelta(days=30)
        qs = qs.filter(estado='Activa', fecha_termino_estimada__gte=hoy, fecha_termino_estimada__lte=limite_30)
    context = {'obras': qs, 'q': q, 'estado': estado, 'proximas_cierre': proximas_cierre}
    return render(request, 'obras/list.html', context)


@login_required
def obra_create(request):
    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            obra = form.save()
            # Inicializar bodega para todos los materiales activos
            for mat in CatalogoMaterial.objects.filter(activo=True):
                BodegaObra.objects.get_or_create(obra=obra, material=mat, defaults={'stock_actual': 0})
            messages.success(request, f'Obra "{obra.nombre}" creada exitosamente.')
            return redirect('obra_detail', pk=obra.pk)
    else:
        form = ObraForm()
    return render(request, 'obras/form.html', {'form': form, 'titulo': 'Nueva Obra'})


@login_required
def obra_edit(request, pk):
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    if request.method == 'POST':
        form = ObraForm(request.POST, instance=obra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Obra actualizada correctamente.')
            return redirect('obra_detail', pk=pk)
    else:
        form = ObraForm(instance=obra)
    return render(request, 'obras/form.html', {'form': form, 'titulo': 'Editar Obra', 'obra': obra})


@login_required
def obra_detail(request, pk):
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    tab = request.GET.get('tab', 'resumen')
    contratos = obra.contratos.filter(activo=True).select_related('trabajador', 'especialidad').order_by('-creado_el')
    documentos = Documento.objects.filter(obra=obra, activo=True).select_related('tipo_documento')
    bodega = obra.bodega_items.all().select_related('material').order_by('material__nombre')
    cierres = obra.cierres_mensuales.all().order_by('-anio', '-mes')

    # Documentos de trabajadores activos en la obra (para carpeta mandante)
    docs_trabajadores = Documento.objects.filter(
        Q(trabajador_rut__in=contratos.filter(estado='Vigente').values_list('trabajador_id', flat=True)) |
        Q(contrato__in=contratos),
        activo=True
    ).select_related('tipo_documento', 'contrato').order_by('trabajador_rut', 'tipo_documento__nombre')

    context = {
        'obra': obra,
        'contratos': contratos,
        'documentos': documentos,
        'docs_trabajadores': docs_trabajadores,
        'bodega': bodega,
        'cierres': cierres,
        'tab': tab,
    }
    return render(request, 'obras/detail.html', context)


@login_required
def obra_cierre_check(request, pk):
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    contratos_vigentes = obra.contratos.filter(estado='Vigente', activo=True).count()
    contratos_finalizados = obra.contratos.filter(estado='Finalizado', activo=True)

    sin_finiquito = 0
    for c in contratos_finalizados:
        tiene = Documento.objects.filter(
            contrato=c,
            tipo_documento__nombre__icontains='finiquito',
            activo=True
        ).exists()
        if not tiene:
            sin_finiquito += 1

    puede_cerrar = contratos_vigentes == 0 and sin_finiquito == 0
    return JsonResponse({
        'contratos_vigentes': contratos_vigentes,
        'sin_finiquito': sin_finiquito,
        'puede_cerrar': puede_cerrar,
    })


@login_required
def obra_cerrar(request, pk):
    if request.method == 'POST':
        obra = get_object_or_404(Obra, pk=pk, activo=True)
        contratos_vigentes = obra.contratos.filter(estado='Vigente', activo=True).count()

        finalizados = obra.contratos.filter(estado='Finalizado', activo=True)
        sin_finiquito = sum(
            1 for c in finalizados
            if not Documento.objects.filter(
                contrato=c, tipo_documento__nombre__icontains='finiquito', activo=True
            ).exists()
        )

        if contratos_vigentes > 0 or sin_finiquito > 0:
            messages.error(request, 'No se puede cerrar la obra. Revise los pendientes.')
            return redirect('obra_detail', pk=pk)

        obra.estado = 'Cerrada'
        obra.fecha_termino_real = timezone.now().date()
        obra.save()
        messages.success(request, f'Obra "{obra.nombre}" cerrada exitosamente.')
    return redirect('obras_list')


@login_required
def obra_download_zip(request, pk):
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    docs = Documento.objects.filter(
        Q(obra=obra) |
        Q(contrato__obra=obra) |
        Q(trabajador_rut__in=Contrato.objects.filter(obra=obra).values_list('trabajador_id', flat=True)),
        activo=True
    ).select_related('tipo_documento')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.archivo and os.path.exists(doc.archivo.path):
                if doc.contrato:
                    folder = f"trabajadores/{doc.contrato.trabajador.rut}"
                elif doc.trabajador_rut:
                    folder = f"trabajadores/{doc.trabajador_rut}"
                else:
                    folder = "obra"
                arcname = f"{folder}/{doc.tipo_documento.nombre}_{doc.nombre_archivo}"
                zf.write(doc.archivo.path, arcname)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    nombre_obra = obra.nombre.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="obra_{nombre_obra}.zip"'
    return response


@login_required
def obra_cierre_mensual(request, pk):
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    if request.method == 'POST':
        mes = int(request.POST.get('mes'))
        anio = int(request.POST.get('anio'))
        if CierreMensual.objects.filter(obra=obra, mes=mes, anio=anio).exists():
            messages.warning(request, f'El cierre {mes}/{anio} ya fue realizado.')
        else:
            cierre = CierreMensual(obra=obra, mes=mes, anio=anio, usuario_cierre=request.user.username)
            if request.FILES.get('archivo_consolidado'):
                cierre.archivo_consolidado = request.FILES['archivo_consolidado']
            cierre.save()
            messages.success(request, f'Cierre {mes}/{anio} ejecutado para {obra.nombre}.')
    return redirect('obra_detail', pk=pk)


@login_required
def obra_cierre_dotacion_ajax(request, pk):
    """AJAX: retorna la dotación activa de la obra para mostrar en el preview del cierre mensual."""
    obra = get_object_or_404(Obra, pk=pk, activo=True)
    from django.db.models import Count
    contratos = Contrato.objects.filter(
        obra=obra, estado='Vigente', activo=True
    ).select_related('trabajador', 'especialidad')

    # Detectar trabajadores en otras obras
    dotacion = []
    for c in contratos:
        otras_obras = Contrato.objects.filter(
            trabajador=c.trabajador, estado='Vigente', activo=True
        ).exclude(obra=obra).select_related('obra')
        dotacion.append({
            'nombre': c.trabajador.nombre_completo,
            'rut': c.trabajador.rut,
            'especialidad': c.especialidad.nombre,
            'otras_obras': [oc.obra.nombre for oc in otras_obras],
        })

    return JsonResponse({'dotacion': dotacion, 'total': len(dotacion)})
