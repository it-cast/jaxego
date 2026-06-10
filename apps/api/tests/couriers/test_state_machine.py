"""Courier + document state machine transitions (T-06). Invalid → 422.

Asserts the explicit transition maps reject illegal moves (InvalidTransitionError,
422) and accept the legal ones. The per-document machine is what powers E4: a
rejected document can return to pending_upload (re-upload that item).
"""

from __future__ import annotations

import pytest
from app.couriers.state_machine import (
    InvalidTransitionError,
    assert_courier_transition,
    assert_document_transition,
)


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending_kyc", "active"),
        ("pending_kyc", "banned"),
        ("active", "suspended"),
        ("suspended", "active"),
    ],
)
def test_valid_courier_transitions(current: str, target: str) -> None:
    assert_courier_transition(current, target)  # no raise


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending_kyc", "suspended"),  # must go through active first
        ("active", "pending_kyc"),  # cannot go back
        ("banned", "active"),  # terminal
    ],
)
def test_invalid_courier_transitions(current: str, target: str) -> None:
    with pytest.raises(InvalidTransitionError):
        assert_courier_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending_upload", "pending"),
        ("pending", "approved"),
        ("pending", "rejected"),
        ("rejected", "pending_upload"),  # E4 re-upload just this item
        ("approved", "expired"),  # expiry job
        ("expired", "pending_upload"),
    ],
)
def test_valid_document_transitions(current: str, target: str) -> None:
    assert_document_transition(current, target)  # no raise


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending_upload", "approved"),  # cannot skip review
        ("approved", "pending"),  # cannot go back to queue
        ("pending", "pending_upload"),  # only via rejected/expired
    ],
)
def test_invalid_document_transitions(current: str, target: str) -> None:
    with pytest.raises(InvalidTransitionError):
        assert_document_transition(current, target)
