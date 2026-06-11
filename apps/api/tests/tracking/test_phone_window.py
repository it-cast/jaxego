"""Phone window by state (RN-022) — telefones só em ACEITA→FINALIZADA.

`phone_window_open` is the predicate the authenticated party surfaces use; the public
serializer never emits a phone regardless (asserted in test_serializer_pii). Here we
pin RN-022: closed before acceptance and after finalisation, open in between.
"""

from __future__ import annotations

import pytest
from app.tracking.serializer import phone_window_open


@pytest.mark.parametrize(
    ("state", "open_"),
    [
        ("CRIADA", False),  # not accepted yet — closed
        ("ACEITA", True),
        ("COLETADA", True),
        ("ENTREGUE", True),
        ("FINALIZADA", False),  # run done — closed
        ("RECUSADA_NO_DESTINO", False),
        ("CANCELADA", False),
    ],
)
def test_phone_window_by_state(state: str, open_: bool) -> None:
    assert phone_window_open(state) is open_
