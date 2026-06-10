"""Audit write service (RN-012 / RN-001).

`write_audit` is the only sanctioned way to record an audited action. It writes
to the `audit_log` TABLE — never to the application log (audit_log is data, not
a structlog line). All inserts are ORM-parametrised (no f-string SQL, A03).
Datetime is aware UTC (TD-010).

A platform-admin cross-area access is recorded with `cross_area_bypass=True` so
the bypass is never silent (RN-001).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog


async def write_audit(
    session: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    area_id: int | None = None,
    before: dict | None = None,
    after: dict | None = None,
    ip: str | None = None,
    cross_area_bypass: bool = False,
) -> AuditLog:
    """Append one audit row. Caller commits within the request transaction."""
    entry = AuditLog(
        actor_user_id=actor_id,
        action=action,
        area_id=area_id,
        before=before,
        after=after,
        ip=ip,
        cross_area_bypass=cross_area_bypass,
        created_at=datetime.now(UTC),  # AWARE — TD-010
    )
    session.add(entry)
    await session.flush()
    return entry
