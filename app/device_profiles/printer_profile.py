
from .base_profile import BaseProfile

class PrinterProfile(BaseProfile):

    async def scan(self, snmp):
        """SNMP-опрос принтера (Printer-MIB)."""
        return await snmp.get_many(self.ip, [
            "1.3.6.1.2.1.1.1.0",          # sysDescr (модель)
            "1.3.6.1.2.1.1.5.0",          # sysName
            "1.3.6.1.2.1.43.5.1.1.16.1",  # prtGeneralSerialNumber
            "1.3.6.1.2.1.43.10.2.1.4.1.1",# prtMarkerSuppliesLevel (тонер)
            "1.3.6.1.2.1.43.11.1.1.6.1.1",# prtAlertDescription (ошибки, замятие бумаги)
            "1.3.6.1.2.1.43.8.2.1.10.1.1" # prtMarkerLifeCount (кол-во отпечатков)
        ])