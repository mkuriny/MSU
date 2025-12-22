from core.interfaces import IUserRepository


class UserRepository(IUserRepository):
    """Работа с данными (например, с базой или файлами)."""

    def __init__(self):
        self._users = [
            {"id": 1, "name": "Иван"},
            {"id": 2, "name": "Мария"},
        ]

    def get_all(self):
        return self._users

    def get_by_id(self, user_id: int):
        return next((u for u in self._users if u["id"] == user_id), None)