let CURRENT_USER = null;
function applyRoleUI(role) {
  const btnScan = document.getElementById("refreshBtn");
  const btnAddDevice = document.getElementById("add-device-btn");
  const btnUsers = document.querySelector("button[onclick='openUsers()']");
  const btnSnmp = document.getElementById("snmp-settings-btn");
  // monitor — только просмотр
  if (role === "monitor") {
    btnScan?.remove();
    btnAddDevice?.remove();
    btnUsers?.remove();
	btnSnmp?.remove();
    // убрать кнопки удаления устройств
    document.body.classList.add("role-monitor");
  }

  // user — всё кроме управления пользователями
  if (role === "user") {
    btnUsers?.remove();
  }
}
async function loadCurrentUser() {
  try {
    CURRENT_USER = await safeFetch("/auth/me");
    applyRoleUI(CURRENT_USER.role);
  } catch (e) {
    console.error("Не удалось получить пользователя", e);
  }
}
/* ---------- Утилиты ---------- */
async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const text = await res.text().catch(()=>null);
      throw new Error(`${res.status} ${res.statusText} ${text ? ' - '+text : ''}`);
    }
    // try json, else text
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return await res.json();
    return await res.text();
  } catch (err) {
    console.error("Fetch error:", url, err);
    throw err;
  }
}

async function logout() {
    await fetch("/auth/logout", { method: "POST" });
    window.location.href = "/auth/login";
}
/* ---------- Загрузка и отображение устройств ---------- */
async function loadDevices() {
  try {
    const devices = await safeFetch("/devices");
    const container = document.getElementById("devicesContainer");
    container.innerHTML = "";

    let onlineCount = 0;

    devices.forEach(d => {
      const card = document.createElement("div");
      card.className = "device-card";

      const isOnline = d.UpTime && d.UpTime !== "N/A";
      if (isOnline) onlineCount++;

      card.innerHTML = `
        <div class="status-label">${isOnline ? "ONLINE" : "OFFLINE"}</div>
        ${
          CURRENT_USER?.role !== "monitor"
            ? `<button class="delete-btn" title="Удалить устройство">🗑️</button>`
            : ""
        }
        <h3>${escapeHtml(d.Name || "Unknown")}</h3>
        <p>${escapeHtml(d.Description || "")}</p>
        <p><b>IP:</b> ${escapeHtml(d.Location || "")}</p>
        <p><b>MAC:</b> ${escapeHtml(d.MAC || "")}</p>
      `;

      if (CURRENT_USER?.role !== "monitor") {
        const deleteBtn = card.querySelector(".delete-btn");
        deleteBtn?.addEventListener("click", async () => {
          if (!confirm(`Удалить устройство "${d.Name}"?`)) return;
          await fetch(`/devices/${encodeURIComponent(d.Name)}`, { method: "DELETE" });
          loadDevices();
        });
      }

      container.appendChild(card);
    });

    document.getElementById("online-count").textContent =
      `${onlineCount} онлайн`;
    document.getElementById("total-count").textContent =
      `${devices.length} всего`;
    document.getElementById("last-update").textContent =
      "Обновление: " + new Date().toLocaleTimeString();

  } catch (err) {
    console.error("loadDevices error:", err);
  }
}


/* Эскейп для вывода в HTML (простая) */
function escapeHtml(str) {
  if (typeof str !== "string") return str;
  return str.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

/* ---------- SNMP: работа с конфигом ---------- */
const CONFIG_URL = "/snmp/config";
const SAVE_URL = "/snmp/config/save";
const DEFAULTS_URL = "/snmp/config/defaults";
const SCAN_URL = "/snmp/scan";

async function loadSnmpConfig() {
  try {
    const cfg = await safeFetch(CONFIG_URL);
    // Заполняем поля; учитываем что v3_user может быть null
    document.getElementById("ipRange").value = cfg.ip_range ?? "";
    document.getElementById("timeout").value = cfg.timeout ?? 2;
    document.getElementById("retries").value = cfg.retries ?? 0;
    document.getElementById("community").value = cfg.community ?? "public";
    const v3 = cfg.v3_user || {};
    document.getElementById("v3_user").value = v3.user ?? "";
    document.getElementById("authKey").value = v3.authKey ?? "";
    document.getElementById("authProtocol").value = v3.authProtocol ?? "";
    document.getElementById("privKey").value = v3.privKey ?? "";
    document.getElementById("privProtocol").value = v3.privProtocol ?? "";
  } catch (err) {
    alert("Не удалось загрузить SNMP-конфигурацию. Проверь backend (см. консоль).");
  }
}

async function saveSnmpConfig() {
  const btn = document.getElementById("saveSettingsBtn");
  try {
    btn.disabled = true;
    const cfg = collectCfgFromForm();
    await safeFetch(SAVE_URL, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(cfg)
    });
    alert("Настройки сохранены");
  } catch (err) {
    alert("Ошибка сохранения: " + err.message);
  } finally {
    btn.disabled = false;
  }
}

async function resetSnmpDefaults() {
  const btn = document.getElementById("defaultSettingsBtn");
  try {
    btn.disabled = true;
    await safeFetch(DEFAULTS_URL, { method: "POST" });
    await loadSnmpConfig();
    alert("Настройки восстановлены по умолчанию");
  } catch (err) {
    alert("Ошибка сброса: " + err.message);
  } finally {
    btn.disabled = false;
  }
}

function collectCfgFromForm() {
  return {
    ip_range: document.getElementById("ipRange").value,
    timeout: parseFloat(document.getElementById("timeout").value || 2),
    retries: parseInt(document.getElementById("retries").value || 0),
    community: document.getElementById("community").value || "public",
    v3_user: (document.getElementById("v3_user").value) ? {
      user: document.getElementById("v3_user").value,
      authKey: document.getElementById("authKey").value || null,
      authProtocol: document.getElementById("authProtocol").value || null,
      privKey: document.getElementById("privKey").value || null,
      privProtocol: document.getElementById("privProtocol").value || null
    } : null
  };
}

/* ---------- UI: события ---------- */
function initUiHandlers() {
  const snmpModal = document.getElementById("snmpModal");
  const usersModal = document.getElementById("usersModal");
  const addUserModal = document.getElementById("addUserModal");

  /* ---------- SNMP ---------- */
  document.getElementById("snmp-settings-btn")
    .addEventListener("click", async () => {
      snmpModal.style.display = "flex";
      await loadSnmpConfig();
    });

  document.getElementById("cancelSettingsBtn")
    .addEventListener("click", () => {
      snmpModal.style.display = "none";
      loadSnmpConfig();
    });

  /* ---------- USERS ---------- */
  document.getElementById("openAddUserBtn")
    ?.addEventListener("click", openAddUser);

  document.getElementById("closeUsersBtn")
    ?.addEventListener("click", closeUsers);

  /* ---------- NEW USER ---------- */
  document.getElementById("createUserBtn")
    ?.addEventListener("click", createUser);

  document.getElementById("closeAddUserBtn")
    ?.addEventListener("click", closeAddUser);
  document.getElementById("refreshBtn")
  .addEventListener("click", scanNetwork);
  document.getElementById("add-device-btn")
  ?.addEventListener("click", openAddDevice);

document.getElementById("createDeviceBtn")
  ?.addEventListener("click", createDevice);

document.getElementById("closeAddDeviceBtn")
  ?.addEventListener("click", closeAddDevice);
}



/* ---------- Список пользователей ---------- */
async function openUsers() {
    const res = await fetch("/users/list");
    const data = await res.json();

    let html = '<div class="users-list">';

	for (const role in data) {
		html += `<h4>${role}</h4><ul>`;
		data[role].forEach(u => {
			html += `
			  <li class="${u.active ? "" : "user-disabled"}">
				<span>${u.username}</span>
				<span class="user-actions">
				  <button title="Вкл/выкл" onclick="toggleUser(${u.id})">🔒</button>
				  <button title="Удалить" onclick="deleteUser(${u.id})">🗑</button>
				</span>
			  </li>`;
		});
		html += "</ul>";
	}

	html += "</div>";

    document.getElementById("usersList").innerHTML = html;
    document.getElementById("usersModal").classList.remove("hidden");
}
/* ---------- Создать пользователя ---------- */
async function createUser() {
    const login = document.getElementById("newLogin").value;
	const p1 = document.getElementById("newPass").value;
	const p2 = document.getElementById("newPass2").value;
	const role = document.getElementById("newRole").value;
	const addUserError = document.getElementById("addUserError");

    if (p1 !== p2) {
        addUserError.innerText = "Пароли не совпадают";
        return;
    }

    const data = new URLSearchParams();
    data.append("username", login);
    data.append("password", p1);
    data.append("role", role);

    const res = await fetch("/users/create", {
        method: "POST",
        body: data
    });

    if (res.ok) {
        closeAddUser();
        openUsers();
    } else {
        addUserError.innerText = "Ошибка создания";
    }
}
async function toggleUser(id) {
    await fetch(`/users/toggle/${id}`, { method: "POST" });
    openUsers();
}

async function deleteUser(id) {
    if (!confirm("Удалить пользователя?")) return;
    await fetch(`/users/${id}`, { method: "DELETE" });
    openUsers();
}
/* ---------- Управление модалками пользователей ---------- */

function openAddUser() {
    document.getElementById("addUserError").innerText = "";
    document.getElementById("newLogin").value = "";
    document.getElementById("newPass").value = "";
    document.getElementById("newPass2").value = "";
    document.getElementById("newRole").value = "user";

    document.getElementById("addUserModal").classList.remove("hidden");
}

function closeAddUser() {
    document.getElementById("addUserModal").classList.add("hidden");
}

function closeUsers() {
    document.getElementById("usersModal").classList.add("hidden");
}
async function scanNetwork() {
  const btn = document.getElementById("refreshBtn");
  try {
    btn.disabled = true;
    btn.textContent = "⏳ Сканирование...";

    await safeFetch("/snmp/scan", { method: "POST" });

    await loadDevices(); // обновляем список после скана
  } catch (err) {
    alert("Ошибка сканирования: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "🔍 Сканировать сеть";
  }
}
window.addEventListener("DOMContentLoaded", async () => {
  await loadCurrentUser();   // 👈 СНАЧАЛА роль
  loadDevices();
  initUiHandlers();
});


function openAddDevice() {
  document.getElementById("addDeviceError").innerText = "";
  document.getElementById("devIp").value = "";
  document.getElementById("devName").value = "";
  document.getElementById("devDesc").value = "";
  document.getElementById("devOs").value = "";
  document.getElementById("devMac").value = "";

  document.getElementById("addDeviceModal").classList.remove("hidden");
}

function closeAddDevice() {
  document.getElementById("addDeviceModal").classList.add("hidden");
}

async function createDevice() {
  const ip = document.getElementById("devIp").value.trim();
  const error = document.getElementById("addDeviceError");

  if (!ip) {
    error.innerText = "IP обязателен";
    return;
  }

  const data = new URLSearchParams();
  data.append("ip", ip);
  data.append("name", document.getElementById("devName").value || "—");
  data.append("description", document.getElementById("devDesc").value || "—");
  data.append("oc", document.getElementById("devOs").value || "—");
  data.append("mac", document.getElementById("devMac").value || "—");

  try {
    const res = await fetch("/devices/create", {
      method: "POST",
      body: data
    });

    if (!res.ok) {
      const t = await res.text();
      throw new Error(t);
    }

    closeAddDevice();
    loadDevices();
  } catch (e) {
    error.innerText = "Ошибка добавления устройства";
  }
}
