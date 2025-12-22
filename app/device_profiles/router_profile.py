from .base_profile import BaseProfile

class RouterProfile(BaseProfile):
    async def scan(self, snmp):
        return await snmp.get_many(self.ip, [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.5.0",  # sysName
            "1.3.6.1.2.1.4.20.1.1",  # IP info
        ])