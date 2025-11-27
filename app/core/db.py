from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.logger import logger

# Настройки подключения
DB_USER = "root"
DB_PASSWORD = "root"  # если есть
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_NAME = "program"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Проверка подключения
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # <- используем text()
    logger.info("Подключение к базе данных успешно!")
except Exception as e:
    logger.error(f"Ошибка подключения к базе данных: {e}")