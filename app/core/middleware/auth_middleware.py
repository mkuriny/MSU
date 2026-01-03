from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from core.auth import decode_token
from core.db import SessionLocal
from models.user import User

PUBLIC_PATHS = (
    "/auth/login",
    "/auth/list",
    "/config/save",
    "/config/defaults",
    "/static"
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        path = request.url.path

        # 1. Публичные пути
        if path.startswith(PUBLIC_PATHS):
            return await call_next(request)

        # 2. Проверка токена
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse("/auth/login", status_code=302)

        payload = decode_token(token)
        if not payload:
            return RedirectResponse("/auth/login", status_code=302)

        user_id = payload.get("user_id")
        if not user_id:
            return RedirectResponse("/auth/login", status_code=302)

        # 3. Загружаем пользователя из БД
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return RedirectResponse("/auth/login", status_code=302)

            if not user.is_active:
                return RedirectResponse("/auth/login", status_code=302)

            # сохраняем пользователя для дальнейшего использования
            request.state.user = user

        finally:
            db.close()

        return await call_next(request)
