import socket
from typing import Dict, Any
from services.snmp_service import SNMPService
from .base_probe import BaseProbe

class CameraProbe(BaseProbe):
    """Пробник IP-камер (RTSP + ONVIF + SNMP)."""

    def __init__(self):
        self.snmp = SNMPService(timeout=1.5, retries=0)

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        info = {"type": "camera", "ip": ip, "mac": mac}

        # RTSP
        try:
            s = socket.socket()
            s.settimeout(0.7)
            s.connect((ip, 554))
            info["rtsp_available"] = True
        except:
            info["rtsp_available"] = False

        # ONVIF (8000, 8001)
        for port in (8000, 8001):
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect((ip, port))
                info["onvif"] = True
                s.close()
                break
            except:
                info["onvif"] = False

        # SNMP fallback
        snmp = await self.snmp._snmp_get_once(ip, "1.3.6.1.2.1.1.1.0")
        if "value" in snmp:
            info["snmp_sysdescr"] = snmp["value"]

        return info