"""Typed area config (REQ-002 / F-08) + sensitive-change diff for audit.

`Area.config` used to be raw JSON written through `update_area` with no
validation and no audit trail (Pitfall 4). `AreaConfig` (Pydantic v2,
`extra="ignore"`) gives every local rule an explicit range, so an absurd value
that would break the Phase 8 dispatch is rejected with 422 (RFC-7807) at the
boundary:

- `kyc_level`                  — "simples" | "completa" (alimenta a Phase 5).
- `timeout_oferta_s`           — 10..60 s (ADR-104, default 20).
- `timeout_favoritos_s`        — 30..180 s (ADR-007, default 60).
- `max_entregas_simultaneas`   — 1..10; limite de entregas ativas por entregador
                                 desta área antes de ele parar de receber ofertas.

Pricing floors (piso_entrega / piso_km) and geofence_m / politica_retorno_pct
were removed — pricing is now handled per-zone by teams.

`SENSITIVE_KEYS` are the keys whose change must be audited (RN-012 / F-08 E2).
`diff_sensitive` returns the (before, after) subset of the sensitive keys that
actually changed, or None — the router turns a non-None diff into a
`write_audit("area.config.update", before, after)` row.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The keys whose change is auditable (RN-012 / F-08 E2).
SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "kyc_level",
        "timeout_oferta_s",
        "timeout_favoritos_s",
        "max_entregas_simultaneas",
    }
)


class AreaConfig(BaseModel):
    """Typed local rules for an area (ranges enforced — A03 input validation)."""

    model_config = ConfigDict(extra="ignore")

    kyc_level: Literal["simples", "completa"] = "simples"
    # Dispatch timeouts (ADR-104 / ADR-007).
    timeout_oferta_s: int = Field(default=20, ge=10, le=60)
    timeout_favoritos_s: int = Field(default=60, ge=30, le=180)
    # Limite de entregas ativas simultâneas por entregador nesta área.
    max_entregas_simultaneas: int = Field(default=1, ge=1, le=10)


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
