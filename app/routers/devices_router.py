from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.device import Device
from fastapi import HTTPException

router = APIRouter() 

# Зависимость для сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_devices(db: Session = Depends(get_db)):
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
def delete_device(device_name: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.Name == device_name).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"message": f"Device '{device_name}' deleted successfully"}