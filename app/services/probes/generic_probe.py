
from typing import Dict, Any
from .base_probe import BaseProbe

class GenericProbe(BaseProbe):
    """Пробник по умолчанию, если тип неизвестен."""

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        return {
            "type": "unknown_device",
            "ip": ip,
            "mac": mac,
            "note": "Тип не определён, использован GenericProbe"
        }