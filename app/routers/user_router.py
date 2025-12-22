from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.db import SessionLocal

from services.user_service import UserService
from models.user import UserRole, User
from core.dependencies import get_db
from core.auth import create_access_token
from core.permissions import require_role




router = APIRouter(tags=["Users"])

templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()






    
@router.get("/list")
def list_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_role(UserRole.admin))
):
    users = db.query(User).all()

    grouped = {
        "admin": [],
        "user": [],
        "monitor": []
    }

    for u in users:
        grouped[u.role].append({
            "id": u.id,
            "username": u.username,
            "active": u.is_active
        })

    return grouped
@router.post("/create")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_role(UserRole.admin))
):
    
    return UserService(db).create_user(username, password, role)
    
@router.post("/toggle/{user_id}")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_role(UserRole.admin))
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    db.commit()
    return {"ok": True}
    
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_role(UserRole.admin))
):
    db.delete(db.get(User, user_id))
    db.commit()
    return {"ok": True}

    
