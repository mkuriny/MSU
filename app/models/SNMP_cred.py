from pydantic import BaseModel, Field
from typing import Optional, Literal


class SNMPCredentialCreate(BaseModel):
    access_type: Literal["snmp"]
    snmp_version: Literal["2c", "3"]
    snmp_community: Optional[str] = None
    snmp_user: Optional[str] = None
    snmp_auth_key: Optional[str] = None
    snmp_priv_key: Optional[str] = None
    comment: Optional[str] = None