"""Area config typed validation + audit on sensitive change (REQ-002).

The area config (piso/geofence/kyc_level/timeouts/política de retorno) is no
longer raw JSON: it is validated by the typed `AreaConfig` (Pydantic v2, ranges)
and, when a SENSITIVE key changes, `update_area` records a `before/after` row in
`audit_log` (RN-012 / F-08 E2 — Pitfall 4). A non-sensitive change (name only)
does NOT produce a config audit.

Runs on SQLite in-memory (no live MySQL).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.areas.config_schema import (
    SENSITIVE_KEYS,
    AreaConfig,
    diff_sensitive,
)
from app.areas.models import Area
from app.audit.models import AuditLog
from pydantic import ValidationError
from sqlalchemy import select


# --- AreaConfig typed ranges -------------------------------------------------
def test_area_config_defaults_valid() -> None:
    """A config with only the required pisos fills defaults for the rest."""
    cfg = AreaConfig(kyc_level="simples", piso_entrega=Decimal("8.00"), piso_km=Decimal("2.00"))
    assert cfg.geofence_m == 80  # RN-005 default
    assert cfg.timeout_oferta_s == 20  # ADR-104 default
    assert cfg.timeout_favoritos_s == 60  # ADR-007 default
    assert cfg.politica_retorno_pct == 0


def test_area_config_geofence_out_of_range_rejected() -> None:
    """geofence_m outside 30..300 → ValidationError (mapped to 422 by the API)."""
    with pytest.raises(ValidationError):
        AreaConfig(
            kyc_level="simples",
            piso_entrega=Decimal("8.00"),
            piso_km=Decimal("2.00"),
            geofence_m=10,
        )


def test_area_config_timeout_oferta_out_of_range_rejected() -> None:
    """timeout_oferta_s outside 10..60 → ValidationError."""
    with pytest.raises(ValidationError):
        AreaConfig(
            kyc_level="simples",
            piso_entrega=Decimal("8.00"),
            piso_km=Decimal("2.00"),
            timeout_oferta_s=120,
        )


def test_area_config_forbids_extra_keys() -> None:
    """extra='forbid' rejects unknown keys (no silent typos in config)."""
    with pytest.raises(ValidationError):
        AreaConfig(
            kyc_level="simples",
            piso_entrega=Decimal("8.00"),
            piso_km=Decimal("2.00"),
            unknown_key=1,
        )


def test_sensitive_keys_cover_the_seven() -> None:
    """The 7 auditable keys are the documented sensitive set."""
    assert SENSITIVE_KEYS == frozenset(
        {
            "kyc_level",
            "piso_entrega",
            "piso_km",
            "geofence_m",
            "timeout_oferta_s",
            "timeout_favoritos_s",
            "politica_retorno_pct",
        }
    )


def test_diff_sensitive_detects_changed_keys() -> None:
    """diff_sensitive returns only the sensitive keys that changed."""
    before = {"piso_km": "2.00", "geofence_m": 80, "kyc_level": "simples"}
    after = {"piso_km": "3.00", "geofence_m": 80, "kyc_level": "simples"}
    diff = diff_sensitive(before, after)
    assert diff is not None
    diff_before, diff_after = diff
    assert diff_before == {"piso_km": "2.00"}
    assert diff_after == {"piso_km": "3.00"}


def test_diff_sensitive_none_when_unchanged() -> None:
    """No sensitive change → None (no audit row)."""
    before = {"piso_km": "2.00", "geofence_m": 80}
    after = {"piso_km": "2.00", "geofence_m": 80}
    assert diff_sensitive(before, after) is None


# --- update_area audit on sensitive change -----------------------------------
@pytest.mark.asyncio
async def test_sensitive_config_change_writes_audit(db_session, seed) -> None:
    """Changing a sensitive key writes one before/after audit row (RN-012)."""
    from app.areas import service
    from app.areas.schemas import AreaUpdate

    area_id = seed.area_a.id
    area = await db_session.get(Area, area_id)
    area.config = {
        "kyc_level": "simples",
        "piso_entrega": "8.00",
        "piso_km": "2.00",
        "geofence_m": 80,
        "timeout_oferta_s": 20,
        "timeout_favoritos_s": 60,
        "politica_retorno_pct": 0,
    }
    await db_session.flush()

    new_config = {
        "kyc_level": "simples",
        "piso_entrega": "8.00",
        "piso_km": "3.50",  # SENSITIVE change
        "geofence_m": 80,
        "timeout_oferta_s": 20,
        "timeout_favoritos_s": 60,
        "politica_retorno_pct": 0,
    }
    _, diff = await service.update_area(db_session, area_id, AreaUpdate(config=new_config))
    assert diff is not None  # service returns the sensitive diff for the router

    diff_before, diff_after = diff
    from app.audit.service import write_audit

    await write_audit(
        db_session,
        actor_id=seed.admin_a.id,
        action="area.config.update",
        area_id=area_id,
        before=diff_before,
        after=diff_after,
    )
    rows = (
        (await db_session.execute(select(AuditLog).where(AuditLog.action == "area.config.update")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].before == {"piso_km": "2.00"}
    assert rows[0].after == {"piso_km": "3.50"}


@pytest.mark.asyncio
async def test_non_sensitive_change_no_config_diff(db_session, seed) -> None:
    """Changing only the name produces no sensitive config diff."""
    from app.areas import service
    from app.areas.schemas import AreaUpdate

    area_id = seed.area_a.id
    _, diff = await service.update_area(db_session, area_id, AreaUpdate(name="Pádua Centro"))
    assert diff is None


@pytest.mark.asyncio
async def test_config_range_violation_raises(db_session, seed) -> None:
    """A config with a key out of range is rejected before persisting."""
    from app.areas import service
    from app.areas.schemas import AreaUpdate
    from app.core.exceptions import AppError

    bad = {
        "kyc_level": "simples",
        "piso_entrega": "8.00",
        "piso_km": "2.00",
        "geofence_m": 5,  # below 30
    }
    with pytest.raises((AppError, ValueError)):
        await service.update_area(db_session, seed.area_a.id, AreaUpdate(config=bad))
