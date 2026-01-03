from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db
from models.device_credential import DeviceCredential
from models.SNMP_cred import SNMPCredentialCreate
from models.ssh_cred import SSHCredentialCreate
from typing import Union

router = APIRouter(prefix="/devices", tags=["Device Credentials"])

CredentialCreate = Union[
    SSHCredentialCreate,
    SNMPCredentialCreate
]

@router.get("/{device_id}/credentials")
def get_credentials(device_id: int, db: Session = Depends(get_db)):
    return db.query(DeviceCredential)\
        .filter(DeviceCredential.device_id == device_id)\
        .all()


@router.post("/{device_id}/credentials")
def create_credential(device_id: int, data: dict, db: Session = Depends(get_db)):
    cred = DeviceCredential(device_id=device_id, **data)
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred
