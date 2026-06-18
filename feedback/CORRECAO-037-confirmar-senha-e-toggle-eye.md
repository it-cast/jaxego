# Correção 037 — Campo "Confirmar senha" e toggle de visibilidade no cadastro do entregador

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Problema

O formulário de cadastro do entregador tinha apenas o campo "Senha" sem confirmação e sem forma de visualizar o que foi digitado.

## Implementação

- Campo `password_confirm` adicionado ao form (`Validators.required`)
- Validação `passwordMismatch()`: compara password com password_confirm, exibe erro "As senhas não coincidem" inline
- `submitStep1` bloqueia envio se senhas não batem
- Toggle de visibilidade com `fa-eye` / `fa-eye-slash` (Font Awesome) em ambos os campos, controlado pelo signal `showPassword`
- Botão de olho: 44×44px touch target, posicionado absoluto à direita do input
