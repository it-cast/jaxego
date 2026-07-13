# CORRECAO-240 — Loading "Cadastrando entregador na plataforma..." na aprovação final do KYC

## Data
2026-07-13

## Contexto
Ao aprovar o último documento pendente na tela `/equipe/entregadores/{id}`, o
backend ativa o entregador e chama a Safe2Pay pra criar a subconta
(`/v2/marketplace/add`) de forma síncrona dentro do próprio request — pode
levar alguns segundos. Sem feedback visual, parecia travado.

## Mudança
`apps/web/src/features/equipe/kyc-detalhe.page.ts`:
- Novo signal `registeringOnPlatform`.
- `willActivateCourier(item)`: detecta se a aprovação em curso é a ÚLTIMA
  pendente (todos os outros documentos já `approved`) — só nesse caso ativa
  o overlay, evitando mostrar loading pesado em aprovações intermediárias
  (que são instantâneas).
- `onDecide`: liga/desliga `registeringOnPlatform` ao redor da chamada
  `svc.approve(...)`.

`kyc-detalhe.page.html` (inline no .ts) + `.scss`: overlay de tela cheia com
spinner + texto "Cadastrando entregador na plataforma…", mesmo padrão visual
usado no wizard de cadastro do app (CORRECAO-236).

## Validado
Build do web (`ng build web`) verde, sem erros de template/tipo.
