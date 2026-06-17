# TsDesk UI Redesign — Plan 1: Sistema de Diseño + Navegación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el CSS actual con un sistema de diseño coherente basado en variables, y rediseñar el sidebar/layout base que afecta las 57 páginas del sistema.

**Architecture:** Primero el CSS (tokens/variables), luego base.html que los consume. Ningún cambio en views.py ni modelos. Bootstrap 5.3.3 y Bootstrap Icons 1.11.3 se mantienen como CDN.

**Tech Stack:** Django templates, Bootstrap 5.3.3, Bootstrap Icons 1.11.3, CSS custom properties

---

## Archivos involucrados

- Modify: `static/css/custom-theme.css` — reemplazo completo
- Modify: `templates/base.html` — sidebar + topbar + layout

---

### Task 1: Nuevo sistema de diseño CSS

**Files:**
- Modify: `static/css/custom-theme.css`

- [ ] **Step 1: Reemplazar custom-theme.css completo**

Contenido exacto del archivo:

```css
/* ═══════════════════════════════════════════════════════════════
   TsDesk Design System — v2.0
   Desktop only. No mobile.
═══════════════════════════════════════════════════════════════ */

/* ── 1. Design Tokens ──────────────────────────────────────── */
:root {
  /* Colores primarios */
  --c-primary:       #1e40af;
  --c-primary-dark:  #1e3a8a;
  --c-primary-soft:  #eff6ff;
  --c-primary-mid:   #bfdbfe;

  /* Semáforo */
  --c-success:       #16a34a;
  --c-success-soft:  #f0fdf4;
  --c-success-mid:   #bbf7d0;

  --c-danger:        #dc2626;
  --c-danger-soft:   #fef2f2;
  --c-danger-mid:    #fecaca;

  --c-warning:       #d97706;
  --c-warning-soft:  #fffbeb;
  --c-warning-mid:   #fde68a;

  /* Neutrales */
  --c-bg:            #f1f5f9;
  --c-surface:       #ffffff;
  --c-border:        #e2e8f0;
  --c-border-dark:   #cbd5e1;
  --c-muted:         #64748b;
  --c-text:          #0f172a;
  --c-text-light:    #94a3b8;

  /* Sidebar */
  --c-sidebar-bg:    #0f172a;
  --c-sidebar-text:  #94a3b8;
  --c-sidebar-hover: rgba(255,255,255,.06);
  --c-sidebar-active-bg: rgba(59,130,246,.15);
  --c-sidebar-active-border: #3b82f6;
  --sidebar-width:   220px;

  /* Topbar */
  --topbar-height:   48px;

  /* Tipografía */
  --text-xs:   0.70rem;
  --text-sm:   0.80rem;
  --text-base: 0.875rem;
  --text-md:   1rem;
  --text-lg:   1.125rem;
  --text-xl:   1.5rem;

  /* Forma */
  --radius-sm:  4px;
  --radius-md:  8px;
  --radius-lg:  12px;
  --shadow-sm:  0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md:  0 4px 6px rgba(0,0,0,.05), 0 2px 4px rgba(0,0,0,.04);
}

/* ── 2. Base ────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: var(--text-base);
  color: var(--c-text);
  background: var(--c-bg);
  -webkit-font-smoothing: antialiased;
}

/* ── 3. Layout ──────────────────────────────────────────────── */
#layoutWrapper {
  display: flex;
  min-height: 100vh;
}

#sidebarMenu {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--c-sidebar-bg);
  min-height: 100vh;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.1) transparent;
}

#mainContent {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

#topbar {
  height: var(--topbar-height);
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  gap: 1rem;
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

#pageContent {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

/* ── 4. Sidebar ─────────────────────────────────────────────── */
.sidebar-logo {
  padding: 1rem 1rem 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,.07);
}

.sidebar-logo .brand-name {
  font-size: var(--text-md);
  font-weight: 700;
  color: #fff;
  letter-spacing: -.01em;
}

.sidebar-logo .brand-sub {
  font-size: var(--text-xs);
  color: var(--c-sidebar-text);
  margin-top: 1px;
}

.sidebar-primary-action {
  padding: 0.75rem 0.75rem 0.5rem;
}

.sidebar-primary-action .btn-new-doc {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.55rem 0.75rem;
  background: var(--c-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: none;
  transition: background .15s;
}
.sidebar-primary-action .btn-new-doc:hover { background: var(--c-primary-dark); color: #fff; }
.sidebar-primary-action .btn-new-doc.active { background: var(--c-primary-dark); }

.sidebar-sub-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem 0.3rem 2.25rem;
  color: var(--c-sidebar-text);
  font-size: var(--text-xs);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: color .15s;
}
.sidebar-sub-link:hover { color: #fff; }
.sidebar-sub-link.active { color: #93c5fd; }

.sidebar-section {
  padding: 0.625rem 0.75rem 0.25rem;
}

.sidebar-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: #475569;
  padding: 0 0.25rem;
}

.sidebar-nav {
  list-style: none;
  padding: 0 0.5rem;
  margin: 0;
}

.sidebar-nav li { margin-bottom: 1px; }

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.45rem 0.75rem;
  color: var(--c-sidebar-text);
  font-size: var(--text-sm);
  text-decoration: none;
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  transition: background .12s, color .12s, border-color .12s;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-nav a:hover {
  background: var(--c-sidebar-hover);
  color: #e2e8f0;
}

.sidebar-nav a.active {
  background: var(--c-sidebar-active-bg);
  border-left-color: var(--c-sidebar-active-border);
  color: #bfdbfe;
  font-weight: 600;
}

.sidebar-nav a .nav-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.sidebar-nav a .nav-badge {
  margin-left: auto;
  font-size: 0.6rem;
  padding: 0.15rem 0.35rem;
  border-radius: 10px;
  background: var(--c-danger);
  color: #fff;
  font-weight: 700;
  line-height: 1;
}

.sidebar-divider {
  height: 1px;
  background: rgba(255,255,255,.07);
  margin: 0.5rem 0.75rem;
}

.sidebar-footer {
  margin-top: auto;
  padding: 0.75rem;
  border-top: 1px solid rgba(255,255,255,.07);
}

.sidebar-user-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-user-role {
  font-size: var(--text-xs);
  color: var(--c-sidebar-text);
}

/* ── 5. Topbar ──────────────────────────────────────────────── */
.topbar-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--c-text);
  flex: 1;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: var(--text-sm);
  color: var(--c-muted);
}

/* ── 6. Cards ───────────────────────────────────────────────── */
.card {
  border: 1px solid var(--c-border) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-sm) !important;
  background: var(--c-surface);
}

.card-header {
  background: var(--c-surface) !important;
  border-bottom: 1px solid var(--c-border) !important;
  border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
  padding: 0.75rem 1.25rem;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--c-text);
}

.card-footer {
  background: #f8fafc !important;
  border-top: 1px solid var(--c-border) !important;
  font-size: var(--text-xs);
  color: var(--c-muted);
  padding: 0.6rem 1.25rem;
}

/* Card con acento de color izquierdo */
.card-accent-danger  { border-left: 3px solid var(--c-danger)  !important; }
.card-accent-warning { border-left: 3px solid var(--c-warning) !important; }
.card-accent-success { border-left: 3px solid var(--c-success) !important; }
.card-accent-primary { border-left: 3px solid var(--c-primary) !important; }
.card-accent-muted   { border-left: 3px solid var(--c-border-dark) !important; }

/* ── 7. KPI Cards ───────────────────────────────────────────── */
.kpi-card {
  padding: 0.875rem 1rem;
}
.kpi-label {
  font-size: var(--text-xs);
  color: var(--c-muted);
  font-weight: 500;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.kpi-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--c-text);
  line-height: 1;
  margin-bottom: 0.15rem;
}
.kpi-sub {
  font-size: var(--text-xs);
  color: var(--c-muted);
}

/* ── 8. Tablas ──────────────────────────────────────────────── */
.table {
  font-size: var(--text-sm);
  margin-bottom: 0;
}

.table th {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--c-muted);
  background: #f8fafc;
  border-bottom: 1px solid var(--c-border) !important;
  padding: 0.6rem 0.75rem;
  white-space: nowrap;
}

.table td {
  padding: 0.55rem 0.75rem;
  vertical-align: middle;
  border-bottom: 1px solid var(--c-border);
  border-top: none;
}

.table tbody tr:hover { background: #f8fafc; }
.table tbody tr:last-child td { border-bottom: none; }

/* ── 9. Badges de estado unificados ─────────────────────────── */
.badge-vigente   { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; font-weight: 600; }
.badge-vencido   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; font-weight: 600; }
.badge-proximo   { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600; }
.badge-pendiente { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; font-weight: 600; }
.badge-papelera  { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; font-weight: 600; }
.badge-firma     { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; font-weight: 600; }
.badge-cerrada   { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600; }
.badge-archivada { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; font-weight: 600; }

/* ── 10. Botones de acción en tabla ─────────────────────────── */
.btn-table {
  padding: 0.2rem 0.45rem;
  font-size: var(--text-xs);
  line-height: 1.4;
  border-radius: var(--radius-sm);
}

.action-group {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: flex-end;
}

/* ── 11. Mensajes flash ──────────────────────────────────────── */
.alert {
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  border: 1px solid transparent;
  padding: 0.75rem 1rem;
}

.alert-success { background: var(--c-success-soft); color: #14532d; border-color: var(--c-success-mid); }
.alert-danger  { background: var(--c-danger-soft);  color: #7f1d1d; border-color: var(--c-danger-mid); }
.alert-warning { background: var(--c-warning-soft); color: #78350f; border-color: var(--c-warning-mid); }
.alert-info    { background: var(--c-primary-soft); color: #1e3a8a; border-color: var(--c-primary-mid); }

/* ── 12. Tabs ───────────────────────────────────────────────── */
.nav-tabs { border-bottom: 2px solid var(--c-border); }
.nav-tabs .nav-link {
  color: var(--c-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 0.6rem 1rem;
  margin-bottom: -2px;
  border-radius: 0;
  transition: color .15s, border-color .15s;
}
.nav-tabs .nav-link:hover { color: var(--c-primary); border-bottom-color: var(--c-primary-mid); }
.nav-tabs .nav-link.active {
  color: var(--c-primary);
  font-weight: 700;
  border-bottom: 2px solid var(--c-primary);
  background: transparent;
}

/* ── 13. Formularios ─────────────────────────────────────────── */
.form-control, .form-select {
  font-size: var(--text-sm);
  border-color: var(--c-border);
  border-radius: var(--radius-sm);
  color: var(--c-text);
}
.form-control:focus, .form-select:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(59,130,246,.15);
}
.form-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--c-text);
  margin-bottom: 0.3rem;
}

/* ── 14. Botones ─────────────────────────────────────────────── */
.btn {
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-sm);
  transition: background .12s, border-color .12s, box-shadow .12s;
}
.btn-primary { background: var(--c-primary); border-color: var(--c-primary); }
.btn-primary:hover { background: var(--c-primary-dark); border-color: var(--c-primary-dark); }
.btn-xs { font-size: var(--text-xs); padding: 0.15rem 0.45rem; }

/* ── 15. Acordeones ──────────────────────────────────────────── */
.accordion-item {
  border: 1px solid var(--c-border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden;
  margin-bottom: 0.5rem;
}
.accordion-button {
  font-size: var(--text-sm);
  font-weight: 600;
  background: var(--c-surface);
  color: var(--c-text);
  padding: 0.75rem 1rem;
  border-radius: 0 !important;
}
.accordion-button:not(.collapsed) {
  background: var(--c-primary-soft);
  color: var(--c-primary-dark);
  box-shadow: none;
}
.accordion-button::after { flex-shrink: 0; }

/* ── 16. Drop zone ───────────────────────────────────────────── */
.drop-zone {
  border: 2px dashed var(--c-border-dark);
  background: #f8fafc;
  transition: border-color .2s, background .2s;
  cursor: pointer;
  border-radius: var(--radius-md);
}
.drop-zone:hover, .drop-zone.active {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
}

/* ── 17. Wizard cards ────────────────────────────────────────── */
.wizard-card {
  transition: transform .15s ease, box-shadow .15s ease;
  cursor: pointer;
  border-width: 2px !important;
  border-radius: var(--radius-md) !important;
}
.wizard-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md) !important;
}

/* ── 18. Miscellaneous ───────────────────────────────────────── */
.stock-critico { animation: pulseRed 2s infinite; }
@keyframes pulseRed {
  0%, 100% { background: rgba(220,38,38,.04); }
  50%       { background: rgba(220,38,38,.12); }
}

.pulse { animation: pulseBadge 1.5s infinite; }
@keyframes pulseBadge {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

.progress { border-radius: 10px; }
.breadcrumb { font-size: var(--text-sm); }
.text-truncate-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cursor-pointer { cursor: pointer; }

/* Section header (h dentro de página) */
.section-title {
  font-size: var(--text-sm);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--c-muted);
  margin-bottom: 0.75rem;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--c-muted);
}
.empty-state i { font-size: 2.5rem; display: block; margin-bottom: 1rem; opacity: .4; }
.empty-state h6 { font-weight: 600; color: var(--c-text); margin-bottom: 0.25rem; }
.empty-state p  { font-size: var(--text-sm); margin: 0; }

/* ── 19. Print ───────────────────────────────────────────────── */
@media print {
  #sidebarMenu, #topbar, .no-print { display: none !important; }
  #pageContent { padding: 0 !important; }
  .card { box-shadow: none !important; border: 1px solid #ccc !important; }
}
```

- [ ] **Step 2: Verificar que Django sirve el CSS**

```bash
python manage.py check
```
Debe retornar: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add static/css/custom-theme.css
git commit -m "style: nuevo sistema de diseño con variables CSS y componentes unificados"
```

---

### Task 2: Rediseño de base.html

**Files:**
- Modify: `templates/base.html`

- [ ] **Step 1: Reemplazar base.html completo**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}TsDesk{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <link rel="stylesheet" href="/static/css/custom-theme.css">
  {% block extra_css %}{% endblock %}
</head>
<body>

{% if user.is_authenticated %}

<div id="layoutWrapper">

  <!-- ══ SIDEBAR ══════════════════════════════════════════════ -->
  <nav id="sidebarMenu">

    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="brand-name"><i class="bi bi-building-fill-gear me-1" style="color:#3b82f6"></i>TsDesk</div>
      <div class="brand-sub">Sistema de Gestión</div>
    </div>

    <!-- Acción primaria -->
    <div class="sidebar-primary-action">
      <a href="{% url 'doc_generado_create' %}"
         class="btn-new-doc {% if request.resolver_match.url_name == 'doc_generado_create' %}active{% endif %}">
        <i class="bi bi-plus-circle-fill"></i>
        Nuevo Documento
      </a>
      <a href="{% url 'doc_generado_borradores' %}"
         class="sidebar-sub-link mt-1 {% if request.resolver_match.url_name == 'doc_generado_borradores' %}active{% endif %}">
        <i class="bi bi-journals" style="font-size:.75rem"></i>Borradores guardados
      </a>
    </div>

    <div class="sidebar-divider"></div>

    <!-- Panel principal -->
    <ul class="sidebar-nav" style="padding-bottom:.25rem">
      <li>
        <a href="{% url 'dashboard' %}"
           class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
          <i class="bi bi-speedometer2 nav-icon"></i>Panel Principal
          {% if total_alertas_sidebar and total_alertas_sidebar > 0 %}
          <span class="nav-badge">{{ total_alertas_sidebar }}</span>
          {% endif %}
        </a>
      </li>
    </ul>

    <!-- Operaciones -->
    <div class="sidebar-section">
      <span class="sidebar-section-label">Operaciones</span>
    </div>
    <ul class="sidebar-nav">
      <li>
        <a href="{% url 'trabajadores_list' %}"
           class="{% if 'trabajadores' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-person-badge-fill nav-icon"></i>Trabajadores
        </a>
      </li>
      <li>
        <a href="{% url 'obras_list' %}"
           class="{% if 'obra' in request.resolver_match.url_name and 'doc' not in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-building-fill nav-icon"></i>Obras y Proyectos
        </a>
      </li>
      <li>
        <a href="{% url 'contratos_list' %}"
           class="{% if 'contrato' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-file-earmark-person-fill nav-icon"></i>Contratos
        </a>
      </li>
      <li>
        <a href="{% url 'bodega_index' %}"
           class="{% if 'bodega' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-boxes nav-icon"></i>Bodega / Materiales
        </a>
      </li>
    </ul>

    <!-- Documentos -->
    <div class="sidebar-section">
      <span class="sidebar-section-label">Documentos</span>
    </div>
    <ul class="sidebar-nav">
      <li>
        <a href="{% url 'documentos_pendientes' %}"
           class="{% if request.resolver_match.url_name == 'documentos_pendientes' %}active{% endif %}">
          <i class="bi bi-exclamation-triangle-fill nav-icon" style="color:#f59e0b"></i>Centro de Alertas
        </a>
      </li>
      <li>
        <a href="{% url 'documentos_central' %}"
           class="{% if request.resolver_match.url_name == 'documentos_central' %}active{% endif %}">
          <i class="bi bi-folder2-open nav-icon"></i>Archivo Documental
        </a>
      </li>
      <li>
        <a href="{% url 'licencia_list' %}"
           class="{% if 'licencia' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-bandaid-fill nav-icon"></i>Licencias Médicas
        </a>
      </li>
      <li>
        <a href="{% url 'reportes_consolidados' %}"
           class="{% if request.resolver_match.url_name == 'reportes_consolidados' %}active{% endif %}">
          <i class="bi bi-bar-chart-fill nav-icon"></i>Reportes
        </a>
      </li>
      <li>
        <a href="{% url 'papelera_documentos' %}"
           class="{% if request.resolver_match.url_name == 'papelera_documentos' %}active{% endif %}">
          <i class="bi bi-trash3 nav-icon" style="opacity:.6"></i>Papelera
        </a>
      </li>
    </ul>

    {% if user.is_superuser %}
    <!-- Admin -->
    <div class="sidebar-section">
      <span class="sidebar-section-label">Administración</span>
    </div>
    <ul class="sidebar-nav">
      <li>
        <a href="{% url 'admin_usuarios' %}"
           class="{% if request.resolver_match.url_name == 'admin_usuarios' %}active{% endif %}">
          <i class="bi bi-people-fill nav-icon"></i>Usuarios
        </a>
      </li>
      <li>
        <a href="{% url 'admin_catalogos' %}"
           class="{% if request.resolver_match.url_name == 'admin_catalogos' %}active{% endif %}">
          <i class="bi bi-gear-fill nav-icon"></i>Catálogos
        </a>
      </li>
      <li>
        <a href="{% url 'admin_auditoria' %}"
           class="{% if request.resolver_match.url_name == 'admin_auditoria' %}active{% endif %}">
          <i class="bi bi-journal-text nav-icon"></i>Auditoría
        </a>
      </li>
      <li>
        <a href="{% url 'config_remuneraciones_list' %}"
           class="{% if 'config_remuneraciones' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-sliders nav-icon"></i>Tasas AFP/Salud
        </a>
      </li>
    </ul>
    {% endif %}

    <div class="sidebar-divider"></div>

    <!-- Configuración -->
    <ul class="sidebar-nav">
      <li>
        <a href="{% url 'empresa_list' %}"
           class="{% if 'empresa' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-building-fill-gear nav-icon"></i>Mis Empresas
        </a>
      </li>
    </ul>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="d-flex align-items-center gap-2">
        <div class="flex-grow-1 overflow-hidden">
          <div class="sidebar-user-name">{{ user.get_full_name|default:user.username }}</div>
          <div class="sidebar-user-role">
            {% if user.is_superuser %}Super Admin{% else %}Secretaria Operativa{% endif %}
          </div>
        </div>
        <a href="{% url 'logout' %}" class="btn btn-sm btn-outline-secondary p-1 flex-shrink-0"
           style="border-color:rgba(255,255,255,.15);color:#94a3b8" title="Cerrar sesión">
          <i class="bi bi-box-arrow-right"></i>
        </a>
      </div>
    </div>

  </nav>
  <!-- ══ /SIDEBAR ══════════════════════════════════════════════ -->

  <!-- ══ CONTENIDO PRINCIPAL ═══════════════════════════════════ -->
  <div id="mainContent">

    <!-- Topbar -->
    <div id="topbar">
      <span class="topbar-title">{% block page_title %}{% endblock %}</span>
      <div class="topbar-user">
        <span class="text-muted" style="font-size:var(--text-xs)">
          {% if user.is_superuser %}
            <span class="badge badge-pendiente me-1">Admin</span>
          {% endif %}
          {{ user.get_full_name|default:user.username }}
        </span>
      </div>
    </div>

    <!-- Mensajes flash -->
    {% if messages %}
    <div style="padding:.75rem 1.5rem 0">
      {% for msg in messages %}
      <div class="alert alert-{{ msg.tags|default:'info' }} alert-dismissible fade show d-flex align-items-center gap-2 mb-2" role="alert">
        {% if msg.tags == 'success' %}<i class="bi bi-check-circle-fill flex-shrink-0"></i>
        {% elif msg.tags == 'danger' or msg.tags == 'error' %}<i class="bi bi-exclamation-circle-fill flex-shrink-0"></i>
        {% elif msg.tags == 'warning' %}<i class="bi bi-exclamation-triangle-fill flex-shrink-0"></i>
        {% else %}<i class="bi bi-info-circle-fill flex-shrink-0"></i>{% endif %}
        <span>{{ msg }}</span>
        <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Contenido de la página -->
    <div id="pageContent">
      {% block content %}{% endblock %}
    </div>

  </div>
  <!-- ══ /CONTENIDO PRINCIPAL ══════════════════════════════════ -->

</div>

{% else %}
{% block content_auth %}{% endblock %}
{% endif %}

<!-- Modal preview documental global -->
<div class="modal fade" id="modalPreviewDoc" tabindex="-1">
  <div class="modal-dialog modal-xl modal-dialog-centered">
    <div class="modal-content" style="height:90vh;display:flex;flex-direction:column">
      <div class="modal-header py-2" style="flex-shrink:0">
        <h6 class="modal-title fw-semibold" id="previewDocTitle">Vista Previa</h6>
        <div class="ms-auto d-flex gap-2">
          <a id="previewDocDownload" href="#" class="btn btn-sm btn-outline-primary" download>
            <i class="bi bi-download me-1"></i>Descargar
          </a>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
      </div>
      <div class="modal-body p-0" id="previewDocBody" style="flex:1;min-height:0;overflow:hidden">
        <div class="text-center py-5"><div class="spinner-border text-primary"></div></div>
      </div>
    </div>
  </div>
</div>

<!-- Modal upload rápido global -->
<div class="modal fade" id="modalSubirRapido" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header py-2">
        <h6 class="modal-title fw-semibold"><i class="bi bi-cloud-upload-fill me-2 text-primary"></i>Subir Documento</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form method="post" action="{% url 'documento_upload_rapido' %}" enctype="multipart/form-data">
        {% csrf_token %}
        <input type="hidden" name="next" value="{{ request.get_full_path }}">
        <input type="hidden" name="trabajador_rut" id="sr_rut">
        <input type="hidden" name="tipo_documento_id" id="sr_tipo_id">
        <input type="hidden" name="nivel" id="sr_nivel">
        <input type="hidden" name="contrato_id" id="sr_contrato_id">
        <div class="modal-body">
          <div class="mb-3">
            <label class="form-label text-muted" style="font-size:var(--text-xs);text-transform:uppercase;letter-spacing:.05em">Tipo de documento</label>
            <div class="fw-semibold" id="sr_tipo_nombre">—</div>
          </div>
          <div class="mb-3">
            <label class="form-label">Archivo <span class="text-danger">*</span></label>
            <input type="file" name="archivo" class="form-control" required accept=".pdf,.jpg,.jpeg,.png,.doc,.docx">
          </div>
          <div class="mb-1" id="sr_fecha_wrapper">
            <label class="form-label">Fecha de vencimiento <small class="text-muted">(opcional)</small></label>
            <input type="date" name="fecha_vencimiento" class="form-control">
          </div>
        </div>
        <div class="modal-footer py-2">
          <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
          <button type="submit" class="btn btn-sm btn-primary">
            <i class="bi bi-cloud-upload-fill me-1"></i>Subir
          </button>
        </div>
      </form>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="/static/js/app-core.js"></script>
{% block extra_js %}{% endblock %}

<script>
/* ── Funciones globales ── */
function previewDoc(url, nombre, extension) {
  document.getElementById('previewDocTitle').textContent = nombre || 'Vista Previa';
  document.getElementById('previewDocDownload').href = url;
  const body = document.getElementById('previewDocBody');
  const ext = (extension || '').toLowerCase();
  if (ext === 'pdf' || ext === 'html') {
    body.innerHTML = `<iframe src="${url}" style="width:100%;height:100%;border:none;"></iframe>`;
  } else if (['jpg','jpeg','png','gif','webp'].includes(ext)) {
    body.innerHTML = `<div class="text-center p-3"><img src="${url}" class="img-fluid" style="max-height:78vh;"></div>`;
  } else {
    body.innerHTML = `<div class="empty-state"><i class="bi bi-file-earmark"></i><h6>Vista previa no disponible</h6><a href="${url}" class="btn btn-sm btn-primary mt-3" download>Descargar archivo</a></div>`;
  }
  new bootstrap.Modal(document.getElementById('modalPreviewDoc')).show();
}

/* Modal subir rápido */
document.querySelectorAll('.btn-subir-rapido').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.getElementById('sr_rut').value          = this.dataset.rut || '';
    document.getElementById('sr_tipo_id').value      = this.dataset.tipoId || '';
    document.getElementById('sr_nivel').value        = this.dataset.nivel || '';
    document.getElementById('sr_contrato_id').value  = this.dataset.contratoId || '';
    document.getElementById('sr_tipo_nombre').textContent = this.dataset.tipoNombre || '—';
    new bootstrap.Modal(document.getElementById('modalSubirRapido')).show();
  });
});

/* Auto-dismiss alerts */
setTimeout(function() {
  document.querySelectorAll('.alert.fade.show').forEach(function(el) {
    var alert = bootstrap.Alert.getOrCreateInstance(el);
    if (alert) alert.close();
  });
}, 4500);

/* Topbar: set title from h4/h5 in page if block is empty */
document.addEventListener('DOMContentLoaded', function() {
  const topbarTitle = document.querySelector('.topbar-title');
  if (topbarTitle && !topbarTitle.textContent.trim()) {
    const h = document.querySelector('#pageContent h4, #pageContent h5, #pageContent h3');
    if (h) topbarTitle.textContent = h.textContent.trim();
  }
});
</script>

</body>
</html>
```

- [ ] **Step 2: Verificar que el servidor arranca sin errores**

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Abrir http://localhost:8000/ y verificar visualmente**

Checklist visual:
- [ ] Sidebar oscuro (#0f172a) con ancho 220px visible
- [ ] Logo "TsDesk" con ícono azul
- [ ] Botón "Nuevo Documento" azul (no amarillo)
- [ ] "Borradores guardados" como sub-item indentado
- [ ] "Contratos" aparece en la sección Operaciones
- [ ] "Centro de Alertas" (antes "Pendientes") y "Archivo Documental" (antes "Centro de Documentos")
- [ ] "Licencias Médicas" con ícono de bandita (bi-bandaid-fill)
- [ ] Active state: borde azul izquierdo + fondo sutil (no bg-primary rounded)
- [ ] Topbar de 48px visible con título de página
- [ ] Mensajes flash con ícono izquierdo

- [ ] **Step 4: Commit**

```bash
git add templates/base.html
git commit -m "feat: rediseño sidebar con sistema de diseño v2 — nuevo layout, jerarquía y topbar"
```

---

### Task 3: Actualizar app-core.js para el nuevo layout

**Files:**
- Modify: `static/js/app-core.js`

- [ ] **Step 1: Actualizar app-core.js**

El archivo actual tiene referencias al layout antiguo (sidebar toggle mobile, etc.). Reemplazar:

```javascript
/* TsDesk App Core — v2.0 */

/* ── Live search con debounce ── */
(function() {
  var searchInputs = document.querySelectorAll('[data-live-search]');
  searchInputs.forEach(function(input) {
    var timeout;
    input.addEventListener('input', function() {
      clearTimeout(timeout);
      timeout = setTimeout(function() {
        input.closest('form').submit();
      }, 400);
    });
  });
})();

/* ── Filas clicables ── */
document.querySelectorAll('tr[data-href]').forEach(function(row) {
  row.style.cursor = 'pointer';
  row.addEventListener('click', function(e) {
    if (e.target.closest('a,button,form,input,select')) return;
    window.location = this.dataset.href;
  });
});

/* ── Modal subir rápido (delegación de eventos, para contenido dinámico) ── */
document.addEventListener('click', function(e) {
  var btn = e.target.closest('.btn-subir-rapido');
  if (!btn) return;
  document.getElementById('sr_rut').value         = btn.dataset.rut || '';
  document.getElementById('sr_tipo_id').value     = btn.dataset.tipoId || '';
  document.getElementById('sr_nivel').value       = btn.dataset.nivel || '';
  document.getElementById('sr_contrato_id').value = btn.dataset.contratoId || '';
  document.getElementById('sr_tipo_nombre').textContent = btn.dataset.tipoNombre || '—';
  new bootstrap.Modal(document.getElementById('modalSubirRapido')).show();
});

/* ── Auto-formateo RUT chileno ── */
document.querySelectorAll('input[data-rut]').forEach(function(input) {
  input.addEventListener('input', function() {
    var v = this.value.replace(/[^0-9kK]/g, '');
    if (v.length > 1) {
      var body = v.slice(0, -1);
      var dv   = v.slice(-1).toUpperCase();
      body = body.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      this.value = body + '-' + dv;
    } else {
      this.value = v;
    }
  });
});

/* ── Confirmación de acciones peligrosas ── */
document.querySelectorAll('[data-confirm]').forEach(function(el) {
  el.addEventListener('click', function(e) {
    if (!confirm(this.dataset.confirm)) e.preventDefault();
  });
});

/* ── Topbar: título desde h4/h5 si el bloque page_title está vacío ── */
document.addEventListener('DOMContentLoaded', function() {
  var topbarTitle = document.querySelector('.topbar-title');
  if (topbarTitle && !topbarTitle.textContent.trim()) {
    var h = document.querySelector('#pageContent h4, #pageContent h5, #pageContent h3');
    if (h) topbarTitle.textContent = h.textContent.trim();
  }
  /* Tooltips Bootstrap */
  document.querySelectorAll('[title]').forEach(function(el) {
    new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' });
  });
});

/* ── Detectar conexión offline ── */
function updateOnlineStatus() {
  var banner = document.getElementById('offlineBanner');
  if (!navigator.onLine) {
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'offlineBanner';
      banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:#dc2626;color:#fff;text-align:center;padding:.4rem;font-size:.8rem;font-weight:600';
      banner.textContent = '⚠ Sin conexión a internet';
      document.body.prepend(banner);
    }
  } else if (banner) {
    banner.remove();
  }
}
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
```

- [ ] **Step 2: Commit**

```bash
git add static/js/app-core.js
git commit -m "refactor: app-core.js limpio para layout v2, sin referencias mobile"
```

---

### Verificación final Plan 1

- [ ] Abrir cada sección del sidebar y verificar estado activo correcto
- [ ] Verificar que `python manage.py check` retorna 0 issues
- [ ] Verificar que los mensajes flash aparecen con ícono y se auto-cierran en 4.5s
- [ ] Verificar que el modal "Subir Documento" abre correctamente desde cualquier página que lo use
- [ ] Verificar que el topbar muestra el título de página
- [ ] Commit final si todo OK:

```bash
git add -A
git commit -m "style: Plan 1 completo — design system + sidebar + topbar"
```
