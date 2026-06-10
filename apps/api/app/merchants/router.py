"""/v1/merchants + /v1/interest endpoints (thin router — F-01).

The router parses the contract, enforces the signup rate limit (TH-07), wires the
environment-selected adapters (Stub in dev/test — never network), and delegates to
the service. Errors propagate as AppError (RFC-7807 envelope). The request body is
NEVER logged (it carries PII — TH-06).

Signup is a PUBLIC endpoint (no auth) by explicit decision (Gate 8): a new store
owner has no account yet. It is protected by rate limiting + Receita validation.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import signup_rate_limit
from app.db.session import get_session
from app.integrations.factory import (
    get_email_adapter,
    get_geocoding_adapter,
    get_receita_adapter,
    get_sms_adapter,
)
from app.merchants import service
from app.merchants.schemas import (
    ConfirmEmailBody,
    ConfirmPhoneBody,
    ConfirmPhoneResponse,
    InterestBody,
    MerchantSignupBody,
    SignupResponse,
)

router = APIRouter(prefix="/merchants", tags=["merchants"])
interest_router = APIRouter(prefix="/interest", tags=["interest"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(signup_rate_limit)],
)
async def signup(
    body: MerchantSignupBody,
    request: Request,
    session: SessionDep,
) -> SignupResponse:
    """Create a store (F-01). Public + rate-limited (explicit auth decision)."""
    result = await service.signup(
        session,
        body=body,
        receita=get_receita_adapter(),
        geocoding=get_geocoding_adapter(),
        sms=get_sms_adapter(),
        email=get_email_adapter(),
        ip=_client_ip(request),
    )
    await session.commit()
    return SignupResponse(
        merchant_id=result.merchant_id,
        status=result.status,
        next_step=result.next_step,
    )


@router.post("/{merchant_id}/confirm-phone", response_model=ConfirmPhoneResponse)
async def confirm_phone(
    merchant_id: int,
    body: ConfirmPhoneBody,
    request: Request,
    session: SessionDep,
) -> ConfirmPhoneResponse:
    """Verify the SMS OTP for a merchant phone (server-side, aware UTC)."""
    confirmed = await service.confirm_phone(
        session, merchant_id=merchant_id, otp=body.otp, ip=_client_ip(request)
    )
    await session.commit()
    return ConfirmPhoneResponse(confirmed=confirmed)


@router.post(
    "/{merchant_id}/confirm-email",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def confirm_email(
    merchant_id: int,
    body: ConfirmEmailBody,
    session: SessionDep,
) -> Response:
    """Confirm a merchant e-mail via the link token."""
    await service.confirm_email(session, merchant_id=merchant_id, token=body.token)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@interest_router.post("", status_code=status.HTTP_202_ACCEPTED)
async def capture_interest(
    body: InterestBody,
    session: SessionDep,
) -> dict[str, str]:
    """Capture interest for an uncovered city ("Ainda não chegamos aí")."""
    await service.capture_interest(session, email=body.email, cidade=body.cidade)
    await session.commit()
    return {"status": "accepted"}
