
from typing import Dict, Any

class BaseProbe:
    """Базовый интерфейс пробника любого устройства."""

    async def probe(self, ip: str, mac: str) -> Dict[str, Any]:
        """
        Выполнить опрос устройства.
        Должен быть переопределён.
        """
        raise NotImplementedError