# CORRECAO-213 — Entrega detalhe: card com dados do entregador

**Data:** 2026-07-08

## O que foi implementado

Na tela `/loja/entregas/{id}`, quando a entrega já foi aceita por um entregador
(`courier_id` presente), um novo card "Entregador" passa a aparecer **ao lado**
do card "Itens e observações" (lado a lado em telas largas, empilhado em
telas estreitas — mesma estratégia responsiva do grid existente).

### Dados exibidos no card
- Nome
- Telefone (formatado, mesmo padrão do telefone do destinatário)
- Veículo (Moto/Bicicleta/Carro/A pé) + placa, quando houver
- Avaliação média (⭐ + nº de avaliações), ou "Ainda sem avaliações"
- Total de entregas concluídas pelo entregador na plataforma
- Valor da corrida (mesmo `price_cents` já usado no card Destinatário)
- Data de entrada do entregador na plataforma ("Na plataforma desde")

A linha duplicada "Entregador: {{ nome }}" que existia dentro do card
Destinatário foi removida — agora o nome do entregador só aparece no novo
card dedicado, evitando repetição.

## Decisão de dados/privacidade

O telefone do entregador é exposto **completo** (não mascarado) para a loja,
no mesmo nível de confiança já usado para `recipient_phone` (o destinatário) —
a loja tem necessidade legítima de ligar para o entregador que está com a
encomenda dela. Isso só é populado no `GET /{id}` (detalhe), nunca na listagem
(`GET /deliveries`), seguindo o padrão já existente para os demais campos
"completos" (endereço, telefone do destinatário etc.).

## Arquivos alterados

### Backend
- `apps/api/app/deliveries/schemas.py` — `DeliveryOut` ganha `courier_phone`,
  `courier_vehicle_type`, `courier_vehicle_plate`, `courier_rating`,
  `courier_rating_count`, `courier_total_deliveries`, `courier_since`
- `apps/api/app/deliveries/router.py` — `_delivery_out()` e `get_delivery()`
  passam a buscar o `Courier` completo (telefone, veículo, `created_at`),
  calcular a média/contagem de `CourierRating` e contar entregas `FINALIZADA`
  do entregador (queries agregadas, sem N+1 por entrega)

### Frontend
- `packages/shared/src/shared/models/delivery.models.ts` — `DeliveryListItem`
  ganha os mesmos campos `courier_*` opcionais (só populados no GET /{id})
- `apps/web/src/features/loja/entrega-detalhe/entrega-detalhe.page.ts`
  - novo wrapper `.jx-detail__row` (grid `auto-fit`) colocando o card
    "Itens e observações" e o novo card "Entregador" lado a lado
  - métodos `vehicleLabel()` e `fmtDate()`
  - removida a linha "Entregador" duplicada do card Destinatário

## Observação (não corrigida nesta sessão)

`apps/api/tests/conftest.py` importa `CourierScoreSnapshot` de
`app.scores.models`, mas esse módulo foi esvaziado (comentário: "tables
dropped in migration 0018 — kept as empty module"). Isso já quebra a suíte
de testes inteira (`pytest` não coleta nada) **mesmo na branch `master` sem
nenhuma mudança minha** — confirmado com `git stash` antes de mexer em
qualquer coisa. Não fiz build de mocks/mudanças para contornar isso porque é
tech debt pré-existente e fora do escopo desta correção; só não foi possível
rodar a suíte de testes real para validar o `get_delivery` end-to-end. A
validação foi feita via `ng build loja` (sem erros de template) e leitura
manual das queries.
