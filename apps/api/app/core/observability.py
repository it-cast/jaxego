"""Sentry initialization — strictly conditional on SENTRY_DSN.

When `SENTRY_DSN` is absent the initialization is a no-op: dev runs without a DSN
and the app never breaks. The DSN is a secret and is read only from env.
"""

from __future__ import annotations

from app.core.config import settings


def init_sentry() -> bool:
    """Initialize Sentry only when a DSN is configured.

    Returns:
        True if Sentry was initialized, False if it was a no-op (no DSN).
    """
    dsn = settings.sentry_dsn
    if not dsn:
        return False

    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.environment,
        release=settings.app_version,
        # PII scrubbing stays on by default — never send user data.
        send_default_pii=False,
        traces_sample_rate=0.0,
    )
    return True
