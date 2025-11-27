import ipaddress
import asyncio
import json
import os
from fastapi import APIRouter, HTTPException
from typing import List
from sqlalchemy.exc import SQLAlchemyError

from app.services.snmp_service import SNMPService
from app.core.db import SessionLocal
from app.models.device import Device

router = APIRouter()

CONFIG_PATH = "app/config/snmp_config.json"
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
    """Читает SNMP настройки из файла или создаёт с дефолтными."""
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(data):
    """Сохраняет конфигурацию SNMP."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ===================== #
#       API             #
# ===================== #

@router.get("/config")
async def get_snmp_config():
    """Получить текущую конфигурацию SNMP."""
    return read_config()


@router.post("/config/save")
async def save_snmp_config(data: dict):
    """Сохранить текущие настройки SNMP."""
    save_config(data)
    return {"status": "saved"}


@router.post("/config/defaults")
async def reset_snmp_config():
    """Восстановить настройки SNMP по умолчанию."""
    save_config(DEFAULT_CONFIG)
    return {"status": "reset to defaults"}


@router.post("/scan")
async def snmp_scan():
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
            ip = device_info["ip"]
            results = device_info["results"]

            name = results.get("1.3.6.1.2.1.1.5.0", {}).get("value", f"Device-{ip}")
            description = results.get("1.3.6.1.2.1.1.1.0", {}).get("value", "No description")

            existing = db.query(Device).filter(Device.Location == ip).first()

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
                    OC="Unknown",
                    Log="_",
                    MAC=None
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