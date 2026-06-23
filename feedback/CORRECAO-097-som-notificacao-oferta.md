# Correção 097 — Som de notificação ao receber nova oferta

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/public/notificacao.mp3` (criado)
- `apps/app/src/features/entregador/inicio.page.ts`

## Problema

Quando uma nova oferta chegava pelo polling, não havia feedback sonoro — o entregador podia não perceber.

## Correção

- Arquivo `notificacao.mp3` copiado para `apps/app/public/`
- No `pollOffer()`, ao detectar uma oferta nova (offer não era null e antes era null), toca o som via `Audio.play()`
- `.catch(() => {})` para não quebrar se o browser bloquear autoplay (ex: primeira interação pendente)
