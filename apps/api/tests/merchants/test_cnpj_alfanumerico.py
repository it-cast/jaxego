"""T-13 — CNPJ alfanumérico (jul/2026): validate-docbr 2.0.0 deve aceitar.

Resolve o item LOW do RESEARCH (A7). Se a lib instalada falhar com o formato
novo, este teste vermelho sinaliza a troca de lib (documentada como TD).
"""

from __future__ import annotations

from app.merchants.schemas import normalize_document, validate_document

# Exemplo oficial Serpro de CNPJ alfanumérico válido (12.ABC.345/01DE-35).
ALFANUMERICO_VALIDO = "12ABC34501DE35"
ALFANUMERICO_TAMPERED = "12ABC34501DE34"


def test_validate_docbr_aceita_cnpj_alfanumerico() -> None:
    assert validate_document(ALFANUMERICO_VALIDO, account_type="cnpj") is True


def test_validate_docbr_rejeita_cnpj_alfanumerico_adulterado() -> None:
    assert validate_document(ALFANUMERICO_TAMPERED, account_type="cnpj") is False


def test_normalize_mantem_alfanumerico_uppercase() -> None:
    # Normalização mantém os caracteres alfanuméricos (não só dígitos) e uppercase.
    assert normalize_document("12.abc.345/01de-35") == "12ABC34501DE35"


def test_validate_docbr_aceita_cnpj_numerico() -> None:
    assert validate_document("11.222.333/0001-81", account_type="cnpj") is True


def test_validate_docbr_rejeita_sequencia_repetida() -> None:
    assert validate_document("00000000000000", account_type="cnpj") is False
