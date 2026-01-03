from .base_profile import BaseProfile
class SwitchProfile(BaseProfile):
    async def scan(self, snmp):
        return await snmp.get_many(self.ip, [
            "1.3.6.1.2.1.17.1.1.0", # bridge MIB
            "1.3.6.1.2.1.2.2.1.2.1", # interface name
        ])