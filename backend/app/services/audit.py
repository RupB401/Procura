"""
Audit Logger service.
Every state-changing action writes an immutable record to audit_logs.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import AuditLog


async def write_audit_log(
    db: AsyncSession,
    user_id: Optional[UUID],
    action_type: str,
    target_table: str,
    target_id: UUID,
    delta_changes: Dict[str, Any],
) -> None:
    """Write an immutable audit record. Caller is responsible for committing."""
    log_entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        target_table=target_table,
        target_id=target_id,
        delta_changes=delta_changes,
    )
    db.add(log_entry)
