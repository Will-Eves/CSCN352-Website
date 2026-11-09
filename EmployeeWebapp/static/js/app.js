/* ============================================================
   Rage N Raze — IT Asset Management
   Client-side JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initFlashMessages();
  initSidebarToggle();
  initTableSort();
  initSearchDebounce();
  initFormValidation();
});

/* =============================================================
   MODAL OPEN / CLOSE
   ============================================================= */
function openModal(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  // close on backdrop click
  overlay.addEventListener('click', function handler(e) {
    if (e.target === overlay) {
      closeModal(id);
      overlay.removeEventListener('click', handler);
    }
  });
  // close on Escape
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') {
      closeModal(id);
      document.removeEventListener('keydown', handler);
    }
  });
}

function closeModal(id) {
  const overlay = document.getElementById(id);
  if (!overlay) return;
  overlay.classList.remove('open');
  document.body.style.overflow = '';
}

/* =============================================================
   FLASH MESSAGES
   ============================================================= */
function initFlashMessages() {
  const flashes = document.querySelectorAll('.flash-msg');
  flashes.forEach(flash => {
    // auto-dismiss after 5 seconds
    const timer = setTimeout(() => dismissFlash(flash), 5000);
    // click dismiss
    const btn = flash.querySelector('.flash-dismiss');
    if (btn) {
      btn.addEventListener('click', () => {
        clearTimeout(timer);
        dismissFlash(flash);
      });
    }
  });
}

function dismissFlash(el) {
  el.style.opacity = '0';
  el.style.transform = 'translateX(-10px)';
  el.style.transition = 'opacity .3s, transform .3s';
  setTimeout(() => el.remove(), 300);
}

/* =============================================================
   SEARCH DEBOUNCE
   ============================================================= */
function initSearchDebounce() {
  const searchInput = document.querySelector('.search-box input[name="q"]');
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const form = searchInput.closest('form');
      if (form) form.submit();
    }, 300);
  });
}

/* =============================================================
   DELETE CONFIRMATION
   ============================================================= */
function confirmDelete(formId, itemName) {
  const msg = `Are you sure you want to delete "${itemName}"?\n\nThis action cannot be undone.`;
  if (confirm(msg)) {
    const form = document.getElementById(formId);
    if (form) form.submit();
  }
}

/* =============================================================
   SIDEBAR TOGGLE (MOBILE)
   ============================================================= */
function initSidebarToggle() {
  const toggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('open');
    toggle.innerHTML = sidebar.classList.contains('open') ? '✕' : '☰';
  });

  // close sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
        toggle.innerHTML = '☰';
      }
    }
  });
}

/* =============================================================
   TABLE SORT (CLIENT-SIDE)
   ============================================================= */
function initTableSort() {
  const tables = document.querySelectorAll('table.data-table');
  tables.forEach(table => {
    const headers = table.querySelectorAll('thead th[data-sort]');
    headers.forEach((th, colIndex) => {
      // add sort arrow indicator
      const arrow = document.createElement('span');
      arrow.className = 'sort-arrow';
      arrow.textContent = ' ⇅';
      th.appendChild(arrow);

      th.addEventListener('click', () => {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        const sortKey = th.dataset.sort;
        const isAsc = th.classList.contains('sort-asc');

        // reset all headers
        headers.forEach(h => {
          h.classList.remove('sort-asc', 'sort-desc');
          const a = h.querySelector('.sort-arrow');
          if (a) { a.textContent = ' ⇅'; a.classList.remove('active'); }
        });

        // determine actual column index from data-sort
        const allTh = Array.from(table.querySelectorAll('thead th'));
        const realIndex = allTh.indexOf(th);

        rows.sort((a, b) => {
          const aCell = a.children[realIndex];
          const bCell = b.children[realIndex];
          if (!aCell || !bCell) return 0;

          let aVal = (aCell.dataset.sortValue || aCell.textContent).trim().toLowerCase();
          let bVal = (bCell.dataset.sortValue || bCell.textContent).trim().toLowerCase();

          // try numeric
          const aNum = parseFloat(aVal);
          const bNum = parseFloat(bVal);
          if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? bNum - aNum : aNum - bNum;
          }

          // string
          if (isAsc) return bVal.localeCompare(aVal);
          return aVal.localeCompare(bVal);
        });

        // apply sort
        rows.forEach(row => tbody.appendChild(row));

        // update indicator
        th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
        arrow.textContent = isAsc ? ' ↓' : ' ↑';
        arrow.classList.add('active');
      });
    });
  });
}

/* =============================================================
   FORM VALIDATION
   ============================================================= */
function initFormValidation() {
  const forms = document.querySelectorAll('form[data-validate]');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      let valid = true;
      const requiredFields = form.querySelectorAll('[required]');

      // clear previous errors
      form.querySelectorAll('.field-error').forEach(el => el.remove());
      form.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));

      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          valid = false;
          field.classList.add('input-error');
          field.style.borderColor = '#ef4444';

          const errorSpan = document.createElement('span');
          errorSpan.className = 'field-error';
          errorSpan.style.cssText = 'color:#ef4444;font-size:.75rem;display:block;margin-top:3px;';
          errorSpan.textContent = 'This field is required';
          field.parentNode.appendChild(errorSpan);

          // remove error on input
          field.addEventListener('input', function handler() {
            field.style.borderColor = '';
            field.classList.remove('input-error');
            const err = field.parentNode.querySelector('.field-error');
            if (err) err.remove();
            field.removeEventListener('input', handler);
          });
        }
      });

      if (!valid) {
        e.preventDefault();
        // scroll to first error
        const firstErr = form.querySelector('.input-error');
        if (firstErr) firstErr.focus();
      }
    });
  });
}

/* =============================================================
   EDIT MODE TOGGLE (Detail Page)
   ============================================================= */
function toggleEditMode() {
  const viewSection = document.querySelector('.view-section');
  const editSection = document.querySelector('.edit-section');
  if (!viewSection || !editSection) return;

  viewSection.classList.toggle('hidden');
  editSection.classList.toggle('active');
}

/* =============================================================
   CATEGORY EDIT MODAL — fill form with current values
   ============================================================= */
function openEditCategoryModal(id, name, description) {
  const form = document.getElementById('editCategoryForm');
  if (form) {
    form.action = '/categories/' + id + '/edit';
    const nameInput = form.querySelector('[name="name"]');
    const descInput = form.querySelector('[name="description"]');
    if (nameInput) nameInput.value = name;
    if (descInput) descInput.value = description;
  }
  openModal('editCategoryModal');
}
