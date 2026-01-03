from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from sqlalchemy.sql import func
from core.db import Base


class SNMPConfig(Base):
    __tablename__ = "snmp_config"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_range = Column(String(255), nullable=False)
    timeout	= Column(Integer, nullable=False)
    retries	= Column(Integer, nullable=False)
    snmp_version = Column(Enum('v2c', 'v3'), nullable=False)
    community = Column(String(100), nullable=True)
    snmp_user = Column(String(100), nullable=True)
    
