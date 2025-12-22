from services.user_service import UserService
from core.db import SessionLocal


class Container:
    def get_user_service(self):
        db = SessionLocal()
        return UserService(db)