from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.logger import logger
import os
# Настройки подключения
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "host.docker.internal")
DB_PORT = "3306"
DB_NAME = os.getenv("DB_NAME", "1")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Проверка подключения
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # <- используем text()
    logger.info("Подключение к базе данных успешно!")
except Exception as e:
    logger.error(f"Ошибка подключения к базе данных: {e}")