
import socket
from typing import Dict, Any
from services.snmp_service import SNMPService
from .base_probe import BaseProbe

class RouterProbe(BaseProbe):
    """Пробник роутеров (SNMP + HTTP banner)."""

    def __init__(self):
        self.snmp = SNMPService(timeout=1.5, retries=0)

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        info = {"type": "router", "ip": ip, "mac": mac}

        # 1) Пробуем SNMP
        snmp = await self.snmp._snmp_get_once(ip, "1.3.6.1.2.1.1.1.0")
        if "value" in snmp:
            info["snmp_sysdescr"] = snmp["value"]

        # 2) Пробуем HTTP баннер
        for port in (80, 8080, 8000, 443):
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect((ip, port))
                s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                data = s.recv(128).decode(errors="ignore")
                info["http_banner"] = data.strip()
                s.close()
                break
            except:
                pass

        return info