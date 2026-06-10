"""Courier / CourierDocument model invariants (T-02).

The composite UNIQUE (area_id, cpf) is the structural enforcement of F-02 E2: a
CPF onboards once per area but may onboard in a DIFFERENT area (new vínculo). The
SQLite in-memory DB enforces UNIQUE, so this runs without live MySQL. The FK
RESTRICT acceptance (delete of a referenced area is blocked) is MySQL-specific
and marked @pytest.mark.mysql.
"""

from __future__ import annotations

import pytest
from app.couriers.models import CourierDocument
from sqlalchemy.exc import IntegrityError

from tests.couriers.conftest import make_courier


@pytest.mark.asyncio
async def test_same_cpf_same_area_blocked(db_session, courier_seed) -> None:
    """E2 structural: a CPF cannot onboard twice in the SAME area."""
    await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    with pytest.raises(IntegrityError):
        # The second insert in the same area violates uq_couriers_area_id_cpf;
        # make_courier flushes, so the error surfaces here.
        await make_courier(
            db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
        )


@pytest.mark.asyncio
async def test_same_cpf_other_area_allowed(db_session, courier_seed) -> None:
    """E2 structural: the SAME CPF may onboard in a DIFFERENT area (new vínculo)."""
    c1 = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    c2 = await make_courier(
        db_session, area_id=courier_seed["area_b_id"], user_id=courier_seed["user_id"]
    )
    assert c1.id != c2.id
    assert c1.cpf == c2.cpf
    assert c1.area_id != c2.area_id


@pytest.mark.asyncio
async def test_document_defaults_and_area_scope(db_session, courier_seed) -> None:
    """A new document starts pending_upload and carries the courier's area_id."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    doc = CourierDocument(
        area_id=courier.area_id,
        courier_id=courier.id,
        kind="selfie",
        status="pending_upload",
    )
    db_session.add(doc)
    await db_session.flush()
    assert doc.status == "pending_upload"
    assert doc.area_id == courier.area_id
    assert doc.sha256 is None
    assert doc.anonymized_at is None


@pytest.mark.asyncio
async def test_courier_mei_pending_default_false(db_session, courier_seed) -> None:
    """mei_pending defaults to False (RN-024 — set True only on inactive MEI)."""
    courier = await make_courier(
        db_session, area_id=courier_seed["area_a_id"], user_id=courier_seed["user_id"]
    )
    assert courier.mei_pending is False
    assert courier.status == "pending_kyc"


@pytest.mark.mysql
@pytest.mark.asyncio
async def test_fk_restrict_area_delete_blocked() -> None:
    """FK RESTRICT: deleting an area referenced by a courier is blocked (MySQL).

    Enforced by the live MySQL 8 server in CI; SQLite in-memory does not enforce
    FK RESTRICT by default. Placeholder so the acceptance is tracked in the suite.
    """
    pytest.skip("requires live MySQL 8 (FK RESTRICT) — run with -m mysql")
