from sqlalchemy.orm import Session
from models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    user_id: int,
    action: str,
    entity_type: str,
    details: str | None = None
):
    """
    Универсальный логгер действий пользователя.
    Никогда не должен ронять основную логику.
    """
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            details=details
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        # Логгер не имеет права ломать систему
        print("⚠️ Ошибка Логгера:", e)
