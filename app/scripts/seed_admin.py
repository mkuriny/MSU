from core.db import SessionLocal
from models.user import User
from core.security import get_password_hash

def main():
    db = SessionLocal()

    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("Администратор уже существует")
        return

    user = User(
        username="admin",
        password_hash=get_password_hash("123"),
        role="admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.close()

    print("Администратор создан: admin / 123")

if __name__ == "__main__":
    main()