# Correção 002 — Validação de senha no formulário de login (frontend + backend + HTML)

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/src/features/auth/login.page.ts`
- `apps/web/src/features/auth/login.page.html`
- `apps/api/app/auth/schemas.py`

## Problema

O campo de senha tinha validação `minLength(10)` em três lugares: validator TypeScript no `.ts`, atributo `minlength="10"` no HTML (que o Angular converte em validator automaticamente ao usar `formControlName`), e `Field(min_length=PASSWORD_MIN_LENGTH)` no schema Pydantic do backend. Qualquer senha com menos de 10 caracteres fazia o submit não acontecer — sem feedback claro para o usuário.

## Correção

- Removido `Validators.minLength(10)` do `login.page.ts`
- Removido atributo `minlength="10"` do `login.page.html`
- Alterado para `min_length=1` no schema de login do backend (`schemas.py`)

## Nota

Validação de comprimento mínimo pertence ao cadastro/troca de senha, não ao login.
