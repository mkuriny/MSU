from typing import Dict, Any
from device_profiles.router_profile import RouterProfile
from device_profiles.switch_profile import SwitchProfile
from device_profiles.ap_profile import AccessPointProfile
from device_profiles.printer_profile import PrinterProfile
from device_profiles.default_profile import DefaultProfile


# Префиксы MAC -> предполагаемый тип производителя
OUI_MAP = {
    # MikroTik
    "DC:2C:6E": "router",
    "4C:5E:0C": "router",

    # TP-Link
    "F4:F2:6D": "router",
    "F0:9F:C2": "router",

    # D-Link
    "C8:BE:19": "router",
    "C4:12:F5": "switch",

    # Ubiquiti
    "24:A4:3C": "ap",
    "68:72:51": "ap",

    # HikVision
    "AC:64:62": "camera",

    # Dahua
    "3C:EF:8C": "camera",

    # HP printers
    "18:60:24": "printer",
    "5C:49:79": "printer",
}


def normalize_mac(mac: str) -> str:
    """
    Приводит MAC адрес к стандартному формату "XX:XX:XX"
    """
    if not mac:
        return ""
    mac = mac.upper().replace("-", ":")
    parts = mac.split(":")
    if len(parts) < 3:
        return ""
    return ":".join(parts[:3])

def resolve_profile(device_info: Dict[str, Any]):
    print(device_info)
    """
    Главный метод выбора профиля.
    Получает сведения об устройстве, анализирует и возвращает объект профиля.
    """
    
    mac = device_info.get("mac", "")
    snmp_data = device_info.get("snmp", {})

    vendor_guess = None

    # 1. Попытка определить по OUI (MAC префиксу)
    oui = normalize_mac(mac)
    if oui in OUI_MAP:
        vendor_guess = OUI_MAP[oui]

    # 2. Попытка определить по sysDescr (SNMP)

    sysdescr = ""
    if isinstance(snmp_data, dict):

        sysdescr = snmp_data.get("1.3.6.1.2.1.1.1.0", {}).get("value", "")


    sysdescr_l = sysdescr.lower()

    # --- Определение устройства по SNMP ---
    if "mikrotik" in sysdescr_l:
        return RouterProfile(device_info)

    if "router" in sysdescr_l or "gateway" in sysdescr_l:
        return RouterProfile(device_info)

    if "switch" in sysdescr_l:
        return SwitchProfile(device_info)

    if "access point" in sysdescr_l or "wireless" in sysdescr_l or "wlan" in sysdescr_l:
        return AccessPointProfile(device_info)

    if "camera" in sysdescr_l:
        return CameraProfile(device_info)

    if "printer" in sysdescr_l or "hp" in sysdescr_l:
        return PrinterProfile(device_info)

    # --- По результатам OUI ---
    if vendor_guess == "router":
        return RouterProfile(device_info)

    if vendor_guess == "switch":
        return SwitchProfile(device_info)

    if vendor_guess == "ap":
        return AccessPointProfile(device_info)

    if vendor_guess == "camera":
        return CameraProfile(device_info)

    if vendor_guess == "printer":
        return PrinterProfile(device_info)

    # --- Ничего не подошло — возвращаем DefaultProfile ---
    return DefaultProfile
