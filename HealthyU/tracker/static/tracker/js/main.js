function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');

  let cssClass = 'toast-success';
  if (type === 'error' || type === 'warning' || type === 'danger') {
    cssClass = 'toast-error';
  }

  toast.className = 'custom-toast ' + cssClass;
  const icon = (type === 'error' || type === 'warning' || type === 'danger') ? '⚠️' : '✅';

  toast.innerHTML =
    '<div style="display:flex; align-items:center; gap:10px;">' +
    '<span style="font-size:18px;">' + icon + '</span>' +
    '<span>' + message + '</span>' +
    '</div>' +
    '<button aria-label="Close" ' +
    'style="background:none;border:none;color:white;cursor:pointer;opacity:0.8;font-size:18px;line-height:1;">' +
    '&times;' +
    '</button>';

  // Close handler
  toast.querySelector('button').addEventListener('click', () => {
    toast.style.animation = 'fadeOutToast 0.3s forwards';
    setTimeout(() => toast.remove(), 300);
  });

  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.animation = 'fadeOutToast 0.5s forwards';
      setTimeout(() => toast.remove(), 500);
    }
  }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  (window.__DJANGO_MESSAGES__ || []).forEach(m => {
    if (m.text && m.text.trim()) showToast(m.text, m.tags);
  });
});

// Optional (if you use half modal somewhere)
function showHalfModal() {
  const el = document.getElementById("halfCompleteModal");
  if (el) el.style.display = "flex";
}
function closeModal() {
  const el = document.getElementById("halfCompleteModal");
  if (el) el.style.display = "none";
}
