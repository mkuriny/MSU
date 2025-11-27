class NetworkMonitor {
    constructor() {
        this.ws = null;
        this.devices = [];
        this.init();
    }

    async init() {
        await this.loadInitialDevices();
        this.connectWebSocket();
        this.setupEventListeners();
    }

    async loadInitialDevices() {
        try {
            const response = await fetch('/api/v1/devices');
            if (response.ok) {
                this.devices = await response.json();
                this.renderDevices();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/devices`);
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'devices_update') {
                    this.devices = data.devices;
                    this.renderDevices();
                    this.updateStats();
                    document.getElementById('last-update').textContent = 
                        `Обновление: ${new Date().toLocaleTimeString()}`;
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        this.ws.onclose = () => {
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    setupEventListeners() {
        document.getElementById('scan-btn').addEventListener('click', () => {
            this.scanNetwork();
        });

        document.getElementById('add-device-btn').addEventListener('click', () => {
            this.showAddDeviceForm();
        });

        document.getElementById('snmp-settings-btn').addEventListener('click', () => {
            this.showSnmpSettings();
        });
    }

    async scanNetwork() {
        try {
            const response = await fetch('/api/v1/devices/scan', { method: 'POST' });
            if (response.ok) {
                alert('Сканирование сети запущено');
            }
        } catch (error) {
            console.error('Error scanning network:', error);
        }
    }

    async deleteDevice(deviceId) {
        if (confirm('Удалить это устройство?')) {
            try {
                const response = await fetch(`/api/v1/devices/${deviceId}`, { method: 'DELETE' });
                if (response.ok) {
                    await this.loadInitialDevices();
                }
            } catch (error) {
                console.error('Error deleting device:', error);
            }
        }
    }

    showAddDeviceForm() {
        const form = `
            <div class="modal">
                <div class="modal-content">
                    <h3>Добавить устройство</h3>
                    <input type="text" id="device-ip" placeholder="IP адрес">
                    <input type="text" id="device-mac" placeholder="MAC адрес">
                    <input type="text" id="device-name" placeholder="Имя устройства">
                    <button onclick="networkMonitor.addDevice()">Добавить</button>
                    <button onclick="this.closest('.modal').remove()">Отмена</button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', form);
    }

    async addDevice() {
        const ip = document.getElementById('device-ip').value;
        const mac = document.getElementById('device-mac').value;
        const name = document.getElementById('device-name').value;

        try {
            const response = await fetch('/api/v1/devices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ip_address: ip,
                    mac_address: mac,
                    hostname: name
                })
            });

            if (response.ok) {
                document.querySelector('.modal').remove();
                await this.loadInitialDevices();
            }
        } catch (error) {
            console.error('Error adding device:', error);
        }
    }

    showSnmpSettings() {
        const form = `
            <div class="modal">
                <div class="modal-content">
                    <h3>Настройки SNMP</h3>
                    <label>Community String:</label>
                    <input type="text" id="snmp-community" value="public">
                    <label>Timeout (сек):</label>
                    <input type="number" id="snmp-timeout" value="2">
                    <label>Retries:</label>
                    <input type="number" id="snmp-retries" value="1">
                    <button onclick="networkMonitor.saveSnmpSettings()">Сохранить</button>
                    <button onclick="this.closest('.modal').remove()">Отмена</button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', form);
        
        this.loadSnmpSettings();
    }

    async loadSnmpSettings() {
        try {
            const response = await fetch('/api/v1/snmp/settings');
            if (response.ok) {
                const settings = await response.json();
                document.getElementById('snmp-community').value = settings.community;
                document.getElementById('snmp-timeout').value = settings.timeout;
                document.getElementById('snmp-retries').value = settings.retries;
            }
        } catch (error) {
            console.error('Error loading SNMP settings:', error);
        }
    }

    async saveSnmpSettings() {
        const community = document.getElementById('snmp-community').value;
        const timeout = parseInt(document.getElementById('snmp-timeout').value);
        const retries = parseInt(document.getElementById('snmp-retries').value);

        try {
            const response = await fetch('/api/v1/snmp/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ community, timeout, retries, enabled: true })
            });

            if (response.ok) {
                alert('Настройки SNMP сохранены');
                document.querySelector('.modal').remove();
            }
        } catch (error) {
            console.error('Error saving SNMP settings:', error);
        }
    }

    renderDevices() {
        const container = document.getElementById('devices-container');
        
        if (this.devices.length === 0) {
            container.innerHTML = `
                <div class="no-devices">
                    <h3>Устройства не найдены</h3>
                    <p>Сканирование сети выполняется каждые 60 секунд.</p>
                    <p>Нажмите "Сканировать сеть" для ручного сканирования.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.devices.map(device => `
            <div class="device-card ${device.is_online ? 'online' : 'offline'}">
                <div class="device-header">
                    <div class="device-status ${device.is_online ? 'status-online' : 'status-offline'}">
                        ${device.is_online ? 'ONLINE' : 'OFFLINE'}
                    </div>
                    <button class="delete-btn" onclick="networkMonitor.deleteDevice('${device.id}')">🗑️</button>
                </div>
                <h3>${device.hostname || device.ip_address}</h3>
                <div class="device-info">
                    <p><strong>IP:</strong> ${device.ip_address}</p>
                    <p><strong>MAC:</strong> ${device.mac_address || 'Unknown'}</p>
                    <p><strong>Производитель:</strong> ${device.vendor || 'Unknown'}</p>
                    <p><strong>Обновлено:</strong> ${new Date(device.last_seen).toLocaleString()}</p>
                </div>
            </div>
        `).join('');
    }

    updateStats() {
        const onlineCount = this.devices.filter(d => d.is_online).length;
        document.getElementById('online-count').textContent = `${onlineCount} онлайн`;
        document.getElementById('total-count').textContent = `${this.devices.length} всего`;
    }
}

let networkMonitor;
document.addEventListener('DOMContentLoaded', () => {
    networkMonitor = new NetworkMonitor();
});
