from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from core.db import Base
import enum


class AccessType(str, enum.Enum):
    ssh = "ssh"
    snmp = "snmp"
    api = "api"


class SNMPVersion(str, enum.Enum):
    v2c = "2c"
    v3 = "3"


class DeviceCredential(Base):
    __tablename__ = "device_credentials"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))

    access_type = Column(Enum(AccessType), nullable=False)
    is_active = Column(Boolean, default=True)
    comment = Column(String(255))

    # SSH / API
    host = Column(String(255))
    port = Column(Integer)
    username = Column(String(128))
    password = Column(String(255))
    private_key = Column(Text)

    # SNMP
    snmp_version = Column(Enum(SNMPVersion))
    snmp_community = Column(String(128))
    snmp_user = Column(String(128))
    snmp_auth_key = Column(String(255))
    snmp_auth_protocol = Column(Enum("MD5", "SHA"))
    snmp_priv_key = Column(String(255))
    snmp_priv_protocol = Column(Enum("DES", "AES"))

    device = relationship("Device", back_populates="credentials")
