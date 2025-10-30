from fastapi import FastAPI
from app.core.container import Container
from app.routers import user_router


class Application:
    """Главный класс приложения (инкапсулирует конфигурацию и зависимости)."""

    def __init__(self):
        self.container = Container()
        self.app = FastAPI(title="My FastAPI App", version="1.0.0")
        self._register_routes()

    def _register_routes(self):
        """Подключение маршрутов (SRP — каждая часть отвечает за одно действие)."""
        self.app.include_router(user_router.router, prefix="/users", tags=["Users"])

    def get_app(self):
        """Возвращает экземпляр FastAPI для запуска Uvicorn."""
        return self.app


# Точка входа
def create_app() -> FastAPI:
    """Фабрика приложения (DIP — зависимости внедряются через контейнер)."""
    application = Application()
    return application.get_app()


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)