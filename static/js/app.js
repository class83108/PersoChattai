/* PersoChattai — shared JS */

// HTMX configuration
document.addEventListener('htmx:configRequest', () => {
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

// --- User Identity ---

function getUserId() {
  return localStorage.getItem('persochattai_user_id');
}

function getDisplayName() {
  return localStorage.getItem('persochattai_display_name');
}

function setUser(id, displayName) {
  localStorage.setItem('persochattai_user_id', id);
  localStorage.setItem('persochattai_display_name', displayName);
  updateUserBadge(displayName);
}

function clearUser() {
  localStorage.removeItem('persochattai_user_id');
  localStorage.removeItem('persochattai_display_name');
  const badge = document.getElementById('user-badge');
  if (badge) badge.classList.add('hidden');
}

function updateUserBadge(name) {
  const badge = document.getElementById('user-badge');
  const nameEl = document.getElementById('user-display-name');
  if (badge && nameEl) {
    nameEl.textContent = name;
    badge.classList.remove('hidden');
  }
}

function showNicknameModal() {
  const modal = document.getElementById('nickname-modal');
  if (modal) {
    modal.showModal();
    const input = document.getElementById('nickname-input');
    if (input) {
      input.value = '';
      input.focus();
    }
    const errorEl = document.getElementById('nickname-error');
    if (errorEl) errorEl.classList.add('hidden');
  }
}

async function submitNickname() {
  const input = document.getElementById('nickname-input');
  const errorEl = document.getElementById('nickname-error');
  const errorMsg = document.getElementById('nickname-error-msg');
  const name = (input.value || '').trim();

  if (!name) {
    errorMsg.textContent = '請輸入暱稱';
    errorEl.classList.remove('hidden');
    return;
  }

  try {
    const resp = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: name }),
    });

    if (resp.status === 422) {
      const data = await resp.json();
      errorMsg.textContent = data.detail?.[0]?.msg || data.detail || '暱稱格式不正確';
      errorEl.classList.remove('hidden');
      return;
    }

    if (!resp.ok) {
      errorMsg.textContent = '系統錯誤，請稍後再試';
      errorEl.classList.remove('hidden');
      return;
    }

    const user = await resp.json();
    setUser(user.id, user.display_name);
    document.getElementById('nickname-modal').close();
  } catch {
    errorMsg.textContent = '網路錯誤，請檢查連線';
    errorEl.classList.remove('hidden');
  }
}

function switchUser() {
  clearUser();
  showNicknameModal();
}

// --- Init: verify user on page load ---

async function initUser() {
  const uid = getUserId();
  const name = getDisplayName();

  if (!uid || !name) {
    clearUser();
    showNicknameModal();
    return;
  }

  try {
    const resp = await fetch(`/api/users/${uid}`);
    if (resp.ok) {
      updateUserBadge(name);
    } else {
      clearUser();
      showNicknameModal();
    }
  } catch {
    // Network error — still show badge with cached name
    updateUserBadge(name);
  }
}

document.addEventListener('DOMContentLoaded', initUser);

// Expose globally
window.getUserId = getUserId;
window.switchUser = switchUser;
window.submitNickname = submitNickname;
