from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..models import Obra, BodegaObra, HistorialMaterial, CatalogoMaterial, Trabajador, Contrato
from ..forms import DespachoMaterialForm, IngresoStockForm, AjusteUmbralForm


@login_required
def bodega_index(request):
    obras = Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada'])
    obra_id = request.GET.get('obra_id', '')
    obra = None
    bodega_items = []
    historial = []

    if obra_id:
        obra = get_object_or_404(Obra, pk=obra_id, activo=True)
        bodega_items = BodegaObra.objects.filter(obra=obra).select_related('material').order_by('material__nombre')
        historial = HistorialMaterial.objects.filter(obra=obra).select_related(
            'material', 'trabajador_capataz'
        ).order_by('-fecha_movimiento')[:50]

    context = {
        'obras': obras,
        'obra': obra,
        'obra_id': obra_id,
        'bodega_items': bodega_items,
        'historial': historial,
    }
    return render(request, 'bodega/index.html', context)


@login_required
def bodega_despacho(request, obra_id):
    obra = get_object_or_404(Obra, pk=obra_id, activo=True)
    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        capataz_rut = request.POST.get('capataz_rut')
        cantidad = int(request.POST.get('cantidad', 0))
        observacion = request.POST.get('observacion', '')

        item, _ = BodegaObra.objects.get_or_create(
            obra=obra, material_id=material_id, defaults={'stock_actual': 0}
        )
        if cantidad > item.stock_actual:
            messages.error(request, f'Stock insuficiente. Disponible: {item.stock_actual}')
            return redirect(f'/bodega/?obra_id={obra_id}')

        item.stock_actual -= cantidad
        item.save()

        capataz = None
        if capataz_rut:
            try:
                capataz = Trabajador.objects.get(rut=capataz_rut)
            except Trabajador.DoesNotExist:
                pass

        HistorialMaterial.objects.create(
            obra=obra,
            material_id=material_id,
            trabajador_capataz=capataz,
            cantidad=cantidad,
            tipo_movimiento='ENTREGA_TERRENO',
            observacion=observacion,
            usuario_registro=request.user.username,
        )
        messages.success(request, f'Despacho registrado: {cantidad} unidades entregadas.')
    return redirect(f'/bodega/?obra_id={obra_id}')


@login_required
def bodega_ingreso_stock(request, obra_id):
    obra = get_object_or_404(Obra, pk=obra_id, activo=True)
    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        cantidad = int(request.POST.get('cantidad', 0))
        observacion = request.POST.get('observacion', '')

        item, _ = BodegaObra.objects.get_or_create(
            obra=obra, material_id=material_id, defaults={'stock_actual': 0}
        )
        item.stock_actual += cantidad
        item.save()

        HistorialMaterial.objects.create(
            obra=obra,
            material_id=material_id,
            cantidad=cantidad,
            tipo_movimiento='INGRESO_STOCK',
            observacion=observacion,
            usuario_registro=request.user.username,
        )
        messages.success(request, f'Stock actualizado: +{cantidad} unidades ingresadas.')
    return redirect(f'/bodega/?obra_id={obra_id}')


@login_required
def bodega_ajuste_umbral(request, bodega_item_id):
    item = get_object_or_404(BodegaObra, pk=bodega_item_id)
    if request.method == 'POST':
        nuevo_minimo = int(request.POST.get('stock_minimo', 0))
        item.material.stock_minimo = nuevo_minimo
        item.material.save()
        messages.success(request, f'Umbral actualizado a {nuevo_minimo} para {item.material.nombre}.')
    return redirect(f'/bodega/?obra_id={item.obra_id}')


@login_required
def bodega_capataces_ajax(request, obra_id):
    obra = get_object_or_404(Obra, pk=obra_id)
    contratos = Contrato.objects.filter(
        obra=obra, estado='Vigente', activo=True
    ).select_related('trabajador')
    data = [
        {'rut': c.trabajador.rut, 'nombre': c.trabajador.nombre_completo}
        for c in contratos
    ]
    return JsonResponse({'capataces': data})
