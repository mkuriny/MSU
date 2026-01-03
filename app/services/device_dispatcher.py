from typing import Optional, Dict
from services.probes.snmp_probe import SNMPProbe
from services.probes.router_probe import RouterProbe
from services.probes.camera_probe import CameraProbe
from services.probes.printer_probe import PrinterProbe
from services.probes.generic_probe import GenericProbe


class DeviceDispatcher:
    """
    Диспетчер, который решает,
    какой пробник (SNMP, Router, Camera, Printer, ...)
    использовать для данного IP + MAC.
    """

    def __init__(self):
        # Инициализируем пробники
        self.snmp_probe = SNMPProbe()
        self.router_probe = RouterProbe()
        self.camera_probe = CameraProbe()
        self.printer_probe = PrinterProbe()
        self.generic_probe = GenericProbe()

        # Простейшая база OUI → тип устройства
        # (будет легко расширить)
        self.oui_map = {
            # маршрутизаторы (TP-Link, Asus, Keenetic)
            "C4-E9-84": "router",
            "B0-BE-76": "router",
            "C8-3A-35": "router",

            # IP-камеры HikVision/Dahua
            "AC-64-62": "camera",
            "DC-DF-D6": "camera",

            # принтеры HP/Brother/Kyocera
            "3C-D9-2B": "printer",
            "FC-EC-DA": "printer",
            "8C-8A-6E": "printer",

            # ПК (обычно Intel/Realtek)
            "C8-6E-08": "pc",
            "F8-75-A4": "pc",
        }

    # -------------------------------------------------------------

    def _get_oui(self, mac: str) -> Optional[str]:
        """Извлекает OUI (первые 3 байта MAC)."""
        if not mac or mac == "Unknown":
            return None
        mac = mac.upper().replace("-", ":")
        parts = mac.split(":")
        if len(parts) < 3:
            return None
        return "-".join(parts[:3])

    # -------------------------------------------------------------

    def _detect_type_by_mac(self, mac: str) -> str:
        """Определяет тип устройства по MAC-префиксу."""
        oui = self._get_oui(mac)
        if oui and oui in self.oui_map:
            return self.oui_map[oui]
        return "unknown"

    # -------------------------------------------------------------

    async def dispatch(self, ip: str, mac: str) -> Dict:
        """
        Главная точка входа.
        Получает IP + MAC, решает какой пробник вызывать.
        """

        # 1) Проверяем MAC по базе производителей
        dtype = self._detect_type_by_mac(mac)

        # ---------- SNMP устройства ----------
        if dtype == "pc":
            return await self.snmp_probe.probe(ip, mac)

        # ---------- Маршрутизаторы ----------
        if dtype == "router":
            return await self.router_probe.probe(ip, mac)

        # ---------- Камеры ----------
        if dtype == "camera":
            return await self.camera_probe.probe(ip, mac)

        # ---------- Принтеры ----------
        if dtype == "printer":
            return await self.printer_probe.probe(ip, mac)

        # ---------- Fallback: пробуем SNMP ----------
        snmp_try = await self.snmp_probe.probe(ip, mac)
        if any(snmp_try.get(k) for k in ("sysDescr", "sysName")):
            snmp_try["type"] = "snmp_device"
            return snmp_try

        # ---------- Генерация простого результата ----------
        return await self.generic_probe.probe(ip, mac)