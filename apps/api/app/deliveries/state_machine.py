"""Delivery state machine (RN-019 / D-03). Invalid transition → 422.

Mirrors `couriers/state_machine.py`: explicit transition map (`dict[str, set[str]]`),
an `assert_delivery_transition` that raises a 422 AppError, and the service records
each transition in `delivery_state_transitions` (append-only — RN-012). The WHOLE
machine (7 states) is defined NOW even though only CRIADA and CANCELADA are
reachable in Phase 7; ACEITA+ are exercised in Phases 8/9. A new state requires an
ADR (D-03).

Transition set confirmed against fluxos.md F-03 (create) / F-05 (dispatch+accept) /
F-06 (delivery+refusal):
  - CRIADA → ACEITA (Phase 8 accept) | CANCELADA (store cancels pre-acceptance, zero cost)
    | SEM_RESPOSTA (cascade exhausted — every eligible courier declined or hit the
    timeout cap, `app/workers/dispatch.py`)
  - SEM_RESPOSTA → ACEITA (a courier self-assigns from the unanswered pool) | CANCELADA
  - ACEITA → COLETADA (Phase 9 pickup) | CRIADA (courier desiste depois de
    aceitar, antes de coletar — CORRECAO-262: reabre a entrega pra fila de
    despacho, excluído da nova rodada, mesmo tratamento de uma recusa ativa).
    No CANCELADA (CORRECAO-249/250): a loja não cancela mais em-app depois do
    aceite. O custo RN-004 de 50%/100% nunca foi ligado a uma cobrança/repasse
    real, então permitir isso só deixava dinheiro de PIX preso sem ninguém
    compensado — volta quando a Phase 11 (faturamento) definir um custo real
    pós-aceite.
  - COLETADA → ENTREGUE | RECUSADA_NO_DESTINO (F-06 refusal) — no CANCELADA, same reason.
  - ENTREGUE → FINALIZADA (Phase 9 settle job)
  - RECUSADA_NO_DESTINO → FINALIZADA (settle with refusal)
  - CANCELADA / FINALIZADA → terminal (no exits)
"""

from __future__ import annotations

from app.core.exceptions import AppError

# The 9 canonical states (RN-019 / D-03).
# AGENDADA is the initial state for scheduled deliveries; Inngest transitions
# it to CRIADA at the scheduled time to kick off the dispatch cascade.
# SEM_RESPOSTA is reached when the dispatch cascade exhausts every eligible
# courier (decline or 10x timeout) — it sits outside the cascade until a
# courier self-assigns it from the unanswered pool (D-03 ADR — see dispatch).
DELIVERY_STATES = (
    "AGENDADA",
    "AGUARDANDO_PAGAMENTO",
    "CRIADA",
    "SEM_RESPOSTA",
    "ACEITA",
    "COLETADA",
    "ENTREGUE",
    "RECUSADA_NO_DESTINO",
    "CANCELADA",
    "FINALIZADA",
)

# Valid transitions (RN-019). Defined in full now; only CRIADA/CANCELADA are
# exercised in Phase 7, the rest are covered by tests and enabled in Phases 8/9.
DELIVERY_TRANSITIONS: dict[str, set[str]] = {
    "AGENDADA": {"CRIADA", "CANCELADA"},  # CRIADA = Inngest fires; CANCELADA = store cancels
    "AGUARDANDO_PAGAMENTO": {"CRIADA", "CANCELADA"},  # CRIADA = PIX confirmed; CANCELADA = timeout/cancel
    "CRIADA": {"ACEITA", "CANCELADA", "SEM_RESPOSTA"},
    "SEM_RESPOSTA": {"ACEITA", "CANCELADA"},  # self-assign from the pool, or store cancels
    "ACEITA": {"COLETADA", "CRIADA"},  # CRIADA = courier desiste pré-coleta (CORRECAO-262)
    "COLETADA": {"ENTREGUE", "RECUSADA_NO_DESTINO"},  # no CANCELADA post-acceptance
    "ENTREGUE": {"FINALIZADA"},
    "RECUSADA_NO_DESTINO": {"FINALIZADA"},
    "CANCELADA": set(),  # terminal
    "FINALIZADA": set(),  # terminal
}


class InvalidTransitionError(AppError):
    """An illegal delivery state transition was attempted (422 — TH-01)."""

    status_code = 422
    code = "invalid_transition"

    def __init__(self, current: str | None, target: str) -> None:
        super().__init__(f"Transição de status inválida: {current} → {target}.")


def assert_delivery_transition(current: str, target: str) -> None:
    """Raise InvalidTransitionError unless current→target is allowed (RN-019)."""
    if target not in DELIVERY_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
