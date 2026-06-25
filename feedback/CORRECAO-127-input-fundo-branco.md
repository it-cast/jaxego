# CORRECAO-127 — Fundo branco nos inputs de texto do formulário de entrega

## O que mudou

### Frontend (packages/shared)
- **field.component.scss**: Background do `.jx-field__input` alterado de `var(--surface-elevated)` para `var(--surface, #fff)`. Dentro de cards (que já usam `--surface-elevated` como fundo), os inputs ficavam sem contraste visual. Agora ficam iguais aos selects (fundo branco).

## Arquivos alterados
- packages/shared/src/shared/components/field/field.component.scss
