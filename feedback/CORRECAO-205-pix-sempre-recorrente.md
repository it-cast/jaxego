---
classe: fix
data: 2026-07-06
arquivos_afetados:
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - apps/web/src/features/loja/plano/plano.page.ts
  - apps/web/src/features/loja/plano/plano.page.scss
---

## Problema

PIX é sempre recorrente (PIX Automático BACEN). Não existe PIX avulso no produto.
A implementação anterior adicionou um toggle "Ativar débito automático" que não faz sentido,
e o cadastro enviava `pix_recorrente: false` (ausente = default false), fazendo o backend
usar o caminho errado (`_create_pix_qr` em vez de `_create_pix_automatic`).

## Correções

### cadastro.page.ts
- Adicionado `pix_recorrente: true` na chamada `merchants.subscribe()` do fluxo PIX

### plano.page.ts
- Removido signal `pixRecorrente` e todo o toggle de UI
- `onPixSubmit` sempre envia `pix_recorrente: true`
- Template PIX simplificado: só mostra o QR/instrução de aprovação (estado CRIADA)
  ou o botão "Autorizar PIX Recorrente"
- Removidas referências a `pixRecorrente` em `closePaymentModal` e `onMethodChange`

### plano.page.scss
- Removida classe `.jx-plano__pix-toggle` (toggle inexistente)
