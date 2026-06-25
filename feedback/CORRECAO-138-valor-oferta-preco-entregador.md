# CORRECAO-138 — Oferta mostra o preço do entregador, não a mediana

## O que mudou

### Backend (apps/api)
- **dispatch/service.py**: O `value_cents` da oferta (`OfferOut`) antes usava `delivery.estimate_max_cents` (mediana dos preços de todos os couriers elegíveis). Agora busca o preço real do courier que está recebendo a oferta via `effective_price_cents` com as pricing rows dele. Se o courier tem preço R$ 2,00 para o bairro Centro, a oferta mostra R$ 2,00 — não a mediana de R$ 2,50.

## Arquivos alterados
- apps/api/app/dispatch/service.py
