/* TsDesk App Core — v2.0 */

/* ── Filas de tabla clicables ── */
document.querySelectorAll('tr[data-href]').forEach(function(row) {
  row.style.cursor = 'pointer';
  row.addEventListener('click', function(e) {
    if (e.target.closest('a,button,form,input,select,label')) return;
    window.location = this.dataset.href;
  });
});

/* ── Modal subir rápido (delegación para contenido dinámico) ── */
document.addEventListener('click', function(e) {
  var btn = e.target.closest('.btn-subir-rapido');
  if (!btn) return;
  var rut  = document.getElementById('sr_rut');
  var tipo = document.getElementById('sr_tipo_id');
  var niv  = document.getElementById('sr_nivel');
  var ctr  = document.getElementById('sr_contrato_id');
  var nom  = document.getElementById('sr_tipo_nombre');
  if (rut)  rut.value  = btn.dataset.rut || '';
  if (tipo) tipo.value = btn.dataset.tipoId || '';
  if (niv)  niv.value  = btn.dataset.nivel || '';
  if (ctr)  ctr.value  = btn.dataset.contratoId || '';
  if (nom)  nom.textContent = btn.dataset.tipoNombre || '—';
  var modal = document.getElementById('modalSubirRapido');
  if (modal) new bootstrap.Modal(modal).show();
});

/* ── Auto-formateo RUT chileno ── */
function formatRUT(rut) {
  rut = rut.replace(/\./g, '').replace(/-/g, '');
  if (rut.length < 2) return rut;
  var body = rut.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return body + '-' + rut.slice(-1).toUpperCase();
}
document.querySelectorAll('input[name="rut"], input[data-rut]').forEach(function(input) {
  input.addEventListener('blur', function() {
    if (this.value) this.value = formatRUT(this.value);
  });
});

/* ── Confirmación de acciones peligrosas ── */
document.querySelectorAll('[data-confirm]').forEach(function(el) {
  el.addEventListener('click', function(e) {
    if (!confirm(this.dataset.confirm)) e.preventDefault();
  });
});

/* ── Tooltips Bootstrap ── */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[title]').forEach(function(el) {
    if (el.tagName !== 'A' || el.title) {
      try { new bootstrap.Tooltip(el, { trigger: 'hover', placement: 'top' }); } catch(e) {}
    }
  });
});

/* ── Offline banner ── */
(function() {
  function setBanner() {
    var b = document.getElementById('offlineBanner');
    if (!navigator.onLine) {
      if (!b) {
        b = document.createElement('div');
        b.id = 'offlineBanner';
        b.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#dc2626;color:#fff;text-align:center;padding:.4rem;font-size:.8rem;font-weight:600';
        b.innerHTML = '<i class="bi bi-wifi-off me-2"></i>Sin conexión — los cambios se guardarán al volver en línea.';
        document.body.appendChild(b);
      }
    } else if (b) { b.remove(); }
  }
  window.addEventListener('online', setBanner);
  window.addEventListener('offline', setBanner);
})();

/* ── Live search por servidor con debounce ── */
(function() {
  document.querySelectorAll('[data-live-search]').forEach(function(input) {
    var t;
    input.addEventListener('input', function() {
      clearTimeout(t);
      t = setTimeout(function() { input.closest('form').submit(); }, 400);
    });
  });
})();

/* ── Debounce helper ── */
function debounce(fn, delay) {
  var t;
  return function() {
    var args = arguments, ctx = this;
    clearTimeout(t);
    t = setTimeout(function() { fn.apply(ctx, args); }, delay);
  };
}
