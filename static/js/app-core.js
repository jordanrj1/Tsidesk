/* TsDesk App Core JS */

// Resiliencia offline: guarda formularios en localStorage si no hay conexión
document.addEventListener('DOMContentLoaded', function() {

  // Auto-hide alerts after 5 seconds
  document.querySelectorAll('.alert-dismissible').forEach(alert => {
    if (!alert.classList.contains('alert-danger') && !alert.classList.contains('alert-warning')) {
      setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      }, 5000);
    }
  });

  // Offline detection
  const offlineBanner = document.createElement('div');
  offlineBanner.id = 'offlineBanner';
  offlineBanner.className = 'alert alert-warning text-center mb-0 rounded-0 d-none';
  offlineBanner.style.position = 'fixed';
  offlineBanner.style.bottom = '0';
  offlineBanner.style.left = '0';
  offlineBanner.style.right = '0';
  offlineBanner.style.zIndex = '9999';
  offlineBanner.innerHTML = '<i class="bi bi-wifi-off me-2"></i><strong>Conexión intermitente.</strong> Los datos se han resguardado en el dispositivo y se procesarán al recuperar la señal.';
  document.body.appendChild(offlineBanner);

  window.addEventListener('offline', () => {
    offlineBanner.classList.remove('d-none');
    // Save pending form data to localStorage
    document.querySelectorAll('form:not([method="get"])').forEach(form => {
      const data = new FormData(form);
      const obj = {};
      data.forEach((v, k) => { if (k !== 'csrfmiddlewaretoken' && k !== 'archivo') obj[k] = v; });
      if (Object.keys(obj).length > 0) {
        localStorage.setItem('pending_form_' + (form.action || window.location.pathname), JSON.stringify(obj));
      }
    });
  });

  window.addEventListener('online', () => {
    offlineBanner.classList.add('d-none');
  });

  // Table row clickable (for rows with data-href)
  document.querySelectorAll('tr[data-href]').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', (e) => {
      if (!e.target.closest('a, button')) window.location.href = row.dataset.href;
    });
  });

  // Confirm before dangerous actions
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Sidebar mobile toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      document.getElementById('sidebarMenu').classList.toggle('show');
    });
  }

  // Search input debounce for live filtering
  const liveSearch = document.getElementById('liveSearch');
  if (liveSearch) {
    liveSearch.addEventListener('input', debounce(function() {
      const q = this.value.toLowerCase();
      document.querySelectorAll('[data-searchable]').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    }, 200));
  }
});

function debounce(fn, delay) {
  let t;
  return function(...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), delay);
  };
}

// Format RUT chileno
function formatRUT(rut) {
  rut = rut.replace(/\./g, '').replace(/-/g, '');
  if (rut.length < 2) return rut;
  const body = rut.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const dv = rut.slice(-1);
  return `${body}-${dv}`;
}

// RUT input auto-format
document.querySelectorAll('input[name="rut"]').forEach(input => {
  input.addEventListener('blur', function() {
    if (this.value) this.value = formatRUT(this.value);
  });
});
