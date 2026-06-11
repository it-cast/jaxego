"""POST /v1/deliveries/{id}/locations — courier posts its position (DEC-002 / TH-5).

Operated by the COURIER assigned to the delivery. Ownership is pushed into the WHERE
clause (`get_delivery_for_courier`, reused from proofs.service) → 404 if courier B
posts on courier A's delivery (IDOR closed, never 403 — TH-5 / A01). The sample is
accepted ONLY while the delivery is in the moving window (ACEITA/COLETADA); outside
it → 409 "fora da janela" (a finished/terminal delivery must not keep collecting a
movement trail — LGPD minimisation). The row is lat/lng + aware-UTC `recorded_at`
(TD-010). Leve: 1 ownership SELECT + 1 INSERT (perf budget p95 ≤ 80ms).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.session import get_session
from app.dispatch.dependencies import CourierScopeDep
from app.proofs.service import get_delivery_for_courier
from app.tracking.models import DeliveryLocation

router = APIRouter(prefix="/deliveries", tags=["tracking"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# The moving window where a position is accepted (RN-022 ACEITA→FINALIZADA, but only
# the mobile sub-window ACEITA/COLETADA produces a meaningful courier position).
_TRACKING_WINDOW = frozenset({"ACEITA", "COLETADA"})


class OutOfTrackingWindowError(AppError):
    """A location was posted outside the ACEITA/COLETADA window (409 — TH-4)."""

    status_code = 409
    code = "out_of_tracking_window"

    def __init__(self) -> None:
        super().__init__("Entrega fora da janela de rastreamento.")


class LocationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


@router.post("/{delivery_id}/locations", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_location(
    delivery_id: int,
    body: LocationIn,
    scope: CourierScopeDep,
    session: SessionDep,
) -> Response:
    """Record one courier position sample (only the assignee, only in-window)."""
    delivery = await get_delivery_for_courier(
        session, delivery_id=delivery_id, courier_id=scope.courier_id
    )  # 404 if not the assigned courier (IDOR closed — TH-5)
    if delivery.state not in _TRACKING_WINDOW:
        raise OutOfTrackingWindowError()
    session.add(
        DeliveryLocation(
            area_id=delivery.area_id,
            delivery_id=delivery.id,
            lat=body.lat,
            lng=body.lng,
            recorded_at=datetime.now(UTC),  # AWARE — TD-010
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
