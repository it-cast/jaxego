"""AiUsageLog model — GLOBAL (ADR-001), Phase 14 (T-02 / REQ-053 / D-03).

This table is GLOBAL (ADR-001): it has NO `area_id` and does NOT inherit
AreaScopedMixin (like `users` and `audit_log`). It records ONE row per LLM call for
cost/latency observability.

PII discipline (TH-03): it carries provider/model/task + token/cost/latency
metadata ONLY. It NEVER stores the prompt, the completion, or any personal data.
`request_id` correlates with the structlog request id; `error_kind` is the failure
class (an exception type name), never a message that could leak data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import BIG_ID, UTC_DATETIME


class AiUsageLog(Base):
    """Append-style usage record for one LLM call (no PII, no prompt)."""

    __tablename__ = "ai_usage_log"

    id: Mapped[int] = mapped_column(BIG_ID, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    task: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Correlation id (structlog request id) — opaque, never PII.
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Failure class (exception type name) — NEVER a message (TH-03).
    error_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # No TimestampMixin: one created_at, set by the router (aware UTC — TD-010).
    created_at: Mapped[datetime] = mapped_column(UTC_DATETIME, nullable=False, index=True)
