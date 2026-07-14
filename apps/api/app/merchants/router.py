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

from app.auth.dependencies import AreaScopeDep, CurrentUser, require_role
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
    MerchantAdminListItem,
    MerchantAdminListOut,
    MerchantProfileRead,
    MerchantProfileUpdate,
    MerchantSignupBody,
    SignupResponse,
    mask_document_display,
)

router = APIRouter(prefix="/merchants", tags=["merchants"])
interest_router = APIRouter(prefix="/interest", tags=["interest"])
admin_router = APIRouter(prefix="/admin/merchants", tags=["merchants-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@admin_router.get("", response_model=MerchantAdminListOut)
async def list_area_merchants(
    session: SessionDep,
    admin: Annotated[CurrentUser, Depends(require_role("admin_area"))],
    scope: AreaScopeDep,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> MerchantAdminListOut:
    """List stores in the area (F2.4). Area in the WHERE clause (TH-09); platform
    admin (scope=None) sees all areas. Document masked (TH-06)."""
    rows, total = await service.list_area_merchants(
        session,
        area_id=scope,
        status=status,
        limit=min(limit, 100),
        offset=max(offset, 0),
    )
    items = [
        MerchantAdminListItem(
            id=m.id,
            trade_name=m.trade_name,
            account_type=m.account_type,
            document_masked=mask_document_display(m.document),
            category=m.category,
            status=m.status,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in rows
    ]
    return MerchantAdminListOut(
        items=items, total=total, limit=min(limit, 100), offset=max(offset, 0)
    )


@router.get("/profile", response_model=MerchantProfileRead)
async def get_profile(
    session: SessionDep,
    user: CurrentUser,
) -> MerchantProfileRead:
    from app.merchants.models import Merchant

    if user.type != "merchant":
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Loja nao encontrada.")
    merchant = await session.get(Merchant, user.id)
    if merchant is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Loja nao encontrada.")
    return MerchantProfileRead(
        id=merchant.id,
        trade_name=merchant.trade_name,
        address=merchant.address,
        address_number=merchant.address_number,
        address_neighborhood=merchant.address_neighborhood,
        category=merchant.category,
        email=merchant.email,
    )


@router.patch("/profile", response_model=MerchantProfileRead)
async def update_profile(
    body: MerchantProfileUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> MerchantProfileRead:
    from app.merchants.models import Merchant

    if user.type != "merchant":
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Loja nao encontrada.")
    merchant = await session.get(Merchant, user.id)
    if merchant is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Loja nao encontrada.")
    if body.trade_name is not None:
        merchant.trade_name = body.trade_name
    if body.address is not None:
        merchant.address = body.address
    if body.address_number is not None:
        merchant.address_number = body.address_number
    if body.address_neighborhood is not None:
        merchant.address_neighborhood = body.address_neighborhood
    await session.flush()
    await session.commit()
    return MerchantProfileRead(
        id=merchant.id,
        trade_name=merchant.trade_name,
        address=merchant.address,
        address_number=merchant.address_number,
        address_neighborhood=merchant.address_neighborhood,
        category=merchant.category,
        email=merchant.email,
    )


@router.get("/credit-balance")
async def get_credit_balance(session: SessionDep, user: CurrentUser) -> dict:
    """Saldo/crédito disponível da loja (pode ser negativo — não bloqueia nada)."""
    from app.core.exceptions import NotFoundError
    from app.merchants import credit

    if user.type != "merchant" or user.area_id is None:
        raise NotFoundError("Loja nao encontrada.")
    balance = await credit.available_credit_cents(
        session, area_id=user.area_id, merchant_id=user.id
    )
    await session.commit()  # libera o FOR UPDATE (leitura, nada a persistir)
    return {"balance_cents": balance}


@router.get("/credit-ledger")
async def get_credit_ledger(
    session: SessionDep,
    user: CurrentUser,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Extrato de créditos/débitos da loja — mais recentes primeiro."""
    from app.core.exceptions import NotFoundError
    from app.merchants import credit

    if user.type != "merchant" or user.area_id is None:
        raise NotFoundError("Loja nao encontrada.")
    entries = await credit.list_ledger(
        session,
        area_id=user.area_id,
        merchant_id=user.id,
        limit=min(limit, 100),
        offset=max(offset, 0),
    )
    return {
        "items": [
            {
                "id": e.id,
                "delivery_id": e.delivery_id,
                "kind": e.kind,
                "amount_cents": e.amount_cents,
                "reason": e.reason,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


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
