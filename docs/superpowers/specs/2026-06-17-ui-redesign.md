# TsDesk UI/UX Redesign — Design Spec
**Fecha:** 2026-06-17  
**Alcance:** Desktop only (sistema local de escritorio)  
**Stack:** Django 4.2 + Bootstrap 5.3.3 + Bootstrap Icons 1.11.3 (sin cambio de librería)

---

## Objetivo

Transformar TsDesk en un ERP visualmente coherente, rápido de usar y profesional para una secretaria operativa que lo usa 8 horas diarias. El problema actual no es la librería de íconos ni Bootstrap — es la **ausencia de un sistema de diseño** que genera inconsistencia en los 57 templates.

---

## 1. Sistema de Diseño (Design Tokens)

### Paleta de colores (CSS variables en :root)

```css
--color-primary:      #1e40af;   /* Azul profesional — acciones principales */
--color-primary-dark: #1e3a8a;
--color-primary-soft: #eff6ff;   /* Fondos suaves azul */

--color-success:      #16a34a;
--color-success-soft: #f0fdf4;

--color-danger:       #dc2626;
--color-danger-soft:  #fef2f2;

--color-warning:      #d97706;
--color-warning-soft: #fffbeb;

--color-muted:        #64748b;
--color-border:       #e2e8f0;
--color-surface:      #ffffff;
--color-bg:           #f1f5f9;   /* Fondo general más oscuro que #f8fafc actual */

--color-sidebar-bg:   #0f172a;   /* Slate-900 — más profundo que bg-dark */
--color-sidebar-text: #94a3b8;   /* Slate-400 */
--color-sidebar-active: #3b82f6; /* Blue-500 accent activo */

--color-text:         #0f172a;
--color-text-muted:   #64748b;
```

### Escala tipográfica única

```css
--text-xs:   0.70rem;   /* Solo metadatos secundarios */
--text-sm:   0.80rem;   /* Tablas, badges, labels */
--text-base: 0.875rem;  /* Texto base del sistema */
--text-md:   1rem;      /* Títulos de tarjetas */
--text-lg:   1.125rem;  /* Títulos de página */
--text-xl:   1.5rem;    /* KPIs numéricos */
```

### Espaciado consistente
- Cards: `border-radius: 8px`, `box-shadow: 0 1px 3px rgba(0,0,0,.08)`
- Padding de tarjetas: `1rem 1.25rem`
- Gap entre secciones: `1.5rem`
- Padding de tablas filas: `0.6rem 0.75rem`

---

## 2. Mapa de íconos — un concepto = un ícono

| Concepto | Ícono Bootstrap | Uso actual (problema) |
|---|---|---|
| Dashboard / Panel | `speedometer2` | ✓ consistente |
| Trabajador | `person-badge-fill` | ✓ consistente |
| Obra / Proyecto | `building-fill` | varía con `building`, `building-fill-gear` |
| Contrato | `file-earmark-person-fill` | varía con múltiples |
| Documento faltante | `folder-x` | 4 íconos distintos |
| Documento pendiente firma | `pen-fill` | varía con `pen`, `pencil` |
| Finiquito | `file-earmark-check-fill` | varía con `file-earmark-break-fill` |
| Subir archivo | `cloud-upload-fill` | varía con `upload`, `file-upload` |
| Eliminar | `trash3-fill` | varía con `trash`, `trash3` |
| Editar | `pencil-square` | varía con `pencil`, `pen` |
| Ver / Preview | `eye-fill` | ✓ consistente |
| Descargar | `download` | ✓ consistente |
| Agregar nuevo | `plus-circle-fill` | varía con `plus`, `plus-lg` |
| Alertas / Urgente | `exclamation-triangle-fill` | ✓ consistente |
| Éxito / OK | `check-circle-fill` | ✓ consistente |
| Vencimiento | `calendar-x-fill` | varía |
| Licencia médica | `bandaid-fill` | actualmente `hospital` |
| Bodega | `boxes` | ✓ consistente |
| Reportes | `bar-chart-fill` | ✓ consistente |
| Restaurar | `arrow-counterclockwise` | ✓ consistente |

---

## 3. Sidebar — Rediseño

### Problema actual
- `bg-dark` con `bg-primary rounded` para activos = mezcla visual inconsistente
- Botón amarillo "Generar Documento" como acción primaria no refleja el flujo real
- "Borradores" como botón ícono separado = UX confusa
- Active state no se distingue bien del hover

### Diseño nuevo
- Fondo: `var(--color-sidebar-bg)` = `#0f172a` (Slate-900, más profundo y profesional)
- Ancho fijo: 220px (reducido de 240px para ganar espacio en contenido)
- Active state: borde izquierdo de 3px `var(--color-sidebar-active)` + fondo sutil `rgba(59,130,246,.12)`
- Hover: fondo `rgba(255,255,255,.05)`
- Íconos: siempre 16px, color `var(--color-sidebar-text)` en reposo, blanco al hover/activo
- Texto: `var(--text-sm)` = 0.80rem (más compacto)
- "Generar Documento" → botón azul primario (no amarillo), tamaño completo
- "Borradores" → sub-item indentado bajo "Generar Documento"
- Separadores entre secciones: línea sutil, no solo `<hr>`
- Logo "TsDesk" con badge de versión

### Jerarquía de navegación (sin cambios en URLs)
```
TsDesk v1.0
─────────────────
[+ Nuevo Documento]     ← acción primaria, azul
  └ Borradores          ← sub-item
─────────────────
Panel Principal

OPERACIONES
  Trabajadores
  Obras y Proyectos
  Contratos
  Bodega / Materiales

DOCUMENTOS
  ⚠ Alertas            ← "Pendientes" renombrado a "Alertas"
  Archivo Central       ← "Centro de Documentos" renombrado
  Licencias Médicas
  Reportes
  Papelera

ADMIN (solo superuser)
  Usuarios
  Catálogos
  Auditoría
  Tasas AFP/Salud

─────────────────
Configuración
  Mis Empresas

─────────────────
[usuario]  [cerrar sesión]
```

**Cambio importante:** "Contratos" aparece en la navegación (actualmente está pero sin enlace directo visible en sidebar). Se agrega como item bajo Operaciones.

---

## 4. Header / Topbar

Actualmente no hay topbar — el contenido empieza directamente en `<main>`. Se agrega una barra fina persistente:

```
[breadcrumb / título de página]              [usuario · rol · logout]
```

- Altura: 48px
- Fondo: blanco, borde inferior 1px `var(--color-border)`
- Sticky top (no scrollea)
- El bloque de mensajes/alertas Django va debajo del topbar, no como primer elemento del content

---

## 5. Dashboard — Progressive Disclosure

### Problema actual
Todas las secciones de alertas se muestran expandidas simultáneamente. Con 8 categorías activas, es un muro.

### Diseño nuevo
- **KPI strip**: se mantiene, mejorado con iconografía correcta y colores del sistema
- **Tabla "Estado por Obra"**: SIEMPRE en primer lugar, es el resumen ejecutivo
- **Alertas colapsables**: cada categoría tiene header clicable con badge de conteo
  - Rojo crítico (`--color-danger`): Vencidos sin renovar, Finiquitos pendientes
  - Ámbar atención (`--color-warning`): Por vencer en 30d, Pendientes firma +15d
  - Azul info (`--color-primary`): Multi-obra, Docs faltantes, Licencias largas
- **Estado por defecto**: la primera categoría con alertas se muestra expandida, el resto colapsado
- **Panel derecho "Próximos Vencimientos"**: rediseñado como timeline vertical con días como separadores

---

## 6. Componentes transversales

### Tarjetas (Cards)
```css
.card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.card-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  padding: 0.75rem 1.25rem;
  font-size: var(--text-sm);
  font-weight: 600;
}
```

### Tablas
- Header: fondo `#f8fafc`, texto `var(--text-sm)`, color `var(--color-muted)`
- Filas: padding `0.55rem 0.75rem`
- Hover: `background: #f8fafc`
- Zebra striping: NO (interfiere con row-colors de estado)
- Bordes: solo horizontales (`border-bottom`)

### Botones de acción en tabla
```
[👁] [⬇] [✏] [🗑]
```
- Tamaño `btn-sm`, sin texto (solo ícono), con `title` para tooltip
- Agrupados en `d-flex gap-1`
- Colores: primary/secondary/danger únicamente

### Badges de estado
Sistema unificado:
- `badge-vigente`: verde suave (fondo `#dcfce7`, texto `#166534`)
- `badge-vencido`: rojo suave (fondo `#fee2e2`, texto `#991b1b`)
- `badge-proximo`: ámbar suave (fondo `#fef3c7`, texto `#92400e`)
- `badge-pendiente`: azul suave (fondo `#dbeafe`, texto `#1e40af`)
- `badge-papelera`: gris suave (fondo `#f1f5f9`, texto `#475569`)

### Mensajes flash (Django messages)
- Posición: debajo del topbar, arriba del contenido
- Auto-dismiss: 4 segundos
- Con ícono izquierdo acorde al tipo

---

## 7. Templates a modificar (prioridad)

### Fase 1 — Base y sistema (afecta todo)
1. `static/css/custom-theme.css` — nuevo sistema de diseño completo
2. `templates/base.html` — sidebar + topbar + layout

### Fase 2 — Páginas de alta frecuencia
3. `templates/dashboard/index.html`
4. `templates/documentos/pendientes.html`
5. `templates/trabajadores/list.html`
6. `templates/trabajadores/detail.html`
7. `templates/obras/list.html`
8. `templates/obras/detail.html`

### Fase 3 — Módulos secundarios
9. `templates/contratos/list.html`
10. `templates/documentos/central.html`
11. `templates/documentos/papelera.html`
12. `templates/licencias/list.html`
13. `templates/bodega/index.html`
14. `templates/reportes/index.html`
15. `templates/admin_panel/usuarios.html`
16. `templates/admin_panel/catalogos.html`

### No se modifican
- Templates de impresión/PDF (`documentos_generados/print/`)
- Formularios de ingreso de datos (riesgo de romper funcionalidad, mejora separada)
- Login page (funcional, baja prioridad)

---

## 8. Criterios de éxito

- Un solo lugar para cambiar cualquier color: `custom-theme.css`
- Cada concepto de negocio usa siempre el mismo ícono en todos los módulos
- La secretaria puede ver el estado crítico del día en menos de 5 segundos al entrar
- Cero estilos inline hardcodeados con colores hex en los templates
- Tipografía legible a escala `var(--text-base)` = 0.875rem como mínimo para contenido

---

## Fuera de alcance

- Mobile/responsive
- Formularios de creación/edición (funcionalidad intacta)
- Lógica de negocio (ningún cambio en views.py)
- Librería de íconos (Bootstrap Icons 1.11.3 se mantiene)
- Templates de impresión PDF
