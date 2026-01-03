from sqlalchemy import Column, Integer, ForeignKey, Enum, LargeBinary, DateTime, String, func

from sqlalchemy.orm import relationship
from core.db import Base

class DeviceConfig(Base):
    __tablename__ = "device_config"

    id = Column(Integer, primary_key=True)
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False
    )

    storage = Column(Enum("blob", "file"), nullable=False)

    config_blob = Column(LargeBinary, nullable=True)
    file_path = Column(String(255), nullable=True)

    comment = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    device = relationship("Device", back_populates="configs")
