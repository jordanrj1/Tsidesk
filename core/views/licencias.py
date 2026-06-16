from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from ..models import LicenciaMedica, Contrato, Trabajador, Obra, ContratoHistorial


def _registrar_historial(contrato, estado_nuevo, usuario, descripcion=''):
    if contrato.estado != estado_nuevo:
        ContratoHistorial.objects.create(
            contrato=contrato,
            estado_anterior=contrato.estado,
            estado_nuevo=estado_nuevo,
            descripcion=descripcion,
            usuario=usuario,
        )


@login_required
def licencia_list(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    tipo = request.GET.get('tipo', '')
    obra_id = request.GET.get('obra_id', '')

    qs = LicenciaMedica.objects.filter(activo=True).select_related(
        'trabajador', 'contrato', 'obra'
    ).order_by('-fecha_inicio')

    if q:
        qs = qs.filter(
            Q(trabajador__nombres__icontains=q) |
            Q(trabajador__apellidos__icontains=q) |
            Q(trabajador__rut__icontains=q) |
            Q(numero_folio__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if obra_id:
        qs = qs.filter(obra_id=obra_id)

    obras = Obra.objects.filter(activo=True).order_by('nombre')
    return render(request, 'licencias/list.html', {
        'licencias': qs,
        'q': q,
        'estado': estado,
        'tipo': tipo,
        'obra_id': obra_id,
        'estado_choices': LicenciaMedica.ESTADO_CHOICES,
        'tipo_choices': LicenciaMedica.TIPO_CHOICES,
        'obras': obras,
        'hoy': timezone.now().date(),
    })


@login_required
def licencia_create(request):
    """Registrar nueva licencia médica desde cualquier contexto."""
    trabajador_rut = request.GET.get('rut', '') or request.POST.get('trabajador_rut', '')
    contrato_pk = request.GET.get('contrato_id', '') or request.POST.get('contrato_id', '')
    obra_pk = request.GET.get('obra_id', '') or request.POST.get('obra_id', '')

    trabajador = None
    contrato = None
    obra = None
    if trabajador_rut:
        trabajador = Trabajador.objects.filter(rut=trabajador_rut, activo=True).first()
    if contrato_pk:
        contrato = Contrato.objects.filter(pk=contrato_pk, activo=True).first()
        if contrato and not trabajador:
            trabajador = contrato.trabajador
        if contrato and not obra:
            obra = contrato.obra
    if obra_pk:
        obra = Obra.objects.filter(pk=obra_pk, activo=True).first()

    if request.method == 'POST':
        rut = request.POST.get('trabajador_rut', '').strip()
        c_id = request.POST.get('contrato_id', '').strip()
        o_id = request.POST.get('obra_id', '').strip()
        numero_folio = request.POST.get('numero_folio', '').strip()
        tipo = request.POST.get('tipo', '1')
        organismo = request.POST.get('organismo', 'FONASA')
        diagnostico = request.POST.get('diagnostico', '').strip()
        fecha_inicio = request.POST.get('fecha_inicio', '').strip()
        fecha_fin = request.POST.get('fecha_fin', '').strip() or None
        dias_autorizados = int(request.POST.get('dias_autorizados', 0) or 0)
        estado_lic = request.POST.get('estado', 'Presentada')
        empresa_pago = request.POST.get('empresa_pago_3_dias') == 'on'
        monto_esperado = request.POST.get('monto_subsidio_esperado', '').strip() or None
        observaciones = request.POST.get('observaciones', '').strip()

        # Validar fechas
        if fecha_inicio and fecha_fin:
            from datetime import date as _date
            try:
                fi = _date.fromisoformat(str(fecha_inicio))
                ff = _date.fromisoformat(str(fecha_fin))
                if ff < fi:
                    messages.error(request, 'La fecha de fin de licencia no puede ser anterior a la fecha de inicio.')
                    return redirect(request.path + '?' + request.GET.urlencode())
            except ValueError:
                pass
        try:
            trab_obj = Trabajador.objects.get(rut=rut, activo=True)
            cont_obj = Contrato.objects.get(pk=int(c_id), activo=True) if c_id else None
            obra_obj = Obra.objects.get(pk=int(o_id), activo=True) if o_id else (cont_obj.obra if cont_obj else None)

            # Bloquear licencia sobre contrato ya terminado
            if cont_obj and cont_obj.estado in ('Finalizado', 'Rescindido', 'Trasladado'):
                messages.error(
                    request,
                    f'No se puede registrar una licencia para un contrato en estado "{cont_obj.estado}". '
                    f'El contrato debe estar activo.'
                )
                return redirect(request.path + '?' + request.GET.urlencode())

            # Folio único por trabajador (advertencia, no bloqueo si folio está vacío)
            if numero_folio:
                folio_existente = LicenciaMedica.objects.filter(
                    trabajador=trab_obj, numero_folio=numero_folio, activo=True
                ).first()
                if folio_existente:
                    messages.error(
                        request,
                        f'Ya existe una licencia registrada con el folio "{numero_folio}" '
                        f'para este trabajador (Licencia #{folio_existente.pk}, {folio_existente.fecha_inicio}). '
                        f'Verifique que no sea un duplicado.'
                    )
                    return redirect(request.path + '?' + request.GET.urlencode())

            # Advertencia de traslape de fechas para el mismo trabajador
            if fecha_inicio:
                from datetime import date as _date2
                fi_obj = _date2.fromisoformat(str(fecha_inicio))
                ff_obj = _date2.fromisoformat(str(fecha_fin)) if fecha_fin else None
                qs_traslape = LicenciaMedica.objects.filter(
                    trabajador=trab_obj, activo=True, fecha_inicio__lte=(ff_obj or fi_obj)
                )
                if ff_obj:
                    qs_traslape = qs_traslape.filter(
                        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fi_obj)
                    )
                else:
                    qs_traslape = qs_traslape.filter(
                        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fi_obj)
                    )
                if qs_traslape.exists():
                    nombres = ', '.join(
                        f'#{l.pk} ({l.fecha_inicio}–{l.fecha_fin or "en curso"})'
                        for l in qs_traslape[:3]
                    )
                    messages.warning(
                        request,
                        f'Advertencia: el trabajador ya tiene licencia(s) con fechas que se solapan: {nombres}. '
                        f'Verifique que sean licencias distintas antes de continuar. Se ha registrado de todas formas.'
                    )

            # Tipo 2 (accidente laboral) debe ser ACHS, Mutual de Seguridad o IST
            if tipo == '2' and organismo not in ('ACHS', 'Mutual de Seguridad', 'IST'):
                messages.warning(
                    request,
                    'Atención: las licencias por Accidente Laboral / Enfermedad Profesional (Tipo 2) '
                    'deben ser tramitadas a través de ACHS, Mutual de Seguridad o IST. '
                    'El organismo registrado no corresponde a las instituciones habituales para este tipo.'
                )

            institucion_nombre = request.POST.get('institucion_nombre', '').strip()
            lic = LicenciaMedica(
                trabajador=trab_obj,
                contrato=cont_obj,
                obra=obra_obj,
                numero_folio=numero_folio,
                tipo=tipo,
                organismo=organismo,
                institucion_nombre=institucion_nombre,
                diagnostico=diagnostico,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                dias_autorizados=dias_autorizados,
                estado=estado_lic,
                empresa_pago_3_dias=empresa_pago,
                monto_subsidio_esperado=monto_esperado,
                observaciones=observaciones,
                usuario_registro=request.user.username,
            )
            for campo in ('archivo_formulario', 'archivo_resolucion', 'archivo_alta'):
                archivo = request.FILES.get(campo)
                if archivo:
                    setattr(lic, campo, archivo)
            lic.save()

            # Si la licencia cubre el contrato, actualizar estado del contrato
            if cont_obj and cont_obj.estado in ('Vigente', 'Pendiente de Firma'):
                _registrar_historial(cont_obj, 'En Licencia', request.user.username,
                                     f'Licencia #{lic.pk} registrada')
                cont_obj.estado = 'En Licencia'
                cont_obj.fecha_inicio_licencia = lic.fecha_inicio
                cont_obj.save(update_fields=['estado', 'fecha_inicio_licencia'])

            messages.success(request, f'Licencia médica registrada para {trab_obj.nombre_completo}.')
            back = request.POST.get('next', '')
            if back:
                return redirect(back)
            return redirect('licencia_detail', pk=lic.pk)
        except Exception as e:
            messages.error(request, f'Error al registrar licencia: {e}')

    trabajadores = Trabajador.objects.filter(activo=True).order_by('apellidos')
    contratos = []
    if trabajador:
        contratos = Contrato.objects.filter(
            trabajador=trabajador, activo=True
        ).select_related('obra').order_by('-creado_el')

    return render(request, 'licencias/form.html', {
        'trabajador': trabajador,
        'contrato': contrato,
        'obra': obra,
        'trabajadores': trabajadores,
        'contratos': contratos,
        'tipo_choices': LicenciaMedica.TIPO_CHOICES,
        'estado_choices': LicenciaMedica.ESTADO_CHOICES,
        'organismo_choices': LicenciaMedica.ORGANISMO_CHOICES,
        'next': request.GET.get('next', ''),
    })


@login_required
def licencia_detail(request, pk):
    lic = get_object_or_404(LicenciaMedica, pk=pk, activo=True)
    return render(request, 'licencias/detail.html', {'lic': lic})


@login_required
def licencia_edit(request, pk):
    lic = get_object_or_404(LicenciaMedica, pk=pk, activo=True)

    if request.method == 'POST':
        lic.numero_folio = request.POST.get('numero_folio', lic.numero_folio).strip()
        lic.tipo = request.POST.get('tipo', lic.tipo)
        lic.organismo = request.POST.get('organismo', lic.organismo)
        lic.diagnostico = request.POST.get('diagnostico', lic.diagnostico).strip()
        fecha_fin_raw = request.POST.get('fecha_fin', '').strip()
        if fecha_fin_raw:
            from datetime import date as _date
            try:
                fi = lic.fecha_inicio
                ff = _date.fromisoformat(fecha_fin_raw)
                if ff < fi:
                    messages.error(request, 'La fecha de fin no puede ser anterior a la fecha de inicio.')
                    return redirect('licencia_edit', pk=lic.pk)
            except (ValueError, TypeError):
                pass
        lic.fecha_fin = fecha_fin_raw or None
        lic.dias_autorizados = int(request.POST.get('dias_autorizados', lic.dias_autorizados) or 0)
        nuevo_estado = request.POST.get('estado', lic.estado)
        lic.estado = nuevo_estado
        lic.empresa_pago_3_dias = request.POST.get('empresa_pago_3_dias') == 'on'
        monto_esp = request.POST.get('monto_subsidio_esperado', '').strip()
        lic.monto_subsidio_esperado = monto_esp or None
        monto_rec = request.POST.get('monto_subsidio_recibido', '').strip()
        lic.monto_subsidio_recibido = monto_rec or None
        lic.observaciones = request.POST.get('observaciones', lic.observaciones).strip()

        for campo in ('archivo_formulario', 'archivo_resolucion', 'archivo_alta'):
            archivo = request.FILES.get(campo)
            if archivo:
                setattr(lic, campo, archivo)

        lic.save()

        # Si la licencia se marca Autorizada/Rechazada y tiene contrato, verificar reactivación
        if lic.contrato:
            if nuevo_estado == 'Rechazada' and lic.contrato.estado == 'En Licencia':
                _registrar_historial(lic.contrato, 'Vigente', request.user.username,
                                     f'Licencia #{lic.pk} rechazada — reactivación automática')
                lic.contrato.estado = 'Vigente'
                lic.contrato.save(update_fields=['estado'])
                messages.warning(request, 'Licencia rechazada: el contrato fue reactivado a Vigente.')

        messages.success(request, 'Licencia actualizada.')
        return redirect('licencia_detail', pk=lic.pk)

    return render(request, 'licencias/form.html', {
        'lic': lic,
        'edit_mode': True,
        'tipo_choices': LicenciaMedica.TIPO_CHOICES,
        'estado_choices': LicenciaMedica.ESTADO_CHOICES,
        'organismo_choices': LicenciaMedica.ORGANISMO_CHOICES,
    })


@login_required
def licencia_delete(request, pk):
    lic = get_object_or_404(LicenciaMedica, pk=pk, activo=True)
    if request.method == 'POST':
        contrato = lic.contrato
        lic.activo = False
        lic.save()
        # Si el contrato está En Licencia y esta era la única licencia activa, revertir a Vigente
        if contrato and contrato.estado == 'En Licencia':
            otras_activas = LicenciaMedica.objects.filter(
                contrato=contrato, activo=True
            ).exists()
            if not otras_activas:
                _registrar_historial(
                    contrato, 'Vigente', request.user.username,
                    f'Reactivación automática: licencia #{pk} eliminada (era la única activa).'
                )
                contrato.estado = 'Vigente'
                contrato.save(update_fields=['estado'])
                messages.warning(request, 'Licencia eliminada. El contrato fue revertido a Vigente automáticamente.')
            else:
                messages.success(request, 'Licencia eliminada.')
        else:
            messages.success(request, 'Licencia eliminada.')
    return redirect('licencia_list')


@login_required
def licencia_prorroga(request, pk):
    """Registrar prórroga de una licencia existente."""
    if request.method != 'POST':
        return redirect('licencia_detail', pk=pk)
    lic = get_object_or_404(LicenciaMedica, pk=pk, activo=True)

    # No se puede prorrogar una licencia rechazada
    if lic.estado == 'Rechazada':
        messages.error(request, 'No se puede prorrogar una licencia en estado Rechazada.')
        return redirect('licencia_detail', pk=pk)

    nueva_fecha_fin = request.POST.get('nueva_fecha_fin', '').strip()
    dias_extra = int(request.POST.get('dias_extra', 0) or 0)
    obs = request.POST.get('obs', '').strip()

    if not nueva_fecha_fin:
        messages.error(request, 'Debe indicar la nueva fecha de fin.')
        return redirect('licencia_detail', pk=pk)

    if dias_extra <= 0:
        messages.error(request, 'Debe indicar los días adicionales autorizados (mayor a 0).')
        return redirect('licencia_detail', pk=pk)

    # Validar nueva_fecha_fin >= fecha_inicio
    from datetime import date as _date
    try:
        if _date.fromisoformat(nueva_fecha_fin) < lic.fecha_inicio:
            messages.error(request, 'La nueva fecha de fin no puede ser anterior a la fecha de inicio de la licencia.')
            return redirect('licencia_detail', pk=pk)
    except ValueError:
        messages.error(request, 'Fecha inválida.')
        return redirect('licencia_detail', pk=pk)

    lic.fecha_fin = nueva_fecha_fin
    lic.dias_autorizados = lic.dias_autorizados + dias_extra
    lic.estado = 'Prorrogada'
    if obs:
        lic.observaciones = (lic.observaciones + '\nPrórroga: ' + obs).strip()
    lic.save()
    messages.success(request, f'Prórroga registrada hasta {nueva_fecha_fin} (+{dias_extra} días).')
    return redirect('licencia_detail', pk=pk)


@login_required
def licencias_trabajador_ajax(request, rut):
    """AJAX: retorna licencias activas de un trabajador."""
    licencias = LicenciaMedica.objects.filter(
        trabajador_id=rut, activo=True
    ).order_by('-fecha_inicio').values(
        'id', 'tipo', 'estado', 'fecha_inicio', 'fecha_fin', 'dias_autorizados', 'organismo'
    )
    return JsonResponse({'licencias': list(licencias)}, json_dumps_params={'default': str})


# ---------------------------------------------------------------------------
# ConfigRemuneraciones
# ---------------------------------------------------------------------------

@login_required
def config_remuneraciones_list(request):
    from ..models import ConfigRemuneraciones
    configs = ConfigRemuneraciones.objects.all().order_by('-vigente_desde')
    return render(request, 'admin_panel/config_remuneraciones.html', {'configs': configs})


@login_required
def config_remuneraciones_save(request):
    from ..models import ConfigRemuneraciones
    if request.method != 'POST':
        return redirect('config_remuneraciones_list')
    pk = request.POST.get('pk', '').strip()
    obj = ConfigRemuneraciones.objects.get(pk=int(pk)) if pk else ConfigRemuneraciones()
    obj.nombre = request.POST.get('nombre', 'Configuración General')
    obj.vigente_desde = request.POST.get('vigente_desde')
    obj.tasa_afp_empleado = request.POST.get('tasa_afp_empleado', 10.58)
    obj.tasa_salud_empleado = request.POST.get('tasa_salud_empleado', 7.00)
    obj.tasa_cesantia_empleado_plazo_fijo = request.POST.get('tasa_cesantia_empleado_plazo_fijo', 0.60)
    obj.tasa_cesantia_empleado_indefinido = request.POST.get('tasa_cesantia_empleado_indefinido', 0.60)
    obj.tasa_cesantia_empleador = request.POST.get('tasa_cesantia_empleador', 2.40)
    obj.tasa_mutual_accidentes = request.POST.get('tasa_mutual_accidentes', 0.93)
    obj.notas = request.POST.get('notas', '')
    obj.activo = request.POST.get('activo') == 'on'
    obj.save()
    messages.success(request, 'Configuración guardada.')
    return redirect('config_remuneraciones_list')
