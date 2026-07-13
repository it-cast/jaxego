# CORRECAO-238 — Zona sem preço mínimo do time fica desativada para o entregador

## Data
2026-07-13

## Problema
Ao criar uma zona nova, se o time não configurava o preço mínimo dela
(`TeamZona`), o entregador ficava **habilitado** nela mesmo assim — recebendo
ofertas de entrega numa zona sem preço definido. Causa: em três pontos do
código, "sem registro de preço" era tratado como "ativo por padrão"
(pressuposto de compatibilidade retroativa de antes da migração pra zonas),
sem checar se o TIME configurou preço para aquela zona.

## Regra nova
Entregador só fica ativo numa zona se:
1. Tem override próprio (`CourierZona.ativo=True`, preço próprio) — vence sempre; OU
2. Não tem override, mas o TIME configurou preço mínimo (`TeamZona`) pra zona.

Sem nenhum dos dois → entregador **inelegível** nessa zona (não recebe oferta,
não aparece pra loja escolher, e a tela dele mostra a zona como inativa).

## Mudanças

### `app/dispatch/cascade.py` — `build_candidates` (motor de despacho real)
No loop de elegibilidade, quando a zona não tem preço próprio nem do time,
`continue` (pula o entregador) em vez de cair no fallback da tabela de preço
antiga (que dava preço 0/None mas mantinha elegível). **Esse era o bug
principal reportado.**

### `app/deliveries/router.py` — `POST /teams-for-address`
Mesma regra na tela da loja que lista equipes/entregadores disponíveis pra
pagamento antecipado (PIX). Sem isso, um entregador sem preço aparecia na
lista com `price_cents: null`, e o frontend (`nova-entrega.page.ts:211`)
caía em `?? 0` — a loja podia acabar vendo/pagando **R$0,00** pela corrida.
Agora esses entregadores são excluídos da lista.

### `app/couriers/router.py` — `GET /couriers/{id}/zonas`
Tela do próprio entregador (área "minhas zonas"): sem override, `ativo`
agora reflete se o time configurou preço, em vez de sempre `true`. Evita a
tela mostrar "ativo" numa zona onde ele nunca vai receber oferta de verdade.

## Validado
Testado direto contra o banco de staging, sem tocar dados reais (zona e
config temporárias, removidas ao final):
1. Zona nova, sem `TeamZona`, entregador online da equipe → `build_candidates`
   retornou `[]` (antes retornaria o entregador).
2. Mesma zona, com `TeamZona.preco_minimo_cents=1500` configurado →
   `build_candidates` retornou `[16]` (entregador elegível).

## Fora de escopo (não alterado)
`areas/service.create_zona` continua criando `CourierZona(ativo=False)` em
massa pra entregadores já existentes quando uma zona nova é criada pelo admin
da cidade — isso já bloqueava esses entregadores antes desta correção (não
era o caminho do bug). O bug afetava especificamente entregadores **sem
nenhuma linha** em `courier_zonas` (cadastrados depois da zona existir, já
que o signup não cria mais essas linhas desde a CORRECAO-229).
