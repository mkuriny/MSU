from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


class Container:
    """Контейнер для зависимостей."""

    def __init__(self):
        # Здесь можно добавить подключение к БД и другие зависимости
        self.user_repository = UserRepository()
        self.user_service = UserService(self.user_repository)