"""Guard against naive datetime in domain code (TD-010).

Audited bug from v1.0: `grace_boundary.replace(tzinfo=None)` silently dropped
the timezone. This AST-based guard rejects, in `app/`:

  - `datetime.now()`              (no tz argument)
  - `datetime.utcnow()`          (naive by definition, deprecated)
  - `datetime.today()`           (naive local time)
  - `.replace(tzinfo=None)`      (strips the timezone — the audited bug)

It ALLOWS:

  - `datetime.now(timezone.utc)` / `datetime.now(tz=...)`
  - `.replace(tzinfo=timezone.utc)` and any non-None tzinfo

Usage:
    python tools/check_naive_datetime.py [path ...]

Exit code 0 = clean, 1 = violations found. Designed to run in CI and via a
pytest test (`tests/test_naive_datetime_guard.py`).
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# Directory scanned by default (relative to this file: apps/api/app).
DEFAULT_TARGETS = [Path(__file__).resolve().parent.parent / "app"]


@dataclass(frozen=True)
class Violation:
    """A single naive-datetime violation."""

    file: Path
    line: int
    col: int
    rule: str
    snippet: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.col}: {self.rule} -> {self.snippet}"


def _attr_chain(node: ast.AST) -> str:
    """Best-effort dotted-name of an attribute/name chain (e.g. datetime.now)."""
    if isinstance(node, ast.Attribute):
        return f"{_attr_chain(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return ""


class _NaiveDatetimeVisitor(ast.NodeVisitor):
    """Walk a module AST collecting naive-datetime violations."""

    # Calls that are naive unless given a tz argument.
    _NOW_LIKE = {"now", "today"}
    # Calls that are always naive (no tz arg fixes them).
    _ALWAYS_NAIVE = {"utcnow", "utcfromtimestamp"}

    def __init__(self, file: Path) -> None:
        self.file = file
        self.violations: list[Violation] = []

    def _add(self, node: ast.AST, rule: str, snippet: str) -> None:
        self.violations.append(
            Violation(
                file=self.file,
                line=getattr(node, "lineno", 0),
                col=getattr(node, "col_offset", 0),
                rule=rule,
                snippet=snippet,
            )
        )

    @staticmethod
    def _has_tz_arg(call: ast.Call) -> bool:
        """True if the call passes a timezone (positional or `tz=`)."""
        if any(kw.arg in {"tz", "tzinfo"} for kw in call.keywords):
            return True
        # datetime.now(timezone.utc) — positional tz argument.
        return bool(call.args)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 (ast API)
        func = node.func
        if isinstance(func, ast.Attribute):
            method = func.attr
            chain = _attr_chain(func)

            if method in self._ALWAYS_NAIVE:
                self._add(node, "naive-datetime-utcnow", f"{chain}(...)")

            elif method in self._NOW_LIKE and not self._has_tz_arg(node):
                # Only flag when it looks like a datetime call (heuristic on chain).
                if "datetime" in chain or chain.endswith(".now") or chain.endswith(".today"):
                    self._add(node, "naive-datetime-now", f"{chain}()")

            elif method == "replace" and self._replaces_tz_with_none(node):
                self._add(node, "naive-datetime-replace-tzinfo-none", f"{chain}(tzinfo=None)")

        self.generic_visit(node)

    @staticmethod
    def _replaces_tz_with_none(call: ast.Call) -> bool:
        """True for `.replace(tzinfo=None)` — the audited bug."""
        for kw in call.keywords:
            if kw.arg == "tzinfo" and isinstance(kw.value, ast.Constant) and kw.value.value is None:
                return True
        return False


def check_source(source: str, file: Path) -> list[Violation]:
    """Return violations found in a single source string."""
    tree = ast.parse(source, filename=str(file))
    visitor = _NaiveDatetimeVisitor(file)
    visitor.visit(tree)
    return visitor.violations


def iter_python_files(targets: Iterable[Path]) -> Iterable[Path]:
    """Yield all .py files under the given targets (files or directories)."""
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            yield target
        elif target.is_dir():
            yield from sorted(target.rglob("*.py"))


def check_paths(targets: Iterable[Path]) -> list[Violation]:
    """Scan all .py files under targets for naive-datetime violations."""
    violations: list[Violation] = []
    for path in iter_python_files(targets):
        violations.extend(check_source(path.read_text(encoding="utf-8"), path))
    return violations


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Returns process exit code."""
    args = argv if argv is not None else sys.argv[1:]
    targets = [Path(a) for a in args] if args else DEFAULT_TARGETS
    violations = check_paths(targets)
    if violations:
        print("Naive datetime violations (TD-010):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print("OK: no naive datetime in domain code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
