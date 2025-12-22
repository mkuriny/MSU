from sqlalchemy.orm import Session
from datetime import datetime

from models.user import User, UserRole
from core.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, password: str, role: UserRole):
        if self.db.query(User).filter_by(username=username).first():
            raise ValueError("User already exists")

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role=role,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, username: str, password: str):
        user = (
            self.db
            .query(User)
            .filter(User.username == username)
            .first()
        )

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user
