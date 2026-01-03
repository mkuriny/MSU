import subprocess
import re
import time
import platform
import logging
import subprocess
from typing import List, Dict, Optional


def normalize_mac(mac: str) -> str:
    mac = mac.strip().replace("-", ":").upper()
    parts = mac.split(":")
    if len(parts) == 6:
        return ":".join(f"{p:0>2}" for p in parts)
    return mac


class ARPService:
    def __init__(self):
        self.logger = logging.getLogger("ARPService")

    def get_arp_table(self) -> List[Dict[str, str]]:
        try:
            output = subprocess.check_output(["arp", "-a"], encoding="cp866", errors="ignore")
        except Exception as e:
            self.logger.error(f"arp -a failed: {e}")
            return []

        entries: List[Dict[str, str]] = []

        for line in output.splitlines():
            line = line.strip()

            # Windows format
            m = re.search(
                r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mac>(?:[0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2})",
                line
            )

            # Linux format
            if not m:
                m = re.search(
                    r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+ether\s+(?P<mac>(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})",
                    line
                )

            if m:
                ip = m.group("ip")
                mac = normalize_mac(m.group("mac"))

                if mac in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
                    continue

                entries.append({"ip": ip, "mac": mac})

        return entries

    @staticmethod
    def get_mac(ip: str) -> Optional[str]:
        arp = ARPService()
        table = arp.get_arp_table()

        # Прямое совпадение
        for entry in table:
            if entry.get("ip") == ip:
                return entry.get("mac")

        # Если MAC нет — пробуем пропинговать, чтобы ARP-таблица обновилась
        try:
            subprocess.run(
                ["ping", "-n", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

        # Повторная попытка
        table = arp.get_arp_table()
        for entry in table:
            if entry.get("ip") == ip:
                return entry.get("mac")

        return None
    @staticmethod
    def ping(ip: str) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "300", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return result.returncode == 0
        except:
            return False