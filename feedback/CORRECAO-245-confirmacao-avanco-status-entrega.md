# CORRECAO-245 — Confirmação antes de avançar status da entrega

## Data
2026-07-13

## Pedido
A cada avanço de status pelo entregador (coletar, chegar ao destino,
finalizar), exibir um modal "Deseja realmente...?" antes de executar a ação.

## Novo componente compartilhado
`packages/shared/src/shared/components/confirm-dialog/` —
`ConfirmDialogComponent` (`jx-confirm-dialog`): bottom-sheet genérico de
confirmação (título, mensagem, botão confirmar customizável, cancelar),
mesmo idioma visual do modal de contato já existente em `entrega-ativa`
(slide-up de baixo, mobile-first). Acessível: `role="alertdialog"`,
foco vai pro título ao abrir, Esc cancela. Registrado no barrel
`shared/components/index.ts`.

## Onde foi aplicado
Escopo: as ações de avanço de status explícitas por **botão** na tela
principal do entregador e na tela de comprovação. Não intercepta o fluxo de
"tirar foto → envia automaticamente" (coleta/recusa com foto) — ali a própria
captura da foto já é o gesto de confirmação, inserir um modal depois quebraria
o padrão "aponta e tira" que esses fluxos já usam.

- `entrega-ativa/entrega-ativa.page.ts`:
  - "Já coletei" → `askCollect()` → "Deseja realmente coletar a entrega?"
  - "Cheguei no destino" → `askAdvance()` → "Deseja realmente confirmar a chegada?"
  - "Destinatário ausente / recusou" → `askRefusal()` → "Deseja realmente
    reportar ausência/recusa?"
  - Os métodos originais (`collect`, `advance`, `refusal`) viraram `private`,
    só executados via `confirmPending()` depois do usuário confirmar no modal.
- `comprovacao/comprovacao.page.ts`:
  - "Finalizar entrega" → `askFinalize()` → "Deseja realmente finalizar a
    entrega?" → confirma → `finalize()`.

## Não alterado (fora de escopo)
- Aceitar/recusar oferta (tela separada, com timer — confirmação extra
  atrapalharia a urgência do fluxo).
- Captura de foto de coleta/recusa (`onCaptured` → `submitAndNavigate`
  automático) — a foto em si já é o "confirmar".
- `validateReference()` (só valida um número, não avança estado).

## Validado
Build do app (`ng build`) verde nas duas rodadas de edição (entrega-ativa e
comprovacao).
