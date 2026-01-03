from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from core.db import Base   # <-- ВАЖНО

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String(255), nullable=False)
    Description = Column(String(255), nullable=True)
    Location = Column(String(255), nullable=True)
    UpTime = Column(String(50), nullable=True)
    UpdateTime = Column(DateTime, default=datetime.utcnow)
    Vendor = Column(String(100), nullable=True)
    Log = Column(Text, nullable=True)
    MAC = Column(Text, nullable=True)

    credentials = relationship(
        "DeviceCredential",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    configs = relationship(
        "DeviceConfig",
        back_populates="device",
        cascade="all, delete-orphan"
    )