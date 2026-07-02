"""/v1/team-admin — team responsible dashboard, courier KYC, deliveries.

Scoped by team_id from the authenticated user's team binding.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from app.areas.models import Zona
from app.auth.dependencies import CurrentUser
from app.auth.models import User
from app.couriers.models import Courier, CourierDocument
from app.db.session import get_session
from app.deliveries.models import Delivery
from app.teams.models import Team, TeamZona

router = APIRouter(prefix="/team-admin", tags=["team-admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _resolve_team(user: User, session: AsyncSession) -> Team:
    team = (
        await session.execute(
            select(Team).where(Team.responsavel_user_id == user.id, Team.deleted_at.is_(None)).limit(1)
        )
    ).scalar_one_or_none()
    if team is None:
        raise HTTPException(status_code=403, detail="Acesso restrito a responsáveis de equipe.")
    return team


@router.get("/dashboard")
async def dashboard(user: CurrentUser, session: SessionDep) -> dict:
    team = await _resolve_team(user, session)
    couriers = list(
        (await session.execute(
            select(Courier).where(Courier.team_id == team.id, Courier.deleted_at.is_(None))
        )).scalars().all()
    )
    total_couriers = len(couriers)
    online = sum(1 for c in couriers if c.is_online)
    pending_kyc = sum(1 for c in couriers if c.status == "pending_kyc")

    today = sa_func.curdate()
    deliveries_today = (await session.execute(
        select(sa_func.count()).select_from(Delivery).where(
            Delivery.team_ids.is_not(None),
            sa_func.date(Delivery.created_at) == today,
        )
    )).scalar() or 0

    finalized_today = (await session.execute(
        select(sa_func.count()).select_from(Delivery).where(
            Delivery.state == "FINALIZADA",
            sa_func.date(Delivery.finalized_at) == today,
        )
    )).scalar() or 0

    return {
        "team_name": team.name,
        "total_couriers": total_couriers,
        "online_couriers": online,
        "pending_kyc": pending_kyc,
        "deliveries_today": deliveries_today,
        "finalized_today": finalized_today,
    }


@router.get("/couriers")
async def list_couriers(user: CurrentUser, session: SessionDep) -> list[dict]:
    team = await _resolve_team(user, session)
    couriers = list(
        (await session.execute(
            select(Courier).where(Courier.team_id == team.id, Courier.deleted_at.is_(None)).order_by(Courier.id)
        )).scalars().all()
    )
    result = []
    for c in couriers:
        docs = list(
            (await session.execute(
                select(CourierDocument).where(CourierDocument.courier_id == c.id).order_by(CourierDocument.id)
            )).scalars().all()
        )
        result.append({
            "id": c.id,
            "full_name": c.full_name,
            "status": c.status,
            "vehicle_type": c.vehicle_type,
            "is_online": c.is_online,
            "documents": [
                {
                    "id": d.id,
                    "kind": d.kind,
                    "status": d.status,
                    "reject_reason": d.reject_reason,
                }
                for d in docs
            ],
        })
    return result


@router.post("/couriers/{courier_id}/documents/{doc_id}/approve")
async def approve_document(
    courier_id: int,
    doc_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    team = await _resolve_team(user, session)
    courier = (
        await session.execute(
            select(Courier).where(Courier.id == courier_id, Courier.team_id == team.id)
        )
    ).scalar_one_or_none()
    if courier is None:
        raise HTTPException(status_code=404, detail="Entregador não encontrado.")
    doc = await session.get(CourierDocument, doc_id)
    if doc is None or doc.courier_id != courier_id:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    doc.status = "approved"
    doc.reject_reason = None
    doc.reject_detail = None

    all_docs = list(
        (await session.execute(
            select(CourierDocument).where(CourierDocument.courier_id == courier_id).order_by(CourierDocument.id.desc())
        )).scalars().all()
    )
    latest_by_kind: dict[str, str] = {}
    for d in all_docs:
        if d.kind not in latest_by_kind:
            latest_by_kind[d.kind] = d.status
    all_approved = bool(latest_by_kind) and all(s == "approved" for s in latest_by_kind.values())
    if all_approved and courier.status == "pending_kyc":
        courier.status = "active"

    await session.commit()
    return {"ok": True, "doc_status": "approved", "courier_status": courier.status}


@router.post("/couriers/{courier_id}/documents/{doc_id}/reject")
async def reject_document(
    courier_id: int,
    doc_id: int,
    body: dict,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    team = await _resolve_team(user, session)
    courier = (
        await session.execute(
            select(Courier).where(Courier.id == courier_id, Courier.team_id == team.id)
        )
    ).scalar_one_or_none()
    if courier is None:
        raise HTTPException(status_code=404, detail="Entregador não encontrado.")
    doc = await session.get(CourierDocument, doc_id)
    if doc is None or doc.courier_id != courier_id:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    doc.status = "rejected"
    doc.reject_reason = body.get("reason", "outro")
    doc.reject_detail = body.get("detail")
    await session.commit()
    return {"ok": True, "doc_status": "rejected"}


@router.get("/couriers/{courier_id}")
async def get_courier_detail(
    courier_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    team = await _resolve_team(user, session)
    courier = (
        await session.execute(
            select(Courier).where(Courier.id == courier_id, Courier.team_id == team.id)
        )
    ).scalar_one_or_none()
    if courier is None:
        raise HTTPException(status_code=404, detail="Entregador não encontrado.")
    from app.auth.models import User as UserModel
    u = await session.get(UserModel, courier.user_id)
    docs = list(
        (await session.execute(
            select(CourierDocument).where(CourierDocument.courier_id == courier.id).order_by(CourierDocument.id)
        )).scalars().all()
    )
    return {
        "id": courier.id,
        "full_name": courier.full_name,
        "cpf_masked": f"***.{(u.cpf or '')[3:6]}.***-{(u.cpf or '')[-2:]}" if u and u.cpf else "***",
        "status": courier.status,
        "kyc_level": courier.kyc_level,
        "vehicle_type": courier.vehicle_type,
        "vehicle_plate": courier.vehicle_plate,
        "created_at": courier.created_at.isoformat() if courier.created_at else None,
        "documents": [
            {
                "id": d.id,
                "kind": d.kind,
                "status": d.status,
                "reject_reason": d.reject_reason,
                "reject_detail": d.reject_detail,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
    }


@router.get("/couriers/{courier_id}/documents/{document_id}/view-url")
async def view_document_url_team(
    courier_id: int,
    document_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    team = await _resolve_team(user, session)
    courier = (
        await session.execute(
            select(Courier).where(Courier.id == courier_id, Courier.team_id == team.id)
        )
    ).scalar_one_or_none()
    if courier is None:
        raise HTTPException(status_code=404, detail="Entregador não encontrado.")
    from app.couriers.view import view_document_url
    from app.integrations.factory import get_storage_adapter
    url, expires_in = await view_document_url(
        session,
        courier_id=courier_id,
        document_id=document_id,
        area_id=team.area_id,
        actor_id=user.id,
        storage=get_storage_adapter(),
    )
    await session.commit()
    return {"url": url, "expires_in": expires_in}


@router.get("/deliveries")
async def list_deliveries(
    user: CurrentUser,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    team = await _resolve_team(user, session)
    courier_ids = [
        c.id for c in (await session.execute(
            select(Courier).where(Courier.team_id == team.id, Courier.deleted_at.is_(None))
        )).scalars().all()
    ]
    if not courier_ids:
        return {"items": [], "total": 0}

    base = select(Delivery).where(Delivery.courier_id.in_(courier_ids))
    total = (await session.execute(select(sa_func.count()).select_from(base.subquery()))).scalar() or 0
    rows = list(
        (await session.execute(
            base.order_by(Delivery.id.desc()).limit(limit).offset(offset)
        )).scalars().all()
    )
    items = []
    for d in rows:
        courier = await session.get(Courier, d.courier_id) if d.courier_id else None
        items.append({
            "id": d.id,
            "state": d.state,
            "pickup_address": d.pickup_address,
            "dropoff_address": d.dropoff_address,
            "price_cents": d.price_cents,
            "courier_name": courier.full_name if courier else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return {"items": items, "total": total}


# ---------------------------------------------------------------------------
# Zonas e preços mínimos
# ---------------------------------------------------------------------------

class TeamZonaSetBody(BaseModel):
    preco_minimo_cents: int


@router.get("/zonas")
async def list_team_zonas(user: CurrentUser, session: SessionDep) -> list[dict]:
    """Retorna todas as zonas da área com o preço mínimo configurado pelo time."""
    team = await _resolve_team(user, session)
    zonas = list(
        (await session.execute(
            select(Zona).where(Zona.area_id == team.area_id).order_by(Zona.id)
        )).scalars().all()
    )
    configs = {
        tz.zona_id: tz
        for tz in (await session.execute(
            select(TeamZona).where(TeamZona.team_id == team.id)
        )).scalars().all()
    }
    return [
        {
            "zona_id": z.id,
            "zona_nome": z.name,
            "preco_minimo_cents": configs[z.id].preco_minimo_cents if z.id in configs else None,
        }
        for z in zonas
    ]


@router.put("/zonas/{zona_id}")
async def set_team_zona(
    zona_id: int,
    body: TeamZonaSetBody,
    user: CurrentUser,
    session: SessionDep,
) -> dict:
    """Define ou atualiza o preço mínimo do time para uma zona."""
    team = await _resolve_team(user, session)
    zona = await session.get(Zona, zona_id)
    if zona is None or zona.area_id != team.area_id:
        raise HTTPException(status_code=404, detail="Zona não encontrada.")
    existing = (await session.execute(
        select(TeamZona).where(TeamZona.team_id == team.id, TeamZona.zona_id == zona_id)
    )).scalar_one_or_none()
    if existing:
        existing.preco_minimo_cents = body.preco_minimo_cents
    else:
        session.add(TeamZona(
            team_id=team.id,
            zona_id=zona_id,
            area_id=team.area_id,
            preco_minimo_cents=body.preco_minimo_cents,
        ))
    await session.commit()
    return {"zona_id": zona_id, "preco_minimo_cents": body.preco_minimo_cents}
