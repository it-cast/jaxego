---
classe: feature
data: 2026-07-07
arquivos_afetados:
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.html
---

## Feature: seleção de método de pagamento antes de exibir o formulário

### Antes
`payMethod` iniciava como `signal<'card' | 'pix'>('card')`, exibindo o formulário
de cartão imediatamente ao chegar na etapa "Ativar plano".

### Depois
`payMethod` mudou para `signal<'card' | 'pix' | null>(null)`.
Ao entrar na etapa de pagamento, o usuário vê apenas dois botões:
- **Cartão de crédito**
- **Pix recorrente**

O formulário (cartão ou PIX) e o botão de submit só aparecem após o clique
em um dos dois botões. Condição adicionada: `payMethod() !== null`.

### Arquivos alterados
- `cadastro.page.ts`: tipo do signal `'card' | 'pix'` → `'card' | 'pix' | null`; default `'card'` → `null`
- `cadastro.page.html`: labels "Cartão" → "Cartão de crédito", "PIX" → "Pix recorrente";
  adicionado parágrafo "Como deseja pagar?";
  submit button: `@if (!pixPending())` → `@if (!pixPending() && payMethod() !== null)`
