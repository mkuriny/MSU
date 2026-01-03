from sqlalchemy import Integer, Column, String
from core.db import Base



class IPLocation(Base):
    __tablename__ = "ip_location"

    id = Column(Integer, primary_key=True)
    ip_start = Column(String(45), nullable=False)
    ip_end   = Column(String(45), nullable=False)
    label    = Column(String(255), nullable=False)