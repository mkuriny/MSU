from app.core.interfaces import IUserRepository


class UserService:
    """Сервисный слой (SRP — отвечает только за бизнес-логику)."""

    def __init__(self, user_repository: IUserRepository):
        self._repo = user_repository

    def list_users(self):
        return self._repo.get_all()

    def get_user(self, user_id: int):
        return self._repo.get_by_id(user_id)