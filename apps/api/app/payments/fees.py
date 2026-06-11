"""Platform fee + revenue share + split builder + refund amount (Phase 10).

Money is integer CENTS, computed in the backend ONLY (TH-F / A04 — the frontend never
sends fee/split values). The split invariant `amount == Σ splits` holds by construction:
the courier gets the corrida intact; Jaxegô gets the taxa (which already embeds the
revenue share). Any rounding residual stays on the Jaxegô leg, so the sum is always exact
(Pitfall 6).

Fee + revenue share are parametrised (seed/config — A6/A7), NEVER hardcoded; only the
value changes. `refund_amount_cents` implements RN-004 (pre-acceptance total; accepted 50%;
post-collection keep 100%+return → refund the excess).
"""

from __future__ import annotations

from app.payments.port import Split


def build_splits(
    *,
    corrida_cents: int,
    taxa_cents: int,
    courier_recipient: str,
    jaxego_recipient: str,
    revenue_share_pct: int,
) -> list[Split]:
    """Build the two-leg split. Invariant: corrida+taxa == Σ splits (TH-F).

    The courier receives the corrida intact (it then sits in the 24h escrow). Jaxegô
    receives the taxa — the `revenue_share_pct` is informational here (the area's share of
    the platform fee, surfaced in a Phase 13 report); it does NOT change the cents that
    leave the payer, only how Jaxegô later attributes its own leg. Any rounding residual
    stays on the Jaxegô leg so the sum is always exact.
    """
    # revenue_share_pct is validated/clamped but does not alter the payer-facing sum.
    _ = max(0, min(100, revenue_share_pct))
    if courier_recipient:
        splits = [
            Split(recipient=courier_recipient, amount_cents=corrida_cents),
            Split(recipient=jaxego_recipient, amount_cents=taxa_cents),
        ]
    else:
        # No courier subaccount yet (delivery created before acceptance): the whole amount
        # goes to the Jaxegô recipient; the corrida owed to the future courier is tracked in
        # the internal escrow ledger and split on payout (Phase 11). Invariant preserved.
        splits = [Split(recipient=jaxego_recipient, amount_cents=corrida_cents + taxa_cents)]
    # Defensive invariant — a broken split must never reach Safe2Pay (TH-F).
    assert corrida_cents + taxa_cents == sum(s.amount_cents for s in splits)
    return splits


def refund_amount_cents(*, state: str, charged_cents: int, return_pct: int) -> int:
    """RN-004 refund (cents) for cancelling in `state`, given the amount charged.

    - CRIADA (pre-acceptance): full refund.
    - ACEITA (accepted, not collected): 50% cost kept → refund the other 50%.
    - COLETADA (collected): keep 100% + return policy% → refund the excess (≥0, capped).
    - terminal/other: nothing to refund.
    """
    if charged_cents <= 0:
        return 0
    if state == "CRIADA":
        return charged_cents
    if state == "ACEITA":
        return charged_cents - charged_cents // 2  # refund the half not kept
    if state == "COLETADA":
        cost = charged_cents + (charged_cents * max(return_pct, 0)) // 100
        return max(0, charged_cents - cost)  # refund only the excess paid
    return 0
