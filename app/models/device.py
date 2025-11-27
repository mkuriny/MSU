from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String(255), nullable=False)
    Description = Column(String(255), nullable=True)
    Location = Column(String(255), nullable=True)
    UpTime = Column(String(50), nullable=True)
    UpdateTime = Column(DateTime, default=datetime.utcnow)
    OC = Column(String(100), nullable=True)
    Log = Column(Text, nullable=True)
    MAC = Column(Text, nullable=True)