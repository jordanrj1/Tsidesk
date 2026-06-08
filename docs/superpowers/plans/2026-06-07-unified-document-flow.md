# Unified Document Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidar la creación de contratos en el flujo "Generar Documento", actualizar la navegación del sidebar, y mejorar la página de búsqueda de documentos.

**Architecture:** Se crea `ContratoTrabajoCreateForm` que extiende `ContratoTrabajoForm` con campos de la Sección A (obra, especialidad, sueldo, tipo, fechas). El view `doc_generado_create` detecta `tipo=contrato_trabajo` y usa este formulario combinado, creando tanto un `Contrato` como un `DocumentoGenerado` en una sola transacción. El sidebar y la lista de contratos se simplifican.

**Tech Stack:** Django 4.2, Bootstrap 5, Python 3.13, SQLite

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `templates/base.html` | Modify | Sidebar: renombrar "Contratos" → "Buscar Documentos", dividir "Generar Documentos" en dos ítems |
| `templates/contratos/list.html` | Modify | Eliminar botón "Nuevo Contrato" |
| `core/forms.py` | Modify | Agregar `ContratoTrabajoCreateForm` con campos Sección A |
| `core/views/documentos_generados.py` | Modify | `doc_generado_create`: usar form combinado para contrato_trabajo; `doc_generado_list`: agregar filtros fecha/empresa/obra |
| `templates/documentos_generados/form.html` | Modify | Mostrar Sección A cuando tipo=contrato_trabajo y no es edit_mode |
| `templates/documentos_generados/list.html` | Modify | Filtros mejorados (fecha desde/hasta, empresa, obra), acciones con tooltips |

---

## Task 1: Sidebar y lista de contratos

**Files:**
- Modify: `templates/base.html:64-65` y `84-85`
- Modify: `templates/contratos/list.html:7`

- [ ] **Step 1.1: Actualizar sidebar en base.html**

Reemplazar el bloque de "Contratos" (línea 64-65) y "Generar Documentos" (línea 84-85):

```html
<!-- ANTES (línea 64-65): -->
<a class="nav-link text-white {% if 'contratos' in request.resolver_match.url_name %}active bg-primary rounded{% endif %}" href="{% url 'contratos_list' %}">
  <i class="bi bi-file-earmark-text-fill me-2"></i>Contratos

<!-- DESPUÉS — eliminar ese bloque completo (las 2 líneas del anchor de Contratos) -->
<!-- NO hay reemplazo: el ítem "Contratos" desaparece del sidebar -->
```

```html
<!-- ANTES (línea 84-85): -->
<a class="nav-link text-white {% if 'doc_generado' in request.resolver_match.url_name %}active bg-primary rounded{% endif %}" href="{% url 'doc_generado_list' %}">
  <i class="bi bi-file-earmark-ruled-fill me-2"></i>Generar Documentos

<!-- DESPUÉS — reemplazar con DOS ítems: -->
<a class="nav-link text-white {% if request.resolver_match.url_name == 'doc_generado_create' %}active bg-primary rounded{% endif %}" href="{% url 'doc_generado_create' %}">
  <i class="bi bi-file-earmark-plus me-2"></i>Generar Documento
</a>
<a class="nav-link text-white {% if request.resolver_match.url_name == 'doc_generado_list' %}active bg-primary rounded{% endif %}" href="{% url 'doc_generado_list' %}">
  <i class="bi bi-search me-2"></i>Buscar Documentos
</a>
```

- [ ] **Step 1.2: Eliminar botón "Nuevo Contrato" de contratos/list.html**

Eliminar la línea 7 completa:
```html
<!-- Eliminar esta línea: -->
<a href="{% url 'contrato_create' %}" class="btn btn-primary"><i class="bi bi-plus-circle-fill me-1"></i>Nuevo Contrato</a>
```

- [ ] **Step 1.3: Verificar manualmente**

Abrir http://localhost:8000 y confirmar:
- Sidebar ya NO muestra "Contratos"
- Sidebar muestra "Generar Documento" y "Buscar Documentos"
- La lista en /contratos/ ya no tiene botón "Nuevo Contrato"

- [ ] **Step 1.4: Commit**

```bash
git add templates/base.html templates/contratos/list.html
git commit -m "feat: remove Nuevo Contrato button and update sidebar navigation"
```

---

## Task 2: ContratoTrabajoCreateForm con Sección A

**Files:**
- Modify: `core/forms.py` — agregar clase al final del archivo, antes de los choices

- [ ] **Step 2.1: Agregar ContratoTrabajoCreateForm en forms.py**

Buscar la clase `ContratoTrabajoForm` en forms.py (alrededor de línea 350-400) y agregar la nueva clase DEBAJO de ella:

```python
class ContratoTrabajoCreateForm(ContratoTrabajoForm):
    """
    Extends ContratoTrabajoForm with Section A fields that create the Contrato record.
    Only used during initial creation (not edit).
    """
    # ── Sección A: datos del Contrato ──────────────────────────────
    obra_contrato = forms.ModelChoiceField(
        queryset=None,  # set in __init__
        label='Obra',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    especialidad_contrato = forms.ModelChoiceField(
        queryset=None,  # set in __init__
        label='Especialidad / Labor',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    tipo_contrato = forms.ChoiceField(
        choices=[('Plazo Fijo', 'Plazo Fijo'),
                 ('Por Obra o Faena', 'Por Obra o Faena'),
                 ('Indefinido', 'Indefinido')],
        label='Tipo de Contrato',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    sueldo_base = forms.DecimalField(
        label='Sueldo Base',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
    )
    fecha_inicio_contrato = forms.DateField(
        label='Fecha de Inicio',
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'}),
    )
    fecha_termino_contrato = forms.DateField(
        label='Fecha de Término Estimada',
        input_formats=['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'],
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa (opcional)'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Obra, Especialidad
        self.fields['obra_contrato'].queryset = Obra.objects.filter(
            activo=True, estado__in=['Activa', 'Pausada']
        )
        self.fields['especialidad_contrato'].queryset = Especialidad.objects.filter(activo=True)
```

- [ ] **Step 2.2: Verificar que no hay errores de importación**

```bash
cd c:\Users\usuario\Desktop\TsDesk\Tsidesk
python manage.py check
```

Salida esperada: `System check identified no issues (0 silenced).`

- [ ] **Step 2.3: Commit**

```bash
git add core/forms.py
git commit -m "feat: add ContratoTrabajoCreateForm with Section A contract fields"
```

---

## Task 3: Actualizar view y template de creación

**Files:**
- Modify: `core/views/documentos_generados.py` — `doc_generado_create` (líneas ~95-220)
- Modify: `templates/documentos_generados/form.html` — agregar Sección A

- [ ] **Step 3.1: Agregar import de ContratoTrabajoCreateForm en documentos_generados.py**

En la línea de imports del archivo (líneas 7-8), agregar `ContratoTrabajoCreateForm`:

```python
from ..forms import (ConfigEmpresaForm, ContratoTrabajoForm, ContratoTrabajoCreateForm,
                     AnexoContratoForm, FiniquitoForm, PactoHorasExtrasForm,
                     ActaEPPForm, ActaReglamentoForm)
```

- [ ] **Step 3.2: Actualizar doc_generado_create para usar el form combinado**

Localizar en `doc_generado_create` el bloque `if request.method == 'POST':` (alrededor de línea 176). Reemplazar todo el bloque POST+GET del método por este código:

```python
    if request.method == 'POST':
        # Para contrato_trabajo usamos el form combinado con Sección A
        if tipo == 'contrato_trabajo':
            form = ContratoTrabajoCreateForm(request.POST)
        else:
            form = FormClass(request.POST)

        empresa_id = request.POST.get('empresa_id')
        trabajador_rut_post = request.POST.get('trabajador_rut_post', trabajador_rut)

        if form.is_valid() and empresa_id and trabajador_rut_post:
            try:
                empresa = ConfigEmpresa.objects.get(pk=empresa_id)
                trab = Trabajador.objects.get(rut=trabajador_rut_post)
            except (ConfigEmpresa.DoesNotExist, Trabajador.DoesNotExist):
                messages.error(request, 'Empresa o trabajador no válidos.')
                return redirect(request.path + f'?tipo={tipo}')

            if tipo == 'contrato_trabajo':
                # Crear Contrato desde Sección A
                cd = form.cleaned_data
                contrato = Contrato.objects.create(
                    trabajador=trab,
                    obra=cd['obra_contrato'],
                    especialidad=cd['especialidad_contrato'],
                    tipo_contrato=cd['tipo_contrato'],
                    sueldo_base=cd['sueldo_base'],
                    fecha_inicio=cd['fecha_inicio_contrato'],
                    fecha_termino_estimada=cd.get('fecha_termino_contrato'),
                    estado='Pendiente de Firma',
                )
                # Datos del documento (excluir campos de Sección A)
                seccion_a_keys = {'obra_contrato', 'especialidad_contrato', 'tipo_contrato',
                                  'sueldo_base', 'fecha_inicio_contrato', 'fecha_termino_contrato'}
                doc_datos = _serializable({k: v for k, v in cd.items() if k not in seccion_a_keys})
                doc = DocumentoGenerado(
                    tipo=tipo,
                    empresa=empresa,
                    trabajador=trab,
                    contrato=contrato,
                    obra=contrato.obra,
                    datos=doc_datos,
                    usuario=request.user.username,
                )
            else:
                doc = DocumentoGenerado(
                    tipo=tipo,
                    empresa=empresa,
                    trabajador=trab,
                    datos=_serializable(form.cleaned_data),
                    usuario=request.user.username,
                )
                obra_id_post = request.POST.get('obra_id_post', obra_id)
                contrato_id_post = request.POST.get('contrato_id_post', contrato_id)
                if obra_id_post:
                    try:
                        doc.obra = Obra.objects.get(pk=obra_id_post)
                    except Obra.DoesNotExist:
                        pass
                if contrato_id_post:
                    try:
                        doc.contrato = Contrato.objects.get(pk=contrato_id_post)
                    except Contrato.DoesNotExist:
                        pass

            doc.save()
            messages.success(request, f'{label} creado y guardado.')
            return redirect('doc_generado_preview', pk=doc.pk)
        else:
            if not empresa_id:
                messages.error(request, 'Debe seleccionar una empresa.')
            if not trabajador_rut_post:
                messages.error(request, 'Debe seleccionar un trabajador.')
    else:
        if tipo == 'contrato_trabajo':
            form = ContratoTrabajoCreateForm(initial=initial)
        else:
            form = FormClass(initial=initial)
```

Asegurarse que `Contrato` está importado al inicio del archivo:
```python
from ..models import ConfigEmpresa, DocumentoGenerado, Trabajador, Obra, Contrato
```

- [ ] **Step 3.3: Agregar Sección A al template form.html**

En `templates/documentos_generados/form.html`, DESPUÉS del bloque "Datos de Asociación" (el card con empresa/trabajador), agregar la Sección A. Insertar ANTES de la línea `{% if contrato_obj and tipo == 'contrato_trabajo' %}`:

```html
{% if tipo == 'contrato_trabajo' and not edit_mode %}
<!-- ── Sección A: Datos del Contrato ── -->
<div class="card border-0 shadow-sm mb-3" style="border-left: 4px solid #0d6efd !important;">
  <div class="card-header bg-primary text-white fw-semibold">
    <i class="bi bi-file-earmark-text me-2"></i>Datos del Contrato
    <small class="fw-normal ms-2 opacity-75">Se creará el registro laboral en el sistema</small>
  </div>
  <div class="card-body">
    <div class="row g-3">
      <div class="col-md-4">
        <label class="form-label fw-semibold">Obra <span class="text-danger">*</span></label>
        {{ form.obra_contrato }}
        {% if form.obra_contrato.errors %}<div class="text-danger small">{{ form.obra_contrato.errors }}</div>{% endif %}
      </div>
      <div class="col-md-4">
        <label class="form-label fw-semibold">Especialidad / Labor <span class="text-danger">*</span></label>
        {{ form.especialidad_contrato }}
        {% if form.especialidad_contrato.errors %}<div class="text-danger small">{{ form.especialidad_contrato.errors }}</div>{% endif %}
      </div>
      <div class="col-md-4">
        <label class="form-label fw-semibold">Tipo de Contrato <span class="text-danger">*</span></label>
        {{ form.tipo_contrato }}
        {% if form.tipo_contrato.errors %}<div class="text-danger small">{{ form.tipo_contrato.errors }}</div>{% endif %}
      </div>
      <div class="col-md-4">
        <label class="form-label fw-semibold">Sueldo Base <span class="text-danger">*</span></label>
        <div class="input-group">
          <span class="input-group-text">$</span>
          {{ form.sueldo_base }}
        </div>
        {% if form.sueldo_base.errors %}<div class="text-danger small">{{ form.sueldo_base.errors }}</div>{% endif %}
      </div>
      <div class="col-md-4">
        <label class="form-label fw-semibold">Fecha de Inicio <span class="text-danger">*</span></label>
        {{ form.fecha_inicio_contrato }}
        {% if form.fecha_inicio_contrato.errors %}<div class="text-danger small">{{ form.fecha_inicio_contrato.errors }}</div>{% endif %}
      </div>
      <div class="col-md-4">
        <label class="form-label fw-semibold">Fecha de Término <small class="text-muted fw-normal">(opcional)</small></label>
        {{ form.fecha_termino_contrato }}
        {% if form.fecha_termino_contrato.errors %}<div class="text-danger small">{{ form.fecha_termino_contrato.errors }}</div>{% endif %}
      </div>
    </div>
  </div>
</div>
{% endif %}
```

También en el bloque "Datos de Asociación", cuando `tipo == 'contrato_trabajo'` y no es edit_mode, **ocultar el campo Obra** (ya está en Sección A). Localizar el bloque `<div class="col-md-4">` que contiene `name="obra_id_post"` y envolverlo:

```html
{% if not tipo == 'contrato_trabajo' or edit_mode %}
<div class="col-md-4">
  <label class="form-label fw-semibold">Obra (opcional)</label>
  ... (el select de obra_id_post existente) ...
</div>
{% endif %}
```

- [ ] **Step 3.4: Verificar Django check**

```bash
python manage.py check
```

Esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 3.5: Probar manualmente el flujo**

1. Ir a http://localhost:8000/documentos-empresa/nuevo/
2. Seleccionar "Contrato de Trabajo"
3. Completar Sección A (obra, especialidad, tipo, sueldo, fecha inicio) + Sección B (datos personales)
4. Guardar → verificar que:
   - Se creó un nuevo `Contrato` en `/contratos/`
   - El preview muestra especialidad, obra, sueldo, tipo (sin blancos)
   - El campo "En [ciudad], a [fecha]" aparece correctamente

- [ ] **Step 3.6: Commit**

```bash
git add core/forms.py core/views/documentos_generados.py templates/documentos_generados/form.html
git commit -m "feat: contrato_trabajo flow creates Contrato + DocumentoGenerado in one step"
```

---

## Task 4: Buscar Documentos — filtros mejorados

**Files:**
- Modify: `core/views/documentos_generados.py` — `doc_generado_list` (líneas 76-92)
- Modify: `templates/documentos_generados/list.html` — filtros + acciones

- [ ] **Step 4.1: Actualizar doc_generado_list view**

Reemplazar la función completa `doc_generado_list`:

```python
@login_required
def doc_generado_list(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')
    empresa_id = request.GET.get('empresa_id', '')
    obra_id = request.GET.get('obra_id', '')
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    qs = DocumentoGenerado.objects.filter(activo=True).select_related(
        'trabajador', 'obra', 'empresa'
    ).order_by('-creado_el')

    if q:
        qs = qs.filter(
            Q(trabajador__nombres__icontains=q) |
            Q(trabajador__apellidos__icontains=q) |
            Q(trabajador__rut__icontains=q)
        )
    if tipo:
        qs = qs.filter(tipo=tipo)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if obra_id:
        qs = qs.filter(obra_id=obra_id)
    if fecha_desde:
        try:
            import datetime
            qs = qs.filter(creado_el__date__gte=datetime.date.fromisoformat(fecha_desde))
        except ValueError:
            pass
    if fecha_hasta:
        try:
            import datetime
            qs = qs.filter(creado_el__date__lte=datetime.date.fromisoformat(fecha_hasta))
        except ValueError:
            pass

    empresas = ConfigEmpresa.objects.filter(activo=True)
    obras = Obra.objects.filter(activo=True).order_by('nombre')

    return render(request, 'documentos_generados/list.html', {
        'documentos': qs,
        'q': q,
        'tipo': tipo,
        'empresa_id': empresa_id,
        'obra_id': obra_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tipo_choices': DocumentoGenerado.TIPO_CHOICES,
        'empresas': empresas,
        'obras': obras,
    })
```

- [ ] **Step 4.2: Reemplazar templates/documentos_generados/list.html completo**

```html
{% extends 'base.html' %}
{% block title %}Buscar Documentos | TsDesk{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2 class="fw-bold mb-0"><i class="bi bi-search text-primary me-2"></i>Buscar Documentos</h2>
  <a href="{% url 'doc_generado_create' %}" class="btn btn-primary">
    <i class="bi bi-plus-circle me-1"></i>Generar Documento
  </a>
</div>

<!-- Filtros -->
<div class="card border-0 shadow-sm mb-3">
  <div class="card-body py-2">
    <form method="get" class="row g-2 align-items-end">
      <div class="col-md-3">
        <input type="text" name="q" value="{{ q }}" class="form-control"
               placeholder="Nombre o RUT del trabajador...">
      </div>
      <div class="col-md-2">
        <select name="tipo" class="form-select">
          <option value="">Todos los tipos</option>
          {% for val, label in tipo_choices %}
          <option value="{{ val }}" {% if tipo == val %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <select name="empresa_id" class="form-select">
          <option value="">Todas las empresas</option>
          {% for e in empresas %}
          <option value="{{ e.pk }}" {% if empresa_id == e.pk|stringformat:"s" %}selected{% endif %}>{{ e.nombre }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <select name="obra_id" class="form-select">
          <option value="">Todas las obras</option>
          {% for o in obras %}
          <option value="{{ o.pk }}" {% if obra_id == o.pk|stringformat:"s" %}selected{% endif %}>{{ o.nombre }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-md-1">
        <input type="date" name="fecha_desde" value="{{ fecha_desde }}" class="form-control"
               title="Fecha desde" placeholder="Desde">
      </div>
      <div class="col-md-1">
        <input type="date" name="fecha_hasta" value="{{ fecha_hasta }}" class="form-control"
               title="Fecha hasta" placeholder="Hasta">
      </div>
      <div class="col-auto d-flex gap-1">
        <button type="submit" class="btn btn-outline-primary">
          <i class="bi bi-search"></i>
        </button>
        {% if q or tipo or empresa_id or obra_id or fecha_desde or fecha_hasta %}
        <a href="{% url 'doc_generado_list' %}" class="btn btn-outline-secondary"
           data-bs-toggle="tooltip" data-bs-title="Limpiar filtros">
          <i class="bi bi-x-circle"></i>
        </a>
        {% endif %}
      </div>
    </form>
  </div>
</div>

<!-- Tabla -->
<div class="card border-0 shadow-sm">
  <div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
      <thead class="table-dark">
        <tr>
          <th>Tipo</th>
          <th>Trabajador</th>
          <th>Empresa</th>
          <th>Obra</th>
          <th>Creado</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {% for doc in documentos %}
        <tr>
          <td><span class="badge bg-secondary">{{ doc.get_tipo_display }}</span></td>
          <td>
            <a href="{% url 'trabajador_detail' doc.trabajador.rut %}">{{ doc.trabajador.nombre_completo }}</a>
            <div class="small text-muted"><code>{{ doc.trabajador.rut }}</code></div>
          </td>
          <td class="small">{{ doc.empresa.nombre }}</td>
          <td class="small">{{ doc.obra.nombre|default:"-" }}</td>
          <td class="small text-muted">{{ doc.creado_el|date:"d/m/Y H:i" }}</td>
          <td class="text-nowrap">
            <a href="{% url 'doc_generado_preview' doc.pk %}"
               class="btn btn-sm btn-success"
               data-bs-toggle="tooltip" data-bs-title="Ver e imprimir / guardar PDF">
              <i class="bi bi-eye me-1"></i>Ver
            </a>
            {% if doc.tipo == 'contrato_trabajo' %}
            <a href="{% url 'doc_generado_word' doc.pk %}"
               class="btn btn-sm btn-outline-primary"
               data-bs-toggle="tooltip" data-bs-title="Descargar Word (.docx)">
              <i class="bi bi-file-word me-1"></i>Word
            </a>
            {% endif %}
            <a href="{% url 'doc_generado_edit' doc.pk %}"
               class="btn btn-sm btn-outline-secondary"
               data-bs-toggle="tooltip" data-bs-title="Editar datos">
              <i class="bi bi-pencil"></i>
            </a>
            <form method="post" action="{% url 'doc_generado_delete' doc.pk %}"
                  class="d-inline" onsubmit="return confirm('¿Eliminar este documento?')">
              {% csrf_token %}
              <button class="btn btn-sm btn-outline-danger"
                      data-bs-toggle="tooltip" data-bs-title="Eliminar">
                <i class="bi bi-trash"></i>
              </button>
            </form>
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="6" class="text-center text-muted py-5">
            <i class="bi bi-file-earmark-x fs-2 d-block mb-2"></i>
            No hay documentos con esos filtros.
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="card-footer text-muted small">{{ documentos|length }} documento(s)</div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bootstrap.Tooltip(el, { trigger: 'hover' });
  });
});
</script>
{% endblock %}
```

- [ ] **Step 4.3: Verificar Django check**

```bash
python manage.py check
```

Esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 4.4: Probar manualmente los filtros**

1. Ir a http://localhost:8000/documentos-empresa/
2. Verificar que aparece con título "Buscar Documentos"
3. Aplicar filtro por tipo → solo muestra ese tipo
4. Aplicar rango de fechas → filtra correctamente
5. Limpiar filtros → muestra todo

- [ ] **Step 4.5: Commit**

```bash
git add core/views/documentos_generados.py templates/documentos_generados/list.html
git commit -m "feat: enhance Buscar Documentos with date range, empresa, obra filters"
```

---

## Self-Review

**Spec coverage:**
- ✅ Botón "Nuevo Contrato" eliminado de lista contratos (Task 1)
- ✅ Sidebar actualizado: "Generar Documento" + "Buscar Documentos" (Task 1)
- ✅ Flujo contrato_trabajo crea Contrato + DocumentoGenerado (Task 3)
- ✅ Sección A en el form con obra, especialidad, sueldo, tipo, fechas (Task 2+3)
- ✅ Buscar Documentos con filtros tipo/empresa/obra/fecha (Task 4)
- ✅ Acciones: Ver, Word (solo contrato_trabajo), Editar, Eliminar (Task 4)

**Consistency check:**
- `obra_contrato`, `especialidad_contrato` en el form → mismos nombres en view ✅
- `fecha_inicio_contrato`, `fecha_termino_contrato` → consistente en form y view ✅
- `seccion_a_keys` excluye todos los campos de Sección A del JSON `datos` ✅

**No placeholders:** Todos los steps tienen código completo ✅
