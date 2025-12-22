from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from core.db import SessionLocal
from models.device import Device
from fastapi import HTTPException
from core.permissions import require_role
from models.user import UserRole
from datetime import datetime
from services.audit_service import log_action
from fastapi import Request

router = APIRouter() 

# Зависимость для сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_devices(
    db: Session = Depends(get_db),
    _: None = Depends(require_role(
        UserRole.admin,
        UserRole.user,
        UserRole.monitor
    ))
):
    devices = db.query(Device).all()
    result = []
    for d in devices:
        result.append({
            "Name": d.Name,
            "Description": d.Description,
            "Location": d.Location,
            "UpTime": d.UpTime,
            "UpdateTime": d.UpdateTime.strftime("%Y-%m-%d %H:%M:%S") if d.UpdateTime else None,
            "OC": d.OC,
            "Log": d.Log,
            "MAC": d.MAC
        })
    return result

@router.delete("/{device_name}")
def delete_device(
    request: Request,
    device_name: str,
    db: Session = Depends(get_db),

    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    device = db.query(Device).filter(Device.Name == device_name).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    log_action(
        db,
        user_id=request.state.user.id,
        action="delete_device",
        entity_type="device",
        details=f"Удалено устройство {device_name}"
    )

    return {"message": f"Device '{device_name}' deleted successfully"}
@router.post("/create")
def create_device(
    request: Request,
    ip: str = Form(...),
    name: str = Form("—"),
    description: str = Form("—"),
    oc: str = Form("—"),
    mac: str = Form("—"),
    db: Session = Depends(get_db),
    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    # проверка — IP обязателен
    if not ip:
        raise HTTPException(status_code=400, detail="IP обязателен")

    # проверка на дубликат
    if db.query(Device).filter(Device.Location == ip).first():
        raise HTTPException(status_code=400, detail="Устройство с таким IP уже существует")
    def mac_boolen(mac):
        if mac == "—":
            return None
        else:
            print("mac_print")
            return mac
    device = Device(
        Name=name or "—",
        Description=description or "—",
        Location=ip,
        UpTime="0",
        UpdateTime=datetime.utcnow(),
        OC=oc or "—",
        Log="_",
        MAC=mac_boolen(mac)
    )
    log_action(
        db,
        user_id=request.state.user.id,
        action="add_device",
        entity_type="device",
        details=f"Добавлено устройство {ip}"
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return {"status": "ok"}