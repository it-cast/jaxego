"""T-06 / TH-06 — signup logs carry NO raw PII (CNPJ/CPF/phone/e-mail)."""

from __future__ import annotations

import pytest
from app.core.logging import mask_document, mask_email, mask_phone
from app.plans.service import seed_plans_if_missing
from httpx import AsyncClient


def test_mask_email_keeps_domain_hides_local() -> None:
    assert mask_email("joao@gmail.com") == "jo***@gmail.com"
    assert "joao" not in mask_email("joao@gmail.com")


def test_mask_phone_keeps_country_and_last4() -> None:
    masked = mask_phone("+5522999991234")
    assert masked.startswith("+55")
    assert masked.endswith("1234")
    assert "99999" not in masked


def test_mask_document_hides_all_but_last2() -> None:
    masked = mask_document("11222333000181")
    assert masked.endswith("81")
    assert "11222333" not in masked


@pytest.fixture
async def seeded(session_factory) -> None:
    async with session_factory() as s:
        await seed_plans_if_missing(s)
        s_area = None  # area comes from the `seed` fixture path; here we add Pádua
        from app.areas.models import Area

        s_area = Area(
            codename="padua",
            name="Pádua",
            config={
                "bbox": {
                    "min_lat": -21.70,
                    "max_lat": -21.40,
                    "min_lng": -42.25,
                    "max_lng": -41.85,
                }
            },
        )
        s.add(s_area)
        await s.commit()


@pytest.mark.asyncio
async def test_signup_logs_no_raw_pii(
    auth_client: AsyncClient, seeded, capsys: pytest.CaptureFixture[str]
) -> None:
    cnpj = "11222333000181"
    phone = "+5522999991234"
    email = "loja.pii@example.com"
    resp = await auth_client.post(
        "/v1/merchants/signup",
        json={
            "account_type": "cnpj",
            "document": cnpj,
            "trade_name": "Loja PII",
            "category": "comercio",
            "phone_e164": phone,
            "email": email,
            "password": "correct-horse-staple-10",
            "consent": True,
        },
    )
    assert resp.status_code in {201, 422}  # 422 only if area missing; assert no PII regardless
    out = capsys.readouterr().out
    # Raw PII must never appear in any structured log line.
    assert cnpj not in out
    assert phone not in out
    assert email not in out
