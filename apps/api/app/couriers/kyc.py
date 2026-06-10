"""KYC level rules (ADR-011 / RN-002) — which documents each level requires.

SIMPLES: CPF + selfie + phone + email (selfie is the only uploaded document).
COMPLETA: simples + CNH (with EAR) + CRLV + antecedentes (if the area requires) +
MEI (consulted via Receita — its absence does NOT block, it sets mei_pending,
RN-024). The area configures its minimum level (`area.config["kyc_level"]`);
never below simples.

A courier becomes `active` only when EVERY required document for its level is
`approved` (RN-002). MEI is NOT a blocking document: an inactive MEI yields
`mei_pending` and the courier can still activate (direct-payment only). This
module is pure logic; the service applies it.
"""

from __future__ import annotations

# Documents required for activation, per level. MEI is intentionally excluded —
# it is handled by the mei_pending flag (RN-024), not as a blocking item.
SIMPLES_REQUIRED = ("selfie",)
COMPLETA_REQUIRED = ("selfie", "cnh", "crlv")

# MEI compatible CNAEs (D-07). An active MEI with one of these → not pending.
COMPATIBLE_CNAES = frozenset({"4930-2/01", "4930-2/02", "5320-2/02", "5229-0/99"})

VALID_LEVELS = ("simples", "completa")


def required_documents(level: str, *, antecedentes_required: bool = False) -> tuple[str, ...]:
    """The document kinds that must be `approved` for activation at this level."""
    if level == "completa":
        docs: list[str] = list(COMPLETA_REQUIRED)
        if antecedentes_required:
            docs.append("antecedentes")
        return tuple(docs)
    return SIMPLES_REQUIRED


def all_required_approved(
    level: str, approved_kinds: set[str], *, antecedentes_required: bool = False
) -> bool:
    """True when every required document for the level is approved (RN-002)."""
    required = set(required_documents(level, antecedentes_required=antecedentes_required))
    return required.issubset(approved_kinds)


def normalize_cnae(raw: str) -> str:
    """Normalise a CNAE to the dotted/slashed form used in COMPATIBLE_CNAES.

    Accepts `4930201`, `4930-2/01` etc. and returns `4930-2/01`. A value that
    cannot be normalised is returned stripped (it simply won't match).
    """
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) == 7:
        return f"{digits[:4]}-{digits[4]}/{digits[5:]}"
    return raw.strip()


def is_mei_compatible(situacao: str | None, cnaes: list[str]) -> bool:
    """True when the MEI is active AND has at least one compatible CNAE (D-07)."""
    if situacao != "ativa":
        return False
    return any(normalize_cnae(c) in COMPATIBLE_CNAES for c in cnaes)
