from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    """Best-effort audit trail write. Never raises — a logging failure must
    not break the primary business operation."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
