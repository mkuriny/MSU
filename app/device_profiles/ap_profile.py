from .base_profile import BaseProfile

class AccessPointProfile(BaseProfile):

    async def scan(self, snmp):
        """Сканирование точки доступа через SNMP."""
        return await snmp.get_many(self.ip, [
            "1.3.6.1.4.1.9.9.513.1.1.1.0",   # пример: количество клиентов (Cisco)
            "1.3.6.1.2.1.1.1.0",             # sysDescr
            "1.3.6.1.2.1.1.5.0",             # sysName
        ])