
from typing import Dict, Any
from services.snmp_service import SNMPService
from .base_probe import BaseProbe

class SNMPProbe(BaseProbe):
    """Пробник, который пытается получить sysName/sysDescr/MAC через SNMP."""

    def __init__(self):
        self.snmp = SNMPService(timeout=1.5, retries=0)

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        oids = {
            "sysDescr": "1.3.6.1.2.1.1.1.0",
            "sysName": "1.3.6.1.2.1.1.5.0",
            "uptime": "1.3.6.1.2.1.1.3.0",
        }

        result = {}
        for key, oid in oids.items():
            r = await self.snmp._snmp_get_once(ip, oid)
            result[key] = r.get("value")

        result["type"] = "snmp_device"
        result["ip"] = ip
        result["mac"] = mac
        return result