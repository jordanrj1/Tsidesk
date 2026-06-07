from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from ..models import LogAuditoria, TipoDocumento, Especialidad, CatalogoMaterial, BodegaObra, Obra
from ..forms import (TipoDocumentoForm, EspecialidadForm, CatalogoMaterialForm,
                     UsuarioCreateForm, UsuarioEditForm)


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
@superuser_required
def admin_usuarios(request):
    usuarios = User.objects.all().order_by('username')
    return render(request, 'admin_panel/usuarios.html', {'usuarios': usuarios})


@login_required
@superuser_required
def admin_usuario_create(request):
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('admin_usuarios')
    else:
        form = UsuarioCreateForm()
    return render(request, 'admin_panel/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})


@login_required
@superuser_required
def admin_usuario_edit(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado.')
            return redirect('admin_usuarios')
    else:
        form = UsuarioEditForm(instance=usuario)
    return render(request, 'admin_panel/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario', 'usuario': usuario})


@login_required
@superuser_required
def admin_usuario_toggle(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario != request.user:
        usuario.is_active = not usuario.is_active
        usuario.save()
        estado = 'activado' if usuario.is_active else 'desactivado'
        messages.info(request, f'Usuario {usuario.username} {estado}.')
    return redirect('admin_usuarios')


@login_required
@superuser_required
def admin_catalogos(request):
    tipos_doc = TipoDocumento.objects.all()
    especialidades = Especialidad.objects.all()
    materiales = CatalogoMaterial.objects.all()
    return render(request, 'admin_panel/catalogos.html', {
        'tipos_doc': tipos_doc,
        'especialidades': especialidades,
        'materiales': materiales,
    })


@login_required
@superuser_required
def admin_tipo_documento_save(request):
    pk = request.POST.get('pk')
    if pk:
        obj = get_object_or_404(TipoDocumento, pk=pk)
        form = TipoDocumentoForm(request.POST, instance=obj)
    else:
        form = TipoDocumentoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tipo de documento guardado.')
    else:
        messages.error(request, str(form.errors))
    return redirect('admin_catalogos')


@login_required
@superuser_required
def admin_especialidad_save(request):
    pk = request.POST.get('pk')
    if pk:
        obj = get_object_or_404(Especialidad, pk=pk)
        form = EspecialidadForm(request.POST, instance=obj)
    else:
        form = EspecialidadForm(request.POST)
    if form.is_valid():
        e = form.save()
        messages.success(request, 'Especialidad guardada.')
    else:
        messages.error(request, str(form.errors))
    return redirect('admin_catalogos')


@login_required
@superuser_required
def admin_material_save(request):
    pk = request.POST.get('pk')
    if pk:
        obj = get_object_or_404(CatalogoMaterial, pk=pk)
        form = CatalogoMaterialForm(request.POST, instance=obj)
    else:
        form = CatalogoMaterialForm(request.POST)
    if form.is_valid():
        mat = form.save()
        # Crear entrada en bodega para obras activas
        for obra in Obra.objects.filter(activo=True, estado__in=['Activa', 'Pausada']):
            BodegaObra.objects.get_or_create(obra=obra, material=mat, defaults={'stock_actual': 0})
        messages.success(request, 'Material guardado.')
    else:
        messages.error(request, str(form.errors))
    return redirect('admin_catalogos')


@login_required
@superuser_required
def admin_auditoria(request):
    tabla = request.GET.get('tabla', '')
    usuario = request.GET.get('usuario', '')
    qs = LogAuditoria.objects.all()
    if tabla:
        qs = qs.filter(tabla_afectada__icontains=tabla)
    if usuario:
        qs = qs.filter(usuario__icontains=usuario)
    logs = qs.order_by('-fecha_hora')[:200]
    return render(request, 'admin_panel/auditoria.html', {
        'logs': logs, 'tabla': tabla, 'usuario': usuario
    })
