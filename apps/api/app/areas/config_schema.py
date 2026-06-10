"""Typed area config (REQ-002 / F-08) + sensitive-change diff for audit.

`Area.config` used to be raw JSON written through `update_area` with no
validation and no audit trail (Pitfall 4). `AreaConfig` (Pydantic v2,
`extra="forbid"`) gives every local rule an explicit range, so an absurd value
that would break the Phase 8 dispatch is rejected with 422 (RFC-7807) at the
boundary:

- `kyc_level`     — "simples" | "completa" (alimenta a Phase 5).
- `piso_entrega`  — R$ por entrega, >= 0 (guard-rail; a plataforma nunca fixa preço).
- `piso_km`       — R$ por km, >= 0.
- `geofence_m`    — 30..300 m (RN-005, default 80).
- `timeout_oferta_s`     — 10..60 s (ADR-104, default 20).
- `timeout_favoritos_s`  — 30..180 s (ADR-007, default 60).
- `politica_retorno_pct` — 0..100 % (default 0).

`SENSITIVE_KEYS` are the 7 keys whose change must be audited (RN-012 / F-08 E2).
`diff_sensitive` returns the (before, after) subset of the sensitive keys that
actually changed, or None — the router turns a non-None diff into a
`write_audit("area.config.update", before, after)` row.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The 7 keys whose change is auditable (RN-012 / F-08 E2).
SENSITIVE_KEYS: frozenset[str] = frozenset(
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


class AreaConfig(BaseModel):
    """Typed local rules for an area (ranges enforced — A03 input validation)."""

    model_config = ConfigDict(extra="forbid")

    kyc_level: Literal["simples", "completa"] = "simples"
    # Money guard-rails (RN-015) — the platform only imposes a floor, never fixes.
    piso_entrega: Decimal = Field(default=Decimal("0"), ge=0)
    piso_km: Decimal = Field(default=Decimal("0"), ge=0)
    # Geofence radius in metres (RN-005).
    geofence_m: int = Field(default=80, ge=30, le=300)
    # Dispatch timeouts (ADR-104 / ADR-007).
    timeout_oferta_s: int = Field(default=20, ge=10, le=60)
    timeout_favoritos_s: int = Field(default=60, ge=30, le=180)
    # Return policy (% over the run).
    politica_retorno_pct: int = Field(default=0, ge=0, le=100)


def diff_sensitive(before: dict, after: dict) -> tuple[dict, dict] | None:
    """Return the (before, after) subset of SENSITIVE_KEYS that changed, or None.

    Values are compared as-is (the caller passes already-serialised dicts, e.g.
    `model_dump(mode="json")`), so a Decimal stored as "2.00" compares stably.
    """
    diff_before: dict = {}
    diff_after: dict = {}
    for key in SENSITIVE_KEYS:
        b = before.get(key)
        a = after.get(key)
        if b != a:
            diff_before[key] = b
            diff_after[key] = a
    if not diff_after:
        return None
    return diff_before, diff_after
