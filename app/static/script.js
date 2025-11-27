
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

/* ---------- Загрузка и отображение устройств ---------- */
async function loadDevices() {
  try {
    const res = await safeFetch("/devices");
    const devices = Array.isArray(res) ? res : [];
    const container = document.getElementById("devicesContainer");
    container.innerHTML = "";

    let onlineCount = 0;
    devices.forEach(d => {
      const isOnline = d.UpTime && d.UpTime !== "Unknown" && d.UpTime !== "—";
      if (isOnline) onlineCount++;

      const card = document.createElement("div");
      card.className = "device-card " + (isOnline ? "online" : "offline");
      card.innerHTML = `
		<div class="status-label">${isOnline ? "ONLINE" : "OFFLINE"}</div>
		<button class="delete-btn" title="Удалить устройство">🗑️</button>
		<h3>${d.Name || "Unknown"}</h3>
		<p><strong>Описание:</strong> ${d.Description || "—"}</p>
		<p><strong>Местоположение:</strong> ${d.Location || "—"}</p>
		<p><strong>Время работы:</strong> ${d.UpTime || "—"}</p>
		<p><strong>Время обновления:</strong> ${d.UpdateTime || "—"}</p>
		<p><strong>Прошивка:</strong> ${d.OC || "—"}</p>
		<p><strong>Лог:</strong> ${d.Log || "—"}</p>
		<p><strong>MAC:</strong> ${d.MAC || "—"}</p>
	`;
	card.querySelector(".delete-btn").addEventListener("click", async () => {
		if (!confirm(`Удалить устройство "${d.Name}"?`)) return;

		const res = await fetch(`/devices/${encodeURIComponent(d.Name)}`, {
			method: "DELETE"
		});

		if (res.ok) {
			card.remove(); // удалить из интерфейса
			a
			loadDevices();
		} else {
			const err = await res.json();
			alert(`Ошибка: ${err.detail || "Не удалось удалить устройство"}`);
		}
	});
      container.appendChild(card);
    });

    document.getElementById("online-count").textContent = `${onlineCount} онлайн`;
    document.getElementById("total-count").textContent = `${devices.length} всего`;
    document.getElementById("last-update").textContent = "Обновление: " + new Date().toLocaleTimeString();
  } catch (err) {
    console.error("loadDevices error:", err);
    // не ломаем UI — просто покажем в консоли
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
  // Сканировать (использует текущий конфиг на сервере)
  document.getElementById("refreshBtn").addEventListener("click", async () => {
    try {
      const scanBtn = document.getElementById("refreshBtn");
      scanBtn.disabled = true;
      const res = await safeFetch(SCAN_URL, { method: "POST" });
      console.log("SNMP scan result:", res);
      await loadDevices();
      // можно показать уведомление с res.summary, но оставлю консоль
    } catch (err) {
      alert("Ошибка при запуске сканирования: " + err.message);
    } finally {
      document.getElementById("refreshBtn").disabled = false;
    }
  });

  // Показ/скрытие формы + загрузка конфигурации при открытии
  const snmpModal = document.getElementById("snmpModal");
	document.getElementById("snmp-settings-btn").addEventListener("click", async () => {
		snmpModal.style.display = "flex";
		await loadSnmpConfig();
	});

  // Кнопки в форме
  document.getElementById("saveSettingsBtn").addEventListener("click", saveSnmpConfig);
  document.getElementById("cancelSettingsBtn").addEventListener("click", () => {
	  snmpModal.style.display = "none";
	  loadSnmpConfig();
	});
  document.getElementById("defaultSettingsBtn").addEventListener("click", resetSnmpDefaults);
}
	snmpModal.addEventListener("click", (e) => {
	  if (e.target === snmpModal) {
		snmpModal.style.display = "none";
	  }
	});
/* ---------- Инициализация страницы ---------- */
window.addEventListener("DOMContentLoaded", () => {
  // Начальная загрузка устройств и привязка обработчиков
  loadDevices();
  initUiHandlers();
});

