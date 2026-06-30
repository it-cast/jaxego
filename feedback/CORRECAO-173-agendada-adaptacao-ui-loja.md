# CORRECAO-173 — Adaptação do estado AGENDADA nas páginas da loja

## Páginas afetadas
- `http://localhost:4200/loja/entregas`
- `http://localhost:4200/loja/entregas/{id}`

## O que mudou

### Shared (packages/shared)
- `state-badge.component.ts` — adicionado `AGENDADA` ao tipo `DeliveryState` e ao `META` (ícone ⏰, label "Agendada", cor `--state-agendada`)
- `_semantic.scss` — adicionado `--state-agendada: var(--jx-delivery-aceita)` nos dois blocos (light + dark)
- `delivery.models.ts` — adicionado `scheduled_at?: string | null` ao `DeliveryListItem`

### Backend (apps/api)
- `deliveries/schemas.py` — adicionado `scheduled_at: str | None = None` ao `DeliveryListItem`
- `deliveries/router.py` — lista de entregas agora serializa `scheduled_at`

### Web (apps/web)
- `entregas-list.page.html` — opção "Agendada" adicionada ao filtro de estado
- `entrega-detalhe.page.ts`:
  - `poll()` continua fazendo polling para `AGENDADA` (aguarda transição para `CRIADA`)
  - `canCancel()` inclui `AGENDADA` (custo zero)
  - `cancelLabel()` retorna "Cancelar (sem custo)" para `AGENDADA`
  - `trackingState()` mapeia `AGENDADA → CRIADA` (sem timeline específica)
  - `fmtScheduled()` formata a data/hora em pt-BR
  - Template exibe banner "⏰ Entrega agendada para DD/MM/YYYY HH:MM" quando `state === 'AGENDADA'`
- `entrega-detalhe.page.scss` — adicionado `.jx-detail__scheduled` (banner brand-wash com borda esquerda)
