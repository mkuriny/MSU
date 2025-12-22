from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    entity_type = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)

    details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())