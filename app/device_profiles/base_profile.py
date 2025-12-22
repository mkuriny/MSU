# services/device_profiles/base_profile.py

from abc import ABC, abstractmethod


class BaseProfile(ABC):
    """
    Базовый класс профиля устройства.
    Каждый профиль должен реализовать методы:
    - detect() — проверка, подходит ли профиль для устройства
    - fetch_info() — получение информации с устройства
    """

    def __init__(self, ip: str, mac: str):
        self.ip = ip
        self.mac = mac

    @abstractmethod
    async def detect(self) -> bool:
        """
        Проверяет, подходит ли данный профиль для устройства.
        Здесь логика проверки производителя, маски MAC, ответа на SNMP/SSH или что-то другое.
        """
        pass

    @abstractmethod
    async def fetch_info(self) -> dict:
        """
        Получение информации об устройстве.
        Возвращает словарь:
        {
            "ip": ...,
            "mac": ...,
            "type": ...,
            "model": ...,
            "vendor": ...,
            "extra": {...}
        }
        """
        pass
    async def scan(self, snmp):
        return await self.fetch_info(snmp)
    # Общая утилита, если нужна
    async def ping(self) -> bool:
        """
        Базовый пинг устройства — может использоваться при детекции.
        """
        import subprocess

        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "500", self.ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="cp866"
            )
            return result.returncode == 0
        except Exception:
            return False