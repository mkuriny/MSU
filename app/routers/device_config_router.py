from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi import Query
from core.dependencies import get_db, get_current_user
from models.device import Device
from models.device_credential import DeviceCredential
from services.config_fetcher import SSHConfigFetcher
from services.device_config_service import DeviceConfigService
from fastapi.responses import Response
from core.dependencies import get_db
from models.device_config import DeviceConfig
import os
import paramiko
import time
router = APIRouter(prefix="/devices", tags=["Device Configs"])



@router.post("/{device_id}/configs/fetch")
def fetch_device_config(
    device_id: int,
    storage: str = Query(..., enum=["db", "file"]),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    device = db.query(Device).get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")

    cred = db.query(DeviceCredential).filter(
        DeviceCredential.device_id == device_id,
        DeviceCredential.access_type == "ssh",
        DeviceCredential.is_active == True
    ).first()

    if not cred:
        raise HTTPException(400, "No active SSH credentials")

    content = SSHConfigFetcher().fetch(cred, device.Vendor)

    cfg = DeviceConfigService().save(
        db=db,
        device=device,
        content=content,
        storage=storage,
        user_id=user.id
    )

    return {"status": "ok", "config_id": cfg.id}

@router.get("/{config_id}/download")
def download_config(config_id: int, db: Session = Depends(get_db)):
    cfg = db.query(DeviceConfig).filter(DeviceConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not found")

    # Получаем содержимое
    if cfg.storage == "blob":
        content = cfg.config_blob.decode("utf-8")

    elif cfg.storage == "file":
        if not cfg.file_path or not os.path.exists(cfg.file_path):
            raise HTTPException(status_code=404, detail="Config file missing")
        with open(cfg.file_path, "r", encoding="utf-8") as f:
            content = f.read()

    else:
        raise HTTPException(status_code=400, detail="Unsupported storage type")

    filename = f"device_{cfg.device_id}_config_{cfg.id}.cfg"

    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
@router.post("/{device_id}/configs/import")
def import_config(
    device_id: int,
    file: UploadFile = File(...),
    comment: str | None = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    device = db.query(Device).get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
        
    raw = file.file.read()
    content = raw.decode("utf-8")

    cfg = DeviceConfig(
        device_id=device.id,
        storage="blob",
        config_blob=raw,
        created_by=user.id,
        comment=comment or f"Импорт из файла {file.filename}"
    )

    db.add(cfg)
    db.commit()

    return {"status": "ok", "config_id": cfg.id}

@router.post("/{device_id}/configs/{config_id}/apply")
def apply_config(
    device_id: int,
    config_id: int,
    db: Session = Depends(get_db)
):
    # Получаем конфиг
    cfg = db.query(DeviceConfig).get(config_id)
    if not cfg:
        raise HTTPException(404, "Config not found")

    if cfg.storage == "blob":
        if not cfg.config_blob:
            raise HTTPException(404, "Config blob is empty")
        config_text = cfg.config_blob.decode("utf-8")
    elif cfg.storage == "file":
        if not cfg.file_path or not os.path.exists(cfg.file_path):
            raise HTTPException(404, "Config file missing")
        with open(cfg.file_path, "r", encoding="utf-8") as f:
            config_text = f.read()
    else:
        raise HTTPException(400, "Unsupported storage type")

    # Получаем SSH креды
    cred = db.query(DeviceCredential).filter(
        DeviceCredential.device_id == device_id,
        DeviceCredential.access_type == "ssh",
        DeviceCredential.is_active == True
    ).first()

    if not cred:
        raise HTTPException(400, "No SSH credentials")

    # Подключение и отправка конфигурации
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=cred.host,
            port=cred.port,
            username=cred.username,
            password=cred.password,
            timeout=5
        )

        chan = ssh.invoke_shell()

        # Сначала очищаем текущую конфигурацию
        chan.send("load config\n")
        time.sleep(0.2)
        while chan.recv_ready():
            _ = chan.recv(1024)

        # Отправляем новые строки конфигурации
        for line in config_text.splitlines():
            if line.strip():
                chan.send(line + "\n")
                time.sleep(0.1)
                while chan.recv_ready():
                    _ = chan.recv(1024)

        # Завершаем сессию
        chan.send("exit\n")
    finally:
        ssh.close()

    return {"status": "applied"}
