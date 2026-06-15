"""ADR-013 isolation: the score NEVER affects dispatch ordering (T-04).

Two structural proofs:
1. Static: `app.dispatch.ranking` does NOT import anything from `app.scores`, and
   `app.dispatch.cascade` does not read a courier snapshot. (The dependency must not
   exist — score is collected/exhibited, never financially/operationally weighted in M1.)
2. Behavioural: `rank_key` ignores the `score` argument — flipping the score from 0 to
   100 leaves the sort key unchanged (the M1 weight is ZERO).
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.dispatch.ranking import rank_key

_APP = Path(__file__).resolve().parents[2] / "app"


def _imports_module(py_file: Path, forbidden_prefix: str) -> bool:
    """True if `py_file` imports any module under `forbidden_prefix`."""
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == forbidden_prefix or node.module.startswith(forbidden_prefix + "."):
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == forbidden_prefix or alias.name.startswith(forbidden_prefix + "."):
                    return True
    return False


def test_ranking_does_not_import_scores() -> None:
    """ADR-013: dispatch/ranking.py must not depend on app.scores."""
    assert not _imports_module(_APP / "dispatch" / "ranking.py", "app.scores")


def test_cascade_does_not_import_scores() -> None:
    """ADR-013: the dispatch cascade must not read score snapshots."""
    assert not _imports_module(_APP / "dispatch" / "cascade.py", "app.scores")


def test_rank_key_ignores_score() -> None:
    """Flipping score 0 → 100 must NOT change the sort key (M1 weight is ZERO)."""
    base = rank_key(eta_s=300, load=1, price_cents=500, score=0.0)
    boosted = rank_key(eta_s=300, load=1, price_cents=500, score=100.0)
    assert base == boosted
