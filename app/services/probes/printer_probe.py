import socket
from typing import Dict, Any
from services.snmp_service import SNMPService
from .base_probe import BaseProbe

class PrinterProbe(BaseProbe):
    """Пробник принтеров (SNMP prtGeneral, JetDirect)."""

    def __init__(self):
        self.snmp = SNMPService(timeout=1.5, retries=0)

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        info = {"type": "printer", "ip": ip, "mac": mac}

        # Основной SNMP принтера
        oids = {
            "model": "1.3.6.1.2.1.43.5.1.1.16.1",
            "serial": "1.3.6.1.2.1.43.5.1.1.17.1",
            "uptime": "1.3.6.1.2.1.1.3.0",
        }

        for key, oid in oids.items():
            r = await self.snmp._snmp_get_once(ip, oid)
            if "value" in r:
                info[key] = r["value"]

        # Пробуем JetDirect порт
        try:
            s = socket.socket()
            s.settimeout(0.5)
            s.connect((ip, 9100))
            info["jetdirect"] = True
            s.close()
        except:
            info["jetdirect"] = False

        return info