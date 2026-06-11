---
phase: 8
phase_name: Despacho em cascata + oferta + aceite
milestone: MS-03
date: 2026-06-10
auto_generated: true
pending_review: true
---

# Retrospectiva — Phase 8: Despacho em cascata + oferta + aceite

## Dados objetivos (capturados automaticamente)
- Tasks: 12 (T-01..T-12)
- Plan revisions: 1 (gate 3 BLOCK → +visual-regression/ionic/responsive → PASS)
- Verification retries: 1 fix ao vivo (teste de corrida assertava exceção errada)
- Gates bypassados: 0
- Tech debt adicionado: TD-12-01 (Web Push VAPID vs FCM no APK)
- Skills citadas: 24 (matriz UI + gesture-touch + micro-animations + motion + push + systematic-debugging + senior-quality-bar + ionic + visual-regression + responsive)
- Commits: ~16 (e4cfec2..b0904b3)
- Testes: 265 backend not-mysql + dispatch mysql + 104 frontend
- Libs: pywebpush/py-vapid, fakeredis

## Auto-observações
- O **aceite único** (peça mais crítica do sistema — corrida de rede) foi implementado em 3 camadas (autorização → Redis Lock → FOR UPDATE → transição idempotente) e verificado com 10/10 runs de stress: nunca houve dupla-aceitação. A produção estava correta.
- A verificação ao vivo de novo provou valor: o teste de corrida era estrito demais (assertava 409 específico), mascarando que a invariante real (1 vencedor, 0 penalidade) sempre vale. Lição: testar a INVARIANTE, não o tipo de exceção, em cenários de concorrência com timing variável.
- Reuso forte das Phases 6/7 (is_eligible, transition+FOR UPDATE, AreaConfig timeouts, adapter pattern) — researcher mapeou bem.
- Bug naive-vs-aware recorrente (TD-010) apareceu de novo no KPI; pego por teste.
- Migration 0007 reversível de primeira (executor aplicou a lição da 0006).

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem?
[AUTO: preencher depois] — Hipótese: aceite único robusto; reuso das phases anteriores; stress test deu confiança.

### 2. O que atrapalhou?
[AUTO: preencher depois] — Hipótese: teste de concorrência estrito demais; naive datetime recorrente.

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois] — Considerar: helper de teste de invariante de concorrência; OSRM/push reais; rodar @mysql no dev loop.

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]
