from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IUserRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Dict[str, Any]:
        pass