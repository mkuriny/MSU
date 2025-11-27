from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import devices_router, snmp_router, user_router
from app.core.container import Container
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class Application:
    """Главный класс приложения (инкапсулирует конфигурацию и зависимости)."""

    def __init__(self):
        self.container = Container()
        self.app = FastAPI(title="My FastAPI App", version="1.0.0")

        # Подключение статических файлов
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")

        # Настройка шаблонов
        self.templates = Jinja2Templates(directory="app/templates")
	
        # Подключение маршрутов
        self._register_routes()

    def _register_routes(self):
        """Подключение всех маршрутов."""
        self.app.include_router(user_router.router, prefix="/users", tags=["Users"])
        self.app.include_router(devices_router.router, prefix="/devices", tags=["Devices"])
        self.app.include_router(snmp_router.router, prefix="/snmp", tags=["SNMP"])

        # Главная страница
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

    def get_app(self):
        """Возвращает экземпляр FastAPI для запуска Uvicorn."""
        return self.app


# Точка входа
def create_app() -> FastAPI:
    application = Application()
    return application.get_app()


app = create_app()

print("Routers:", [route.path for route in app.routes])  # ← для отладки

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)