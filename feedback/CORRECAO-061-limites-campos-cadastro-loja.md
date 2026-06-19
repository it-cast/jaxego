# Correção 061 — Campos CPF, CNPJ e telefone sem limite de caracteres no cadastro da loja

> **Classe:** UX · **Data:** 2026-06-19

---

## Arquivo afetado

- `apps/web/src/features/loja/cadastro/cadastro.page.html`

## Problema

Os campos de documento (CPF/CNPJ) e telefone no cadastro da loja não tinham `maxlength`, permitindo digitação além do tamanho válido.

## Correção

- **CNPJ**: `maxlength="18"` (`00.000.000/0001-00`)
- **CPF**: `maxlength="14"` (`000.000.000-00`)
- Maxlength dinâmico via `[attr.maxlength]` conforme o tipo selecionado (CNPJ ou CPF)
- **Telefone**: `maxlength="15"` (`(22) 99999-1234`)
- Placeholder também dinâmico: CNPJ mostra `00.000.000/0001-00`, CPF mostra `000.000.000-00`
