from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..models import Obra, HistorialMaterial, CatalogoMaterial, Trabajador, Contrato


@login_required
def bodega_index(request):
    """Catálogo de materiales e insumos."""
    q = request.GET.get('q', '')
    cat = request.GET.get('cat', '')
    materiales = CatalogoMaterial.objects.filter(activo=True)
    if q:
        materiales = materiales.filter(nombre__icontains=q)
    if cat:
        materiales = materiales.filter(categoria=cat)

    materiales = list(materiales.order_by('categoria', 'nombre'))
    obras_activas = Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada']).order_by('nombre')
    grupos_count = len(set(m.categoria for m in materiales))

    context = {
        'materiales': materiales,
        'obras_activas': obras_activas,
        'categorias': CatalogoMaterial.CATEGORIA_CHOICES,
        'unidades': CatalogoMaterial.UNIDAD_CHOICES,
        'q': q,
        'cat': cat,
        'grupos_count': grupos_count,
    }
    return render(request, 'bodega/index.html', context)


@login_required
def bodega_material_save(request):
    """Crear o editar un material del catálogo."""
    pk = request.POST.get('pk')
    nombre = request.POST.get('nombre', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()
    categoria = request.POST.get('categoria', 'OTROS')
    unidad = request.POST.get('unidad_medida', 'unid')

    if not nombre:
        messages.error(request, 'El nombre del material es obligatorio.')
        return redirect('bodega_index')

    if pk:
        mat = get_object_or_404(CatalogoMaterial, pk=pk)
        mat.nombre = nombre
        mat.descripcion = descripcion
        mat.categoria = categoria
        mat.unidad_medida = unidad
        mat.save()
        messages.success(request, f'Material "{nombre}" actualizado.')
    else:
        if CatalogoMaterial.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe un material con el nombre "{nombre}".')
            return redirect('bodega_index')
        CatalogoMaterial.objects.create(
            nombre=nombre, descripcion=descripcion,
            categoria=categoria, unidad_medida=unidad,
        )
        messages.success(request, f'Material "{nombre}" creado.')
    return redirect('bodega_index')


@login_required
def bodega_material_delete(request, pk):
    """Desactiva (soft-delete) un material del catálogo."""
    mat = get_object_or_404(CatalogoMaterial, pk=pk)
    if request.method == 'POST':
        mat.activo = False
        mat.save()
        messages.success(request, f'Material "{mat.nombre}" eliminado del catálogo.')
    return redirect('bodega_index')


@login_required
def bodega_registrar_entrega(request):
    """Registra la entrega de un material a una obra."""
    if request.method == 'POST':
        obra = get_object_or_404(Obra, pk=request.POST.get('obra_id'), activo=True)
        mat = get_object_or_404(CatalogoMaterial, pk=request.POST.get('material_id'), activo=True)
        cantidad = int(request.POST.get('cantidad', 0))
        receptor_nombre = request.POST.get('receptor_nombre', '').strip()
        obs = request.POST.get('observacion', '').strip()

        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
            return redirect('bodega_index')

        # Try to match free-text receptor to a registered worker by name
        capataz = None
        if receptor_nombre:
            try:
                capataz = Trabajador.objects.get(rut=receptor_nombre, activo=True)
            except Trabajador.DoesNotExist:
                pass

        HistorialMaterial.objects.create(
            obra=obra,
            material=mat,
            trabajador_capataz=capataz,
            receptor_libre=receptor_nombre,
            cantidad=cantidad,
            tipo_movimiento='ENTREGA_TERRENO',
            observacion=obs,
            usuario_registro=request.user.username,
        )
        messages.success(request, f'{cantidad} {mat.get_unidad_medida_display()} de "{mat.nombre}" registrados en {obra.nombre}.')
    return redirect('bodega_index')


@login_required
def bodega_capataces_ajax(request, obra_id):
    obra = get_object_or_404(Obra, pk=obra_id)
    contratos = Contrato.objects.filter(obra=obra, estado='Vigente', activo=True).select_related('trabajador')
    data = [{'rut': c.trabajador.rut, 'nombre': c.trabajador.nombre_completo} for c in contratos]
    return JsonResponse({'capataces': data})


# Compatibilidad con URLs antiguas
@login_required
def bodega_ingreso_central(request):
    return redirect('bodega_index')

@login_required
def bodega_ajuste_umbral(request, bodega_item_id):
    return redirect('bodega_index')

@login_required
def bodega_asignar_obra(request):
    return bodega_registrar_entrega(request)

@login_required
def bodega_despacho(request, obra_id):
    return redirect('bodega_index')

@login_required
def bodega_ingreso_stock(request, obra_id):
    return redirect('bodega_index')
