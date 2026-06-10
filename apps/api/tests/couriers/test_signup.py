"""F-02 signup (step 1) — E2 anti-enumeration per area (T-05).

Driven directly against the service with the SQLite session (no network). A CPF
already onboarded in the SAME area is blocked with ONE generic message; the SAME
CPF in ANOTHER area is allowed (new vínculo). Invalid CPF → 422.
"""

from __future__ import annotations

import pytest
from app.couriers import service
from app.couriers.schemas import CourierSignupBody

VALID_CPF = "390.533.447-05"  # check-digit valid (masked form accepted)
SECOND_CPF = "111.444.777-35"


def _body(area_id: int, **overrides: object) -> CourierSignupBody:
    data = {
        "area_id": area_id,
        "cpf": VALID_CPF,
        "full_name": "João Entregador",
        "phone_e164": "+5522999990000",
        "email": "joao@example.com",
        "password": "correct-horse-staple-10",
        "vehicle_type": "moto",
        "vehicle_plate": "ABC1D23",
        "consent": True,
    }
    data.update(overrides)
    return CourierSignupBody.model_validate(data)


@pytest.mark.asyncio
async def test_signup_creates_pending_kyc(db_session, courier_seed) -> None:
    """Happy path: a courier is created pending_kyc with the area's KYC level."""
    result = await service.signup(db_session, body=_body(courier_seed["area_a_id"]))
    assert result.status == "pending_kyc"
    assert result.kyc_level == "completa"  # area_a config = completa
    assert result.next_step == "documents"


@pytest.mark.asyncio
async def test_simples_area_next_step_selfie(db_session, courier_seed) -> None:
    """A simples area routes the wizard straight to the selfie step."""
    result = await service.signup(
        db_session,
        body=_body(courier_seed["area_b_id"], email="outro@example.com"),
    )
    assert result.kyc_level == "simples"
    assert result.next_step == "selfie"


@pytest.mark.asyncio
async def test_cpf_same_area_blocks(db_session, courier_seed) -> None:
    """E2 — the SAME CPF cannot onboard twice in the SAME area (generic message)."""
    await service.signup(db_session, body=_body(courier_seed["area_a_id"]))
    await db_session.flush()
    with pytest.raises(service.CourierExistsError) as exc:
        await service.signup(
            db_session,
            body=_body(courier_seed["area_a_id"], email="joao2@example.com"),
        )
    assert "essa cidade" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_cpf_other_area_allowed(db_session, courier_seed) -> None:
    """E2 — the SAME CPF MAY onboard in a DIFFERENT area (new vínculo)."""
    r1 = await service.signup(db_session, body=_body(courier_seed["area_a_id"]))
    await db_session.flush()
    r2 = await service.signup(
        db_session, body=_body(courier_seed["area_b_id"])
    )
    assert r1.courier_id != r2.courier_id


@pytest.mark.asyncio
async def test_invalid_cpf_rejected(db_session, courier_seed) -> None:
    with pytest.raises(service.InvalidCpfError):
        await service.signup(
            db_session,
            body=_body(courier_seed["area_a_id"], cpf="11111111111"),
        )


@pytest.mark.asyncio
async def test_unknown_area_404(db_session, courier_seed) -> None:
    with pytest.raises(service.AreaNotFoundError):
        await service.signup(db_session, body=_body(999_999))
