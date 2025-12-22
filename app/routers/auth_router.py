from fastapi import APIRouter, Request, Form, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from services.user_service import UserService
from core.security import create_access_token
from core.db import SessionLocal
from core.dependencies import get_db
from models.user import User
from services.audit_service import log_action

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    response: Response,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = UserService(db).authenticate(username, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    log_action(
        db,
        user_id=user.id,
        action="login",
        entity_type="auth",
        details=f"User {user.username} logged in"
    )

    return {"status": "ok"}



@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
    
@router.get("/me")
def me(request: Request):
    user: User | None = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401)

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active
    }