from typing import Any

from sqlalchemy.orm import Session

from ..models import AuditLog


def write_audit(
    db: Session,
    actor: str,
    action: str,
    target_type: str = "",
    target_id: int | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail or {},
    )
    db.add(log)
    db.flush()
    return log
