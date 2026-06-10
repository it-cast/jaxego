"""Tests for the naive-datetime guard (TD-010).

Proves the guard (a) approves the real project code, (b) detects each forbidden
pattern in synthetic snippets, and (c) allows timezone-aware constructions.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tools.check_naive_datetime import check_paths, check_source

APP_DIR = Path(__file__).resolve().parent.parent / "app"
GUARD_FILE = Path("snippet.py")


def test_project_code_is_clean() -> None:
    """The real app/ code is born clean (no naive datetime)."""
    violations = check_paths([APP_DIR])
    assert violations == [], f"Unexpected naive datetime in app/: {violations}"


@pytest.mark.parametrize(
    ("snippet", "expected_rule"),
    [
        (
            "import datetime\nx = datetime.datetime.now()\n",
            "naive-datetime-now",
        ),
        (
            "import datetime\nx = datetime.datetime.utcnow()\n",
            "naive-datetime-utcnow",
        ),
        (
            # The exact audited v1.0 bug.
            "grace_boundary = grace_boundary.replace(tzinfo=None)\n",
            "naive-datetime-replace-tzinfo-none",
        ),
        (
            "import datetime\nx = datetime.datetime.today()\n",
            "naive-datetime-now",
        ),
    ],
)
def test_guard_detects_forbidden(snippet: str, expected_rule: str) -> None:
    """Each forbidden pattern is flagged with the right rule."""
    violations = check_source(snippet, GUARD_FILE)
    assert violations, f"Expected a violation for: {snippet!r}"
    assert any(v.rule == expected_rule for v in violations), (
        f"Expected rule {expected_rule}, got {[v.rule for v in violations]}"
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "from datetime import datetime, timezone\nx = datetime.now(timezone.utc)\n",
        "from datetime import datetime, timezone\nx = datetime.now(tz=timezone.utc)\n",
        "x = dt.replace(tzinfo=timezone.utc)\n",
        "x = dt.replace(hour=0, minute=0)\n",
    ],
)
def test_guard_allows_aware(snippet: str) -> None:
    """Timezone-aware constructions and unrelated replace() are allowed."""
    violations = check_source(snippet, GUARD_FILE)
    assert violations == [], f"Aware snippet wrongly flagged: {snippet!r} -> {violations}"
