"""Exhaustive state-machine tests (REQ-022 / TH-01 / D-03).

The 7-state machine (RN-019) is defined in full NOW even though only CRIADA and
CANCELADA are reachable in Phase 7. Every (current, target) pair from the
cartesian product of the 7 states is checked: the valid ones pass, ALL the
invalid ones raise InvalidTransitionError (422). This is the antifraude
invariant — the server never trusts a client-supplied target state.
"""

from __future__ import annotations

from itertools import product

import pytest
from app.deliveries.state_machine import (
    DELIVERY_STATES,
    DELIVERY_TRANSITIONS,
    InvalidTransitionError,
    assert_delivery_transition,
)


def test_seven_states_defined() -> None:
    assert len(DELIVERY_STATES) == 7
    assert set(DELIVERY_TRANSITIONS.keys()) == set(DELIVERY_STATES)


def test_valid_transitions_pass() -> None:
    for current, targets in DELIVERY_TRANSITIONS.items():
        for target in targets:
            assert_delivery_transition(current, target)  # must not raise


def test_all_invalid_transitions_raise_422() -> None:
    """Cartesian product minus the valid set → every invalid pair raises 422."""
    valid = {(c, t) for c, targets in DELIVERY_TRANSITIONS.items() for t in targets}
    for current, target in product(DELIVERY_STATES, DELIVERY_STATES):
        if (current, target) in valid:
            continue
        with pytest.raises(InvalidTransitionError) as exc:
            assert_delivery_transition(current, target)
        assert exc.value.status_code == 422


def test_terminal_states_have_no_exits() -> None:
    assert DELIVERY_TRANSITIONS["CANCELADA"] == set()
    assert DELIVERY_TRANSITIONS["FINALIZADA"] == set()


def test_criada_can_only_go_to_aceita_or_cancelada() -> None:
    assert DELIVERY_TRANSITIONS["CRIADA"] == {"ACEITA", "CANCELADA"}


def test_self_transition_invalid() -> None:
    for state in DELIVERY_STATES:
        with pytest.raises(InvalidTransitionError):
            assert_delivery_transition(state, state)
