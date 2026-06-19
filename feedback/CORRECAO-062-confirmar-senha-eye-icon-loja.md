# Correção 062 — Campo "Confirmar senha" e ícone fa-eye no cadastro da loja

> **Classe:** UX · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/web/src/features/loja/cadastro/cadastro.page.ts`
- `apps/web/src/features/loja/cadastro/cadastro.page.html`

## Problema

O cadastro da loja não tinha campo "Confirmar senha" e usava emojis (`🙈`/`👁`) como toggle de visibilidade da senha.

## Correção

- Campo `password_confirm` adicionado ao form com `Validators.required`
- Método `passwordMismatch()` valida se as senhas batem
- Emojis substituídos por `fa-icon` (`faEye`/`faEyeSlash`) do Font Awesome
- `FaIconComponent` adicionado aos imports
- `password_confirm` excluído do draft persistence (igual ao `password`)
