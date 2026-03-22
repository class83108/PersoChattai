/* PersoChattai — shared JS */

// HTMX configuration
document.addEventListener('htmx:configRequest', (event) => {
  // Add CSRF or custom headers here if needed in the future
});

// Update active nav state after HTMX swap
document.addEventListener('htmx:afterSettle', () => {
  updateActiveNav();
});

function updateActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('[data-nav-link]').forEach((link) => {
    const href = link.getAttribute('href');
    const isActive = path === href || (href !== '/' && path.startsWith(href));
    link.classList.toggle('active', isActive);
  });
}

// Initial nav state
document.addEventListener('DOMContentLoaded', updateActiveNav);
