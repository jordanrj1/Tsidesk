from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from ..models import Contrato, Trabajador, Obra, Documento, TipoDocumento
from ..forms import ContratoForm, ContratoEditForm, DocumentoForm


@login_required
def contratos_list(request):
    from datetime import timedelta
    q = request.GET.get('q', '')
    obra_id = request.GET.get('obra_id', '')
    estado = request.GET.get('estado', '')
    multiples = request.GET.get('multiples', '')
    especialidad_id = request.GET.get('especialidad_id', '')
    vence_pronto = request.GET.get('vence_pronto', '')
    sin_finiquito = request.GET.get('sin_finiquito', '')

    qs = Contrato.objects.filter(activo=True).select_related('trabajador', 'obra', 'especialidad')

    if q:
        qs = qs.filter(
            Q(trabajador__nombres__icontains=q) |
            Q(trabajador__apellidos__icontains=q) |
            Q(trabajador__rut__icontains=q)
        )
    if obra_id:
        qs = qs.filter(obra_id=obra_id)
    if estado:
        qs = qs.filter(estado=estado)
    if especialidad_id:
        qs = qs.filter(especialidad_id=especialidad_id)
    if multiples:
        from django.db.models import Count
        ruts_multiples = (
            Contrato.objects.filter(estado='Vigente', activo=True)
            .values('trabajador')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
            .values_list('trabajador', flat=True)
        )
        qs = qs.filter(trabajador__in=ruts_multiples, estado='Vigente')
    if vence_pronto:
        hoy = timezone.now().date()
        limite = hoy + timedelta(days=10)
        qs = qs.filter(estado='Vigente', fecha_termino_estimada__gte=hoy, fecha_termino_estimada__lte=limite)
    if sin_finiquito:
        finalizados = Contrato.objects.filter(estado='Finalizado', activo=True)
        ids_sin_finiquito = [
            c.pk for c in finalizados
            if not Documento.objects.filter(
                contrato=c, tipo_documento__nombre__icontains='finiquito', activo=True
            ).exists()
        ]
        qs = Contrato.objects.filter(pk__in=ids_sin_finiquito, activo=True).select_related('trabajador', 'obra', 'especialidad')

    from ..models import Obra, Especialidad
    obras = Obra.objects.filter(activo=True)
    especialidades = Especialidad.objects.filter(activo=True)

    context = {
        'contratos': qs.order_by('-creado_el'),
        'q': q,
        'obra_id': obra_id,
        'estado': estado,
        'multiples': multiples,
        'especialidad_id': especialidad_id,
        'obras': obras,
        'especialidades': especialidades,
        'vence_pronto': vence_pronto,
        'sin_finiquito': sin_finiquito,
    }
    return render(request, 'contratos/list.html', context)


@login_required
def contrato_check_duplicado(request):
    trabajador_id = request.GET.get('trabajador_id', '')
    obra_id = request.GET.get('obra_id', '')
    if not trabajador_id or not obra_id:
        return JsonResponse({'duplicado': False})
    existe = Contrato.objects.filter(
        trabajador_id=trabajador_id, obra_id=obra_id,
        estado='Vigente', activo=True
    ).exists()
    return JsonResponse({'duplicado': existe})


@login_required
def contrato_create(request):
    trabajador_rut = request.GET.get('trabajador_rut', '')
    obra_id = request.GET.get('obra_id', '')

    if request.method == 'POST':
        form = ContratoForm(request.POST, trabajador_rut=trabajador_rut, obra_id=obra_id)
        if form.is_valid():
            contrato = form.save(commit=False)
            contrato.estado = 'Pendiente de Firma'
            contrato.save()
            messages.success(request, f'Contrato #{contrato.pk} generado. Estado: Pendiente de Firma.')
            return redirect('contrato_wizard', pk=contrato.pk)
    else:
        form = ContratoForm(trabajador_rut=trabajador_rut, obra_id=obra_id)

    # Contratos activos del trabajador en otras obras + documentos pendientes
    trabajador = None
    contratos_activos = []
    if trabajador_rut:
        try:
            trabajador = Trabajador.objects.get(rut=trabajador_rut)
            contratos_activos = (
                Contrato.objects
                .filter(trabajador=trabajador, activo=True)
                .exclude(estado__in=['Finalizado', 'Rescindido'])
                .select_related('obra')
                .order_by('-creado_el')
            )
            # Anotar documentos pendientes por contrato
            for c in contratos_activos:
                docs_pendientes = []
                tiene_finiquito = Documento.objects.filter(
                    contrato=c, tipo_documento__nombre__icontains='finiquito', activo=True
                ).exists()
                if not tiene_finiquito:
                    docs_pendientes.append('Finiquito')
                c.docs_pendientes = docs_pendientes
        except Trabajador.DoesNotExist:
            pass

    obra_obj = None
    if obra_id:
        try:
            obra_obj = Obra.objects.get(pk=obra_id)
        except Obra.DoesNotExist:
            pass

    context = {
        'form': form,
        'trabajador': trabajador,
        'contratos_activos': contratos_activos,
        'obra_id': obra_id,
        'obra_obj': obra_obj,
    }
    return render(request, 'contratos/form.html', context)


@login_required
def contrato_wizard(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk, activo=True)
    return render(request, 'contratos/wizard.html', {'contrato': contrato})


@login_required
def contrato_edit(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk, activo=True)
    if request.method == 'POST':
        form = ContratoEditForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contrato actualizado.')
            return redirect('contratos_list')
    else:
        form = ContratoEditForm(instance=contrato)
    return render(request, 'contratos/edit.html', {'form': form, 'contrato': contrato})


@login_required
def contrato_upload_firmado(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk, activo=True)
    if request.method == 'POST':
        tipo_contrato = TipoDocumento.objects.filter(nombre__icontains='contrato', nivel='Contrato').first()
        if not tipo_contrato:
            tipo_contrato, _ = TipoDocumento.objects.get_or_create(
                nombre='Contrato de Trabajo Firmado', defaults={'nivel': 'Contrato', 'obligatorio': True}
            )
        archivo = request.FILES.get('archivo')
        if archivo:
            Documento.objects.filter(contrato=contrato, tipo_documento=tipo_contrato, activo=True).update(activo=False)
            Documento.objects.create(
                tipo_documento=tipo_contrato,
                contrato=contrato,
                archivo=archivo,
                usuario_carga=request.user.username,
            )
            contrato.estado = 'Vigente'
            contrato.save()
            messages.success(request, 'Contrato firmado cargado. Estado actualizado a Vigente.')
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'No se recibió archivo'})
    return HttpResponse(status=405)


def _monto_en_palabras(n):
    """Convert integer to Spanish words for Chilean peso amounts."""
    n = int(n)
    if n == 0:
        return 'cero'
    UNO = ['', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve',
           'diez', 'once', 'doce', 'trece', 'catorce', 'quince',
           'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve',
           'veinte', 'veintiún', 'veintidós', 'veintitrés', 'veinticuatro',
           'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho', 'veintinueve']
    DEC = ['', '', '', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    CEN = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos',
           'seiscientos', 'setecientos', 'ochocientos', 'novecientos']

    def _bajo_mil(x):
        if x < 30:
            return UNO[x]
        elif x < 100:
            d, u = divmod(x, 10)
            return DEC[d] + (' y ' + UNO[u] if u else '')
        elif x == 100:
            return 'cien'
        else:
            c, r = divmod(x, 100)
            return CEN[c] + (' ' + _bajo_mil(r) if r else '')

    partes = []
    if n >= 1_000_000:
        m, n = divmod(n, 1_000_000)
        partes.append('un millón' if m == 1 else _bajo_mil(m) + ' millones')
    if n >= 1_000:
        t, n = divmod(n, 1_000)
        partes.append('mil' if t == 1 else _bajo_mil(t) + ' mil')
    if n > 0:
        partes.append(_bajo_mil(n))
    return ' '.join(partes)


CIUDADES_VIII = [
    'Concepción', 'Talcahuano', 'Chiguayante', 'Hualpén', 'San Pedro de la Paz',
    'Coronel', 'Lota', 'Hualqui', 'Penco', 'Tomé', 'Florida', 'Santa Juana',
    'Yumbel', 'Chillán', 'Chillán Viejo', 'Los Ángeles', 'Lebu', 'Cañete',
    'Arauco', 'Curanilahue', 'Tirúa', 'Nacimiento', 'Negrete', 'Mulchén',
    'Cabrero', 'Laja', 'San Rosendo', 'Yungay', 'Coihueco',
]


@login_required
def contrato_pdf(request, pk):
    from ..models import ConfigEmpresa
    import datetime as dt
    contrato = get_object_or_404(Contrato, pk=pk, activo=True)

    ciudad = request.GET.get('ciudad', '').strip()
    fecha_str = request.GET.get('fecha_doc', '').strip()

    # If params not yet provided, show the config form first
    if not ciudad or not fecha_str:
        return render(request, 'contratos/pdf_config.html', {
            'contrato': contrato,
            'ciudades': CIUDADES_VIII,
            'fecha_hoy': contrato.fecha_inicio.strftime('%Y-%m-%d'),
        })

    # Parse fecha_doc (type=date sends YYYY-MM-DD)
    try:
        fecha_doc = dt.date.fromisoformat(fecha_str)
    except ValueError:
        fecha_doc = contrato.fecha_inicio

    # Prefer empresa linked to obra, fall back to first active
    empresa = (contrato.obra.empresa
               if contrato.obra and contrato.obra.empresa
               else ConfigEmpresa.objects.filter(activo=True).first())
    sueldo = int(contrato.sueldo_base)
    sueldo_formateado = f"{sueldo:,}".replace(",", ".")
    sueldo_palabras = _monto_en_palabras(sueldo).capitalize()

    return render(request, 'contratos/pdf_preview.html', {
        'contrato': contrato,
        'empresa': empresa,
        'sueldo_formateado': sueldo_formateado,
        'sueldo_palabras': sueldo_palabras,
        'ciudad_doc': ciudad,
        'fecha_doc': fecha_doc,
    })
