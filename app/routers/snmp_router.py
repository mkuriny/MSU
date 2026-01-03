import ipaddress
import asyncio
import json
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from services.audit_service import log_action
from services.snmp_service import SNMPService
from core.db import SessionLocal
from models.device import Device
from core.permissions import require_role
from models.user import UserRole
from core.db import SessionLocal
from models.snmp_config import SNMPConfig
router = APIRouter()

#CONFIG_PATH = "app/config/snmp_config.json"
DEFAULT_CONFIG = {
    "ip_range": "192.168.1.1-192.168.1.10",
    "timeout": 2,
    "retries": 0,
    "community": "public",
    "v3_user": None
}

snmp_service = SNMPService()


# ===================== #
#   ВСПОМОГАТЕЛЬНЫЕ    #
# ===================== #

def expand_ip_range(ip_range: str) -> List[str]:
    """Преобразует диапазон IP вида '192.168.1.1-192.168.1.20' в список."""
    try:
        start_ip, end_ip = ip_range.split('-')
        start_int = int(ipaddress.IPv4Address(start_ip))
        end_int = int(ipaddress.IPv4Address(end_ip))
        return [str(ipaddress.IPv4Address(i)) for i in range(start_int, end_int + 1)]
    except Exception as e:
        print("Ошибка парсинга диапазона:", e)
        raise HTTPException(status_code=400, detail="Некорректный диапазон IP")

def read_config():
    db = SessionLocal()
    try:
        cfg = db.query(SNMPConfig).filter(SNMPConfig.id == 1).first()

        if not cfg:
            # инициализация БД из DEFAULT_CONFIG
            cfg = SNMPConfig(
                id=1,
                ip_range=DEFAULT_CONFIG["ip_range"],
                timeout=DEFAULT_CONFIG["timeout"],
                retries=DEFAULT_CONFIG["retries"],
                snmp_version="v2c",
                community=DEFAULT_CONFIG["community"],
                snmp_user=DEFAULT_CONFIG["v3_user"],
            )
            db.add(cfg)
            db.commit()
            db.refresh(cfg)

        # ⬅️ ВОЗВРАЩАЕМ ТОЛЬКО DICT
        return {
            "ip_range": cfg.ip_range,
            "timeout": cfg.timeout,
            "retries": cfg.retries,
            "community": cfg.community,
            "v3_user": cfg.snmp_user,
        }

    finally:
        db.close()
            



def save_snmp_config_db(data: dict):
    db = SessionLocal()
    try:
        cfg = db.query(SNMPConfig).filter(SNMPConfig.id == 1).first()
        if not cfg:
            cfg = SNMPConfig(id=1)
            db.add(cfg)

        cfg.ip_range = data.get("ip_range", DEFAULT_CONFIG["ip_range"])
        cfg.timeout = data.get("timeout", DEFAULT_CONFIG["timeout"])
        cfg.retries = data.get("retries", DEFAULT_CONFIG["retries"])
        cfg.snmp_version = data.get("snmp_version", "v2c")
        cfg.community = data.get("community", DEFAULT_CONFIG["community"])
        cfg.snmp_user = data.get("v3_user", DEFAULT_CONFIG["v3_user"])

        db.commit()
        db.refresh(cfg)
        return cfg
    finally:
        db.close()

def reset_snmp_config_db():
    return save_snmp_config_db(DEFAULT_CONFIG)
# ===================== #
#       API             #
# ===================== #

@router.get("/config")
async def get_snmp_config(
    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    """Получить текущую конфигурацию SNMP."""
    return read_config()


@router.post("/config/save")
async def save_snmp_config(
    data: dict,
    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    """Сохранить текущие настройки SNMP."""
    save_snmp_config_db(data)
    return {"status": "saved"}



@router.post("/config/defaults")
async def reset_snmp_config(
    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    """Восстановить настройки SNMP по умолчанию."""
    reset_snmp_config_db()
    return {"status": "reset to defaults"}


@router.post("/scan")
async def snmp_scan(
    request: Request,

    _: None = Depends(require_role(UserRole.admin, UserRole.user))
):
    """
    Сканирование сети по текущим настройкам SNMP
    и сохранение найденных устройств в БД.
    """
    cfg = read_config()
    try:
        targets = expand_ip_range(cfg["ip_range"])
        print(f"📡 Запуск SNMP сканирования для {len(targets)} IP...")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # выполняем сканирование
        result = await snmp_service.scan(
            targets=targets,
            community=cfg.get("community"),
            v3_user=cfg.get("v3_user"),
            timeout=cfg.get("timeout"),
            retries=cfg.get("retries"),
        )

        db = SessionLocal()
        added, updated = 0, 0

        for device_info in result["details"]:
            if device_info.get("alive") is False:
                print(f"Пропуск {device_info['ip']}: недоступен")
                continue
            ip = device_info["ip"]
            results = device_info["results"]

            name = results.get("1.3.6.1.2.1.1.5.0", {}).get("value", f"Device-{ip}")
            description = results.get("1.3.6.1.2.1.1.1.0", {}).get("value", "No description")

            existing = db.query(Device).filter(Device.Location == ip).first()
            mac = device_info.get("mac")
            if existing:
                existing.Name = name
                existing.Description = description
                updated += 1
            else:
                new_device = Device(
                    Name=name,
                    Description=description,
                    Location=ip,
                    UpTime="N/A",
                    UpdateTime=None,
                    Vendor="Unknown",
                    Log="_",
                    MAC=mac
                )
                db.add(new_device)
                added += 1

        db.commit()


        db.close()

        print(f"✅ Сканирование завершено: добавлено {added}, обновлено {updated}")

        return {
            "status": "ok",
            "added": added,
            "updated": updated,
            "result": result
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {e}")
    except Exception as e:
        print("❌ Ошибка SNMP сканирования:", e)
        raise HTTPException(status_code=500, detail=f"Ошибка SNMP сканирования: {e}")
    