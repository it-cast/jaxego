"""CourierService — F-02 orchestration (E1–E5), anti-enumeration, KYC item-a-item.

Security invariants (server-side, A04):
- F-02 E2 anti-enumeration: a CPF already onboarded in the SAME area raises ONE
  generic error (`CourierExistsError`) and pays the dummy-hash cost
  (`verify_dummy`) so the response time does not reveal existence. A CPF in
  ANOTHER area is allowed (new vínculo).
- Document access: ownership+area in the WHERE clause (TH-03) → 404 (not 403)
  for anything outside the admin's scope.
- MEI (RN-024): an inactive/incompatible MEI sets `mei_pending=True`; the courier
  still onboards (direct-payment only). CNPJ is never logged.
- KYC item-a-item (D-04/E4): each document approves/rejects INDEPENDENTLY; a
  reject never invalidates an already-approved item. A reject without a reason is
  blocked. When every required document for the level is approved → courier active.
- PII (cpf, cnpj, phone, email) is masked in outputs and NEVER logged (TH-05).
All datetimes are aware UTC (TD-010).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.areas.models import Area
from app.audit.service import write_audit
from app.auth.models import User
from app.core.exceptions import AppError
from app.core.logging import mask_email, mask_phone
from app.core.security import hash_password, verify_dummy
from app.couriers import documents as docs_mod
from app.couriers import kyc
from app.couriers.models import Courier, CourierDocument
from app.couriers.schemas import CourierSignupBody, validate_cpf
from app.couriers.state_machine import assert_courier_transition, assert_document_transition
from app.integrations.base import PresignResult, ReceitaPort, StoragePort

logger = structlog.get_logger("couriers")

# Single generic collision message — NEVER reveals the CPF exists (E2).
DUPLICATE_MESSAGE = "Você já tem cadastro nessa cidade. Recupere o acesso."

CourierStatus = Literal["pending_kyc", "active", "suspended", "banned"]


# ---------------------------------------------------------------------------
# Errors (RFC-7807 envelope via AppError)
# ---------------------------------------------------------------------------
class CourierExistsError(AppError):
    """E2 — CPF already onboarded in the SAME area (generic, anti-enumeration)."""

    status_code = 409
    code = "courier_exists"

    def __init__(self) -> None:
        super().__init__(DUPLICATE_MESSAGE)


class InvalidCpfError(AppError):
    """CPF failed server-side check-digit validation (TH-08)."""

    status_code = 422
    code = "cpf_invalido"

    def __init__(self) -> None:
        super().__init__("CPF inválido. Confira os dígitos e tente de novo.")


class AreaNotFoundError(AppError):
    status_code = 404
    code = "area_not_found"

    def __init__(self) -> None:
        super().__init__("Cidade não encontrada.")


class CourierNotFoundError(AppError):
    status_code = 404
    code = "courier_not_found"

    def __init__(self) -> None:
        super().__init__("Entregador não encontrado.")


class DocumentNotFoundError(AppError):
    """Document outside the caller's scope (ownership/area) → 404, never 403 (TH-03)."""

    status_code = 404
    code = "document_not_found"

    def __init__(self) -> None:
        super().__init__("Documento não encontrado.")


class RejectReasonRequiredError(AppError):
    """A reject without a reason is blocked (D-04 — the courier must know why)."""

    status_code = 422
    code = "reject_reason_required"

    def __init__(self) -> None:
        super().__init__("Selecione o motivo antes de reprovar.")


@dataclass(frozen=True)
class SignupResult:
    """Outcome of a courier signup, shaped for the router/UI."""

    courier_id: int
    status: CourierStatus
    kyc_level: str
    next_step: Literal["selfie", "documents", "done"]


# ---------------------------------------------------------------------------
# Area helpers
# ---------------------------------------------------------------------------
async def _get_area(session: AsyncSession, area_id: int) -> Area:
    area = await session.get(Area, area_id)
    if area is None or area.deleted_at is not None:
        raise AreaNotFoundError()
    return area


def _area_kyc_level(area: Area) -> str:
    """The minimum KYC level the area requires (defaults to simples, RN-002)."""
    cfg = area.config if isinstance(area.config, dict) else {}
    level = cfg.get("kyc_level", "simples")
    return level if level in kyc.VALID_LEVELS else "simples"


def _area_requires_antecedentes(area: Area) -> bool:
    cfg = area.config if isinstance(area.config, dict) else {}
    return bool(cfg.get("requires_antecedentes", False))


# ---------------------------------------------------------------------------
# Signup (step 1) — E2 anti-enumeration per area.
# ---------------------------------------------------------------------------
async def _assert_unique_in_area(
    session: AsyncSession, *, area_id: int, cpf: str, password: str
) -> None:
    """Raise a generic CourierExistsError if the CPF already onboarded HERE.

    Pays the dummy-hash cost on collision so timing does not reveal existence
    (E2). A CPF in another area is fine (new vínculo) — not checked here.
    """
    stmt = select(Courier.id).where(Courier.area_id == area_id, Courier.cpf == cpf)
    if (await session.execute(stmt)).first() is not None:
        verify_dummy(password)  # constant-time path (anti-enumeration)
        logger.info("courier_collision")  # no PII, no field hint
        raise CourierExistsError()


async def signup(
    session: AsyncSession,
    *,
    body: CourierSignupBody,
    ip: str | None = None,
) -> SignupResult:
    """Run the F-02 step-1 signup (creates User + Courier, pending_kyc)."""
    if not validate_cpf(body.cpf):
        raise InvalidCpfError()

    area = await _get_area(session, body.area_id)
    await _assert_unique_in_area(session, area_id=area.id, cpf=body.cpf, password=body.password)

    level = _area_kyc_level(area)

    # Reuse an existing user with this email if present (the same person may
    # onboard across areas); otherwise create one (argon2id).
    existing = (
        await session.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing is not None:
        user = existing
    else:
        user = User(
            email=body.email,
            name=body.full_name,
            phone=body.phone_e164,
            password_hash=hash_password(body.password),
            platform_role="user",
        )
        session.add(user)
        await session.flush()

    courier = Courier(
        area_id=area.id,
        user_id=user.id,
        cpf=body.cpf,
        full_name=body.full_name,
        phone_e164=body.phone_e164,
        email=body.email,
        kyc_level=level,
        status="pending_kyc",
        vehicle_type=body.vehicle_type,
        vehicle_plate=body.vehicle_plate,
        mei_pending=False,
    )
    session.add(courier)
    await session.flush()

    await write_audit(
        session,
        actor_id=user.id,
        action="courier.submitted",
        area_id=area.id,
        after={
            "courier_id": courier.id,
            "status": "pending_kyc",
            "kyc_level": level,
            "email_hint": mask_email(body.email),
            "phone_hint": mask_phone(body.phone_e164),
        },
        ip=ip,
    )

    next_step: Literal["selfie", "documents", "done"] = (
        "documents" if level == "completa" else "selfie"
    )
    return SignupResult(
        courier_id=courier.id,
        status="pending_kyc",
        kyc_level=level,
        next_step=next_step,
    )


# ---------------------------------------------------------------------------
# Courier / document fetch — ownership+area in the WHERE clause (TH-03).
# ---------------------------------------------------------------------------
async def get_courier(session: AsyncSession, courier_id: int) -> Courier:
    courier = await session.get(Courier, courier_id)
    if courier is None or courier.deleted_at is not None:
        raise CourierNotFoundError()
    return courier


async def get_document_for_scope(
    session: AsyncSession,
    *,
    document_id: int,
    courier_id: int,
    area_id: int | None,
) -> CourierDocument:
    """Fetch a document by id, scoped to courier (+area when set) — 404 if outside.

    `area_id is None` is the platform-admin cross-area scope (audited by the
    caller). Otherwise the area is part of the WHERE clause (TH-03 — never an
    `if` after the fetch).
    """
    stmt = select(CourierDocument).where(
        CourierDocument.id == document_id,
        CourierDocument.courier_id == courier_id,
    )
    if area_id is not None:
        stmt = stmt.where(CourierDocument.area_id == area_id)
    doc = (await session.execute(stmt)).scalar_one_or_none()
    if doc is None:
        raise DocumentNotFoundError()
    return doc


# ---------------------------------------------------------------------------
# Document upload (presign + complete) — wraps documents.py.
# ---------------------------------------------------------------------------
async def presign_document(
    session: AsyncSession,
    *,
    courier_id: int,
    kind: str,
    sha256_client: str,
    content_type: str,
    storage: StoragePort,
) -> tuple[CourierDocument, PresignResult]:
    courier = await get_courier(session, courier_id)
    doc, presign = await docs_mod.issue_presign(
        session,
        courier=courier,
        kind=kind,
        sha256_client=sha256_client,
        content_type=content_type,
        storage=storage,
    )
    await write_audit(
        session,
        actor_id=courier.user_id,
        action="courier.document_presigned",
        area_id=courier.area_id,
        after={"courier_id": courier.id, "document_id": doc.id, "kind": kind},
        ip=None,
    )
    return doc, presign


async def complete_document(
    session: AsyncSession,
    *,
    courier_id: int,
    document_id: int,
    storage: StoragePort,
) -> CourierDocument:
    """Run the reprocess pipeline and transition the document to pending."""
    doc = await get_document_for_scope(
        session, document_id=document_id, courier_id=courier_id, area_id=None
    )
    doc = await docs_mod.complete_upload(session, doc=doc, storage=storage)
    await write_audit(
        session,
        actor_id=None,
        action="courier.document_completed",
        area_id=doc.area_id,
        after={"courier_id": courier_id, "document_id": doc.id, "status": doc.status},
    )
    return doc


# ---------------------------------------------------------------------------
# MEI validation (RN-024 / E3) — reuses the Phase 4 Receita adapter.
# ---------------------------------------------------------------------------
async def validate_mei(
    session: AsyncSession,
    *,
    courier_id: int,
    cnpj: str,
    receita: ReceitaPort,
) -> bool:
    """Validate a MEI; set mei_pending if inactive/incompatible (returns the flag).

    CNPJ is NEVER logged (TH-08). A provider-down result (None) is treated as
    not-yet-active → mei_pending (the courier can still work direct; revalidation
    is a future job, mirroring merchants).
    """
    courier = await get_courier(session, courier_id)
    courier.mei_cnpj = cnpj
    result = await receita.consultar_cnpj(cnpj)
    situacao = result.situacao if result is not None else None
    cnaes = result.cnaes if result is not None else []
    compatible = kyc.is_mei_compatible(situacao, cnaes)
    courier.mei_pending = not compatible

    await write_audit(
        session,
        actor_id=courier.user_id,
        action="courier.mei_pending" if courier.mei_pending else "courier.mei_active",
        area_id=courier.area_id,
        after={"courier_id": courier.id, "mei_pending": courier.mei_pending},
    )

    # Phase 10 (RN-010): a now-active MEI registers a Safe2Pay subaccount so the delivery
    # split can pay the courier's corrida. Degrades gracefully if the API is unavailable.
    if not courier.mei_pending:
        from app.couriers.subaccount import register_subaccount_on_mei_active
        from app.payments.factory import get_payment_adapter

        await register_subaccount_on_mei_active(
            session, courier=courier, payment=get_payment_adapter()
        )

    return courier.mei_pending


# ---------------------------------------------------------------------------
# KYC item-a-item review (D-04 / E4) — admin of the area.
# ---------------------------------------------------------------------------
async def _approved_kinds(session: AsyncSession, courier_id: int) -> set[str]:
    """The set of document kinds currently approved for a courier (eager, no N+1)."""
    stmt = select(CourierDocument.kind).where(
        CourierDocument.courier_id == courier_id,
        CourierDocument.status == "approved",
    )
    return {row[0] for row in (await session.execute(stmt)).all()}


async def review_document(
    session: AsyncSession,
    *,
    courier_id: int,
    document_id: int,
    area_id: int | None,
    actor_id: int,
    action: Literal["approve", "reject"],
    reason: str | None = None,
    detail: str | None = None,
    cross_area_bypass: bool = False,
) -> tuple[CourierDocument, CourierStatus]:
    """Approve/reject a document item-a-item; activate the courier when complete.

    Each item is independent (E4): rejecting one never touches another's status.
    A reject requires a reason (D-04). When every required document for the
    courier's level is approved, the courier transitions to `active` (RN-002).
    """
    doc = await get_document_for_scope(
        session, document_id=document_id, courier_id=courier_id, area_id=area_id
    )
    courier = await get_courier(session, courier_id)

    if action == "reject":
        if not reason:
            raise RejectReasonRequiredError()
        assert_document_transition(doc.status, "rejected")
        doc.status = "rejected"
        doc.reject_reason = reason
        doc.reject_detail = detail
        await write_audit(
            session,
            actor_id=actor_id,
            action="kyc.item_rejected",
            area_id=courier.area_id,
            after={"document_id": doc.id, "kind": doc.kind, "reason": reason},
            cross_area_bypass=cross_area_bypass,
        )
    else:
        assert_document_transition(doc.status, "approved")
        doc.status = "approved"
        doc.reject_reason = None
        doc.reject_detail = None
        await write_audit(
            session,
            actor_id=actor_id,
            action="kyc.item_approved",
            area_id=courier.area_id,
            after={"document_id": doc.id, "kind": doc.kind},
            cross_area_bypass=cross_area_bypass,
        )

    # Activate the courier iff every required document for the level is approved.
    await session.flush()
    approved = await _approved_kinds(session, courier_id)
    area = await _get_area(session, courier.area_id)
    if (
        courier.status == "pending_kyc"
        and action == "approve"
        and kyc.all_required_approved(
            courier.kyc_level,
            approved,
            antecedentes_required=_area_requires_antecedentes(area),
        )
    ):
        assert_courier_transition(courier.status, "active")
        courier.status = "active"
        await write_audit(
            session,
            actor_id=actor_id,
            action="courier.activated",
            area_id=courier.area_id,
            after={"courier_id": courier.id, "status": "active"},
            cross_area_bypass=cross_area_bypass,
        )

    return doc, cast(CourierStatus, courier.status)


async def list_area_couriers(
    session: AsyncSession,
    *,
    area_id: int | None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Courier], int]:
    """List couriers in the admin's area (F2.0 — KYC queue + courier list).

    Area in the WHERE clause (TH-09). `area_id is None` is the platform-admin
    cross-area bypass (audited at the caller). Optional `status` filter powers the
    KYC queue (status='pending_kyc'). Single query + COUNT, no N+1.
    """
    base = select(Courier).where(Courier.deleted_at.is_(None))
    count_stmt = select(func.count(Courier.id)).where(Courier.deleted_at.is_(None))
    if area_id is not None:
        base = base.where(Courier.area_id == area_id)
        count_stmt = count_stmt.where(Courier.area_id == area_id)
    if status is not None:
        base = base.where(Courier.status == status)
        count_stmt = count_stmt.where(Courier.status == status)
    base = base.order_by(Courier.created_at.desc()).limit(limit).offset(offset)
    rows = list((await session.execute(base)).scalars().all())
    total = int((await session.execute(count_stmt)).scalar_one())
    return rows, total
