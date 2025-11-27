
const btnLogin = document.getElementById('btn-login');
const btnLogout = document.getElementById('btn-logout');
const loginModal = document.getElementById('login-modal');
const loginForm = document.getElementById('login-form');
const loginCancel = document.getElementById('login-cancel');
const loginMsg = document.getElementById('login-msg');
const roleBadge = document.getElementById('role-badge');

function showModal() { loginModal.classList.remove('hidden'); loginModal.setAttribute('aria-hidden', 'false'); }
function hideModal() { loginModal.classList.add('hidden'); loginModal.setAttribute('aria-hidden', 'true'); }

btnLogin.addEventListener('click', () => { showModal(); });
loginCancel.addEventListener('click', () => { hideModal(); loginMsg.innerText=''; });

loginForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  loginMsg.innerText = '';
  const form = new FormData(loginForm);
  const data = new URLSearchParams();
  form.forEach((v,k) => data.append(k, v));

  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      body: data
    });
    if (!res.ok) {
      const txt = await res.text();
      loginMsg.innerText = 'Ошибка: ' + (txt || res.status);
      return;
    }
    const json = await res.json();
    // json: { token: "...", role: "admin" }
    localStorage.setItem('jwt', json.token);
    localStorage.setItem('role', json.role || 'viewer');
    applyRoleUI();
    hideModal();
    loginForm.reset();
  } catch (e) {
    loginMsg.innerText = 'Сетевой ошибка';
  }
});

// logout
btnLogout.addEventListener('click', () => {
  localStorage.removeItem('jwt');
  localStorage.removeItem('role');
  applyRoleUI();
});

// Применяем UI в зависимости от роли
function applyRoleUI() {
  const role = localStorage.getItem('role');
  if (!role) {
    roleBadge.className = 'badge badge-hidden';
    roleBadge.innerText = 'Не авторизован';
    btnLogin.classList.remove('hidden');
    btnLogout.classList.add('hidden');
    return;
  }
  btnLogin.classList.add('hidden');
  btnLogout.classList.remove('hidden');

  let cls = 'badge ';
  if (role === 'admin') cls += 'badge-admin';
  else if (role === 'operator') cls += 'badge-operator';
  else cls += 'badge-viewer';
  roleBadge.className = cls;
  roleBadge.innerText = role.toUpperCase();
}

// При загрузке страницы применим состояние (если пользователь уже залогинен)
applyRoleUI();