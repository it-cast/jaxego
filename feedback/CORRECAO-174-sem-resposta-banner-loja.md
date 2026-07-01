# CORRECAO-174 — Banner SEM_RESPOSTA + cancelamento na página da loja

## Páginas afetadas
- `http://localhost:4200/loja/entregas/{id}`
- `/r/{token}` (tracker público — consome os mesmos componentes compartilhados)

## O que mudou

### Shared (packages/shared)
- `state-badge.component.ts` — adicionado `SEM_RESPOSTA` ao tipo `DeliveryState` e ao `META` (ícone ⏳, label "Sem resposta", reaproveita `--state-recusada` — sem token novo)
- `tracking-timeline.component.ts` — adicionado `SEM_RESPOSTA` ao tipo `TrackingState` e ao `LABELS` ("Ninguém aceitou ainda"); tratado no mesmo branch de estados desviados (`CANCELADA`/`RECUSADA_NO_DESTINO`) já que é recuperável (cascata de autoatribuição → `ACEITA`)
- `tracking-banner.component.ts` — adicionado `SEM_RESPOSTA` ao headline ("Ainda procurando — pode demorar um pouco mais")

### Web (apps/web)
- `entrega-detalhe.page.ts`:
  - Novo banner `@if (d.state === 'SEM_RESPOSTA')` (`.jx-detail__no-response`, `role="status"`) avisando que pode demorar mais e que o cancelamento está disponível a qualquer momento — sem botão de dispensar (instrução explícita do usuário: "nem tem pra que isso")
  - `canCancel()` inclui `SEM_RESPOSTA`
  - `cancelLabel()` retorna "Cancelar (sem custo)" para `SEM_RESPOSTA` (RN-004 — grátis, igual `CRIADA`/`AGENDADA`)
  - `poll()` continua fazendo polling em `SEM_RESPOSTA` (antes parava) — necessário para o banner sumir sozinho se um entregador se autoatribuir pelo pool
- `entrega-detalhe.page.scss` — adicionado `.jx-detail__no-response` (variante warning: `--warning`/`--warning-bg`, distinta do brand-wash usado em `AGENDADA`/`CRIADA`)

## Por quê
Instrução do usuário evoluiu em 3 mensagens até a forma final: banner estático, sem mecanismo de dispensar, só avisando que pode demorar e que cancelar já está disponível (botão já existia na página, só faltava habilitar para esse estado).

## Verificação
- `npx tsc -p apps/web/tsconfig.app.json --noEmit` — limpo
- `npx tsc -p apps/app/tsconfig.app.json --noEmit` — limpo (tipos compartilhados não quebraram o app do entregador)
