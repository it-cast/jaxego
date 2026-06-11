"""Fixtures for the proof pipeline tests (Phase 9, T-03).

`make_jpeg_with_gps` writes a real JPEG with a GPS EXIF block via piexif (TEST-ONLY
— production reads EXIF with Pillow, never piexif). `make_jpeg_no_gps` is a plain
JPEG. A filesystem-backed StorageStubAdapter under a tmp root lets the pipeline
`fetch` the RAW the way it would from B2, with NO network.

`proof_seed` builds a delivery ASSIGNED to a courier, in a state ready for a pickup
(ACEITA) proof, with pickup/dropoff lat/lng near a known POINT so the geofence has a
real target. The area's geofence_m is the default 80 m.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import piexif
import pytest
import pytest_asyncio
from app.areas.models import Area
from app.auth.models import User
from app.core.security import hash_password
from app.couriers.models import Courier
from app.deliveries.models import Delivery
from app.integrations.storage_stub import StorageStubAdapter
from app.merchants.models import Merchant
from app.neighborhoods.models import Neighborhood
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Known Pádua-ish target. Near = ~55 m (inside 80 m); Far = ~1.1 km (outside).
TARGET_LAT, TARGET_LNG = -21.5400, -42.1800
NEAR_LAT, NEAR_LNG = -21.5405, -42.1800
FAR_LAT, FAR_LNG = -21.5500, -42.1800


def _deg_to_dms_rational(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Convert decimal degrees to ((d,1),(m,1),(s,100)) rationals for piexif."""
    value = abs(value)
    deg = int(value)
    minutes_full = (value - deg) * 60
    minutes = int(minutes_full)
    sec = round((minutes_full - minutes) * 60 * 100)
    return ((deg, 1), (minutes, 1), (sec, 100))


def make_jpeg_with_gps(lat: float, lng: float) -> bytes:
    """A real JPEG carrying a GPS EXIF block at (lat, lng)."""
    img = Image.new("RGB", (32, 32), (120, 90, 60))
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: "S" if lat < 0 else "N",
        piexif.GPSIFD.GPSLatitude: _deg_to_dms_rational(lat),
        piexif.GPSIFD.GPSLongitudeRef: "W" if lng < 0 else "E",
        piexif.GPSIFD.GPSLongitude: _deg_to_dms_rational(lng),
    }
    exif_bytes = piexif.dump({"GPS": gps_ifd})
    out = io.BytesIO()
    img.save(out, format="JPEG", exif=exif_bytes)
    return out.getvalue()


def make_jpeg_no_gps() -> bytes:
    """A plain JPEG with no GPS EXIF."""
    img = Image.new("RGB", (32, 32), (60, 90, 120))
    out = io.BytesIO()
    img.save(out, format="JPEG")
    return out.getvalue()


@pytest.fixture
def storage_stub(tmp_path: Path) -> StorageStubAdapter:
    return StorageStubAdapter(root=tmp_path / "b2-proofs")


@dataclass
class ProofSeed:
    area_id: int
    delivery_id: int
    courier_id: int
    courier_user_id: int
    other_courier_id: int


@pytest_asyncio.fixture
async def proof_seed(session_factory: async_sessionmaker[AsyncSession]) -> ProofSeed:
    """A delivery ASSIGNED to a courier, in ACEITA, with pickup/dropoff POINTs."""
    async with session_factory() as s:
        area = Area(codename="padua", name="Pádua", config={})
        s.add(area)
        await s.flush()

        nbhd = Neighborhood(area_id=area.id, name="Centro", is_informal=False)
        s.add(nbhd)
        await s.flush()

        merchant = Merchant(
            area_id=area.id,
            account_type="cnpj",
            document="11222333000181",
            trade_name="Loja",
            category="restaurante",
            phone_e164="+5522999991111",
            email="loja@example.com",
            status="active",
        )
        s.add(merchant)
        await s.flush()

        courier_user = User(
            email="entregador@example.com",
            name="João Entregador",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        other_user = User(
            email="maria@example.com",
            name="Maria Entregadora",
            password_hash=hash_password("correct-horse-staple-10"),
            platform_role="user",
        )
        s.add_all([courier_user, other_user])
        await s.flush()

        courier = Courier(
            area_id=area.id,
            user_id=courier_user.id,
            cpf="39053344705",
            full_name="João Entregador",
            phone_e164="+5522999990000",
            email="entregador@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            max_concurrent=2,
        )
        other_courier = Courier(
            area_id=area.id,
            user_id=other_user.id,
            cpf="52998224725",
            full_name="Maria Entregadora",
            phone_e164="+5522999990001",
            email="maria@example.com",
            kyc_level="simples",
            status="active",
            vehicle_type="moto",
            is_online=True,
            max_concurrent=2,
        )
        s.add_all([courier, other_courier])
        await s.flush()

        delivery = Delivery(
            area_id=area.id,
            merchant_id=merchant.id,
            courier_id=courier.id,
            recipient_id=None,
            state="ACEITA",
            dispatch_mode="direct",
            payment_method="direct",
            proof_method="photo",
            pickup_address="Rua do Comércio, 100",
            pickup_lat=TARGET_LAT,
            pickup_lng=TARGET_LNG,
            dropoff_address="Rua das Flores, 200",
            dropoff_neighborhood_id=nbhd.id,
            dropoff_lat=TARGET_LAT,
            dropoff_lng=TARGET_LNG,
            reference_number="A1B2C3",
            fee_cents=0,
            items_quantity=1,
            public_token="01HZ0PROOFSEED00000000000A",
            origin="manual",
        )
        s.add(delivery)
        await s.flush()
        await s.commit()
        return ProofSeed(
            area_id=area.id,
            delivery_id=delivery.id,
            courier_id=courier.id,
            courier_user_id=courier_user.id,
            other_courier_id=other_courier.id,
        )
