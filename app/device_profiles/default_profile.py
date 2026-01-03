
from .base_profile import BaseProfile


class DefaultProfile(BaseProfile):
    """
    Если тип устройства неизвестен — выполняем минимальный опрос.
    """
    def __init__(self, ip, mac=None):
        super().__init__(ip, mac)
    async def detect(self, snmp):
        return {"type": "unknown"}

    async def fetch_info(self, snmp):
        return {}

    async def scan(self, snmp):
        """
        Сканирование по умолчанию — только базовые данные SNMP.
        """
        return await snmp.get_many(self.ip, [
            "1.3.6.1.2.1.1.1.0",
            "1.3.6.1.2.1.1.5.0",
        ])
