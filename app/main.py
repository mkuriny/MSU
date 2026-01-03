from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import devices_router, snmp_router, user_router
from core.container import Container
from services.arp_service import ARPService
import logging
from core.dependencies import get_current_user
import asyncio
from core.middleware.auth_middleware import AuthMiddleware
from routers import auth_router
from sqlalchemy.orm import Session
from routers.device_config_router import router as device_config_router
from routers.device_credentials_router import router as device_credentials_router
from core.dependencies import get_db
from models.device import Device
from models.device_config import DeviceConfig

async def debug_console():
    while True:
        try:
            cmd = input("debug> ")
        except EOFError:
            break

        if cmd == "arp":
            print(ARPService().get_arp_table())
        elif cmd == "exit":
            break


      
class Application:
    """Главный класс приложения (инкапсулирует конфигурацию и зависимости)."""

    def __init__(self):
        self.container = Container()
        self.app = FastAPI(title="My FastAPI App", version="1.0.0")
        self.app.include_router(user_router.router, prefix="/users", tags=["Users"])
        self.app.add_middleware(AuthMiddleware)
        # Подключение статических файлов
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

        # Настройка шаблонов
        self.templates = Jinja2Templates(directory="templates")
	
        # Подключение маршрутов
        self._register_routes()

    def _register_routes(self):
        """Подключение всех маршрутов."""
        self.app.include_router(user_router.router, prefix="/auth")
        self.app.include_router(auth_router.router, prefix="/auth")
        self.app.include_router(devices_router.router, prefix="/devices", tags=["Devices"])
        self.app.include_router(snmp_router.router, prefix="/snmp", tags=["SNMP"])
        self.app.include_router(device_config_router)
        self.app.include_router(device_credentials_router)


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
@app.get("/debug/arp")
async def debug_arp():
    return ARPService().get_arp_table()
print("Routers:", [route.path for route in app.routes])  # ← для отладки

@app.get("/debug/ping/{ip}")
async def debug_ping(ip: str):
    from app.services.snmp_service import SNMPService
    snmp = SNMPService()
    alive = await snmp.ping(ip)
    return {"ip": ip, "alive": alive}
    
@app.get("/devices/{device_id}/configs")
def get_device_configs(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return [
        {
            "id": cfg.id,
            "storage": cfg.storage,
            "comment": cfg.comment,
            "created_at": cfg.created_at
        }
        for cfg in device.configs
    ]
