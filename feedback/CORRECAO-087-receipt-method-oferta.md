# Correção 087 — Forma de recebimento exibida na oferta do entregador

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/dispatch/schemas.py` — campo `receipt_method` adicionado ao `OfferOut`
- `apps/api/app/dispatch/service.py` — `build_offer_view` popula `receipt_method` da delivery

### Frontend (App entregador)

- `apps/app/src/features/entregador/oferta/offer.models.ts` — campo `receipt_method` na interface `OfferOut`
- `apps/app/src/features/entregador/oferta/offer-sheet.component.ts` — badge dinâmico: 💵 DINHEIRO / 💳 MAQUINA DA LOJA / 📱 APLICATIVO (fallback: PAGAMENTO DIRETO)

## Problema

Na tela de oferta do entregador, o badge de pagamento era hardcoded "PAGAMENTO DIRETO 💵", sem refletir a forma de recebimento escolhida pela loja no cadastro da entrega.

## Correção

- `receipt_method` agora flui da delivery → oferta → app
- Badge exibe a forma de recebimento real definida pela loja
