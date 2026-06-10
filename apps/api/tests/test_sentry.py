"""Sentry conditional initialization tests (T-06, D-08).

Proves:
  - No SENTRY_DSN => init_sentry() is a no-op (returns False, SDK not initialized).
  - Fake DSN present => init_sentry() calls sentry_sdk.init once without raising.

The DSN is treated as a secret: never hardcoded, always via env; the init call
is mocked so no real traffic is sent and no credential is required.
"""

from __future__ import annotations

from unittest.mock import patch

from app.core import observability
from app.core.config import Settings


def _settings(**overrides: object) -> Settings:
    return Settings(**overrides)  # type: ignore[arg-type]


def test_init_sentry_noop_without_dsn() -> None:
    """Without a DSN, init is a no-op and never imports/initializes the SDK."""
    with (
        patch.object(observability, "settings", _settings(sentry_dsn=None)),
        patch("sentry_sdk.init") as mock_init,
    ):
        initialized = observability.init_sentry()

    assert initialized is False
    mock_init.assert_not_called()


def test_init_sentry_initializes_with_dsn() -> None:
    """With a fake DSN, init is called exactly once and does not raise."""
    fake_dsn = "https://examplePublicKey@o0.ingest.sentry.io/0"
    with (
        patch.object(
            observability,
            "settings",
            _settings(sentry_dsn=fake_dsn, environment="test", app_version="0.1.0"),
        ),
        patch("sentry_sdk.init") as mock_init,
    ):
        initialized = observability.init_sentry()

    assert initialized is True
    mock_init.assert_called_once()
    kwargs = mock_init.call_args.kwargs
    assert kwargs["dsn"] == fake_dsn
    assert kwargs["send_default_pii"] is False


def test_app_boots_without_sentry_dsn() -> None:
    """The app factory runs without a DSN (Sentry no-op, dev does not break)."""
    with patch.object(observability, "settings", _settings(sentry_dsn=None)):
        from app.main import create_app

        app = create_app()
    assert app.title == "Jaxego API"
