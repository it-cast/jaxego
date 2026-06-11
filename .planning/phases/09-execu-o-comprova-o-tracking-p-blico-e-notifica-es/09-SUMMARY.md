---
phase: 09-execu-o-comprova-o-tracking-p-blico-e-notifica-es
plan: PLAN
subsystem: api
tags: [exif-gps, geofence, st_distance_sphere, tracking, maplibre, web-push, sms, arq-cron, lgpd, alembic]

requires:
  - phase: 05-cadastro-kyc-entregador
    provides: StoragePort (B2 presign/fetch/put + reprocess WebP strip EXIF), media/validation magic bytes
  - phase: 06-area-operavel
    provides: AreaConfig.geofence_m (typed), ST_Contains spatial precedent
  - phase: 07-criacao-de-entrega
    provides: transition() FOR UPDATE append-only, máquina 7 estados, deliveries.pickup/dropoff lat-lng, public_token ULID
  - phase: 08-despacho-oferta-aceite
    provides: PushPort/PushMessage, arq worker, courier_scope
  - phase: 04-cadastro-loja
    provides: SmsPort/EmailPort adapters + stubs, OTP/job aware-UTC
provides:
  - Pipeline de comprovação foto+EXIF/GPS antifraude server-side (oposto do KYC — lê GPS antes de strippar)
  - Geofence server-side via ST_Distance_Sphere (+ haversine fallback)
  - Endpoint público de tracking sem auth com serializer de minimização de PII por estado
  - Ingestão de localização anti-IDOR + delivery_locations (retenção 24h)
  - Notificações multicanal (push/SMS/email) com fallback; push_subscriptions
  - Confirmação de pagamento direto + registro de disputa (RN-026)
  - Número de referência (E4) + liberação manual auditável
  - Jobs arq de ciclo (FINALIZADA 24h / purge 24h / absent 10min)
  - Migration 0008 reversível (5 tabelas + cancel_cost_cents)
  - 8 componentes UI (proof-capture, geofence-pill, tracking-timeline/banner, live-map lazy, notice, pending-upload, direct-payment-confirm) + telas 07/13/26
affects: [Phase 10 (pagamento online), Phase 11 (fatura + mediação de disputa), Phase 13 (score), Phase 14 (direitos do titular sobre delivery_locations/proofs)]

tech-stack:
  added: [maplibre-gl@^5.24.0 (lazy chunk), piexif (dev-only, gera JPEG com GPS nos testes)]
  patterns:
    - "Pipeline EXIF-antes-de-strip: extract_gps_from_raw ANTES de reprocess_to_webp (oposto do KYC)"
    - "Geofence server-side parametrizado POINT(lng,lat) SRID 4326 + haversine fallback documentado"
    - "Serializer de minimização de PII por estado (endereço só pós-COLETADA, courier anônimo)"
    - "Cron arq idempotente que loga count+duração; aware-UTC em todos os timestamps"
    - "Componente de mapa via import dinâmico (IntersectionObserver) — fora do bundle crítico"

key-files:
  created:
    - apps/api/app/proofs/{exif,geofence,service,models,schemas,router,reference}.py
    - apps/api/app/tracking/{public,locations,serializer,models}.py
    - apps/api/app/notifications/{dispatcher,models,router,tasks}.py
    - apps/api/app/payments_direct/{service,models,router}.py
    - apps/api/app/workers/lifecycle.py
    - apps/api/alembic/versions/0008_proofs_tracking_notifications.py
    - apps/web/src/shared/components/{geofence-pill,notice,tracking-timeline,tracking-banner,proof-capture,direct-payment-confirm,pending-upload-banner,live-map}/
    - apps/web/src/features/public-tracking/, apps/web/src/features/entregador/{comprovacao,entrega-ativa}/, apps/web/src/features/loja/entrega-detalhe/
  modified:
    - apps/api/app/deliveries/{service,models}.py (cancellation cost + reveal + cancel_cost_cents)
    - apps/api/app/workers/settings.py (notify_task + cron_jobs)
    - apps/api/app/api/v1/router.py (5 routers Phase 9)
    - apps/web/src/app/app.routes.ts (/r/:token público + comprovar + detalhe)

key-decisions:
  - "GPS {lat,lng} explícito do cliente é evidência PRINCIPAL (A3); EXIF do RAW é reforço; geofence server-side é a única autoridade"
  - "3 falhas de geofence → low_confidence + revisão admin: a transição prossegue (CTA destrava, não trava para sempre)"
  - "Migration 0008 agregada e reversível: downgrade FK-order children->parents SEM drop_index redundante (lição 0006)"
  - "Tracking público minimiza PII por estado: endereço só pós-COLETADA (RN-013), courier anônimo (só vehicle_type), telefone nunca no payload público"
  - "MapLibre lazy via import dinâmico: LCP é a timeline (texto), mapa fora do main (231KB transfer separado)"

patterns-established:
  - "EXIF-antes-de-strip provado por teste de ordem (test_pipeline_order)"
  - "Janela de telefones RN-022 como predicado testável por estado (phone_window_open)"
  - "Ingestão de localização: ownership na query -> 404 não 403; janela ACEITA/COLETADA -> 409"
  - "Jobs de retenção LGPD hard-delete por recorded_at indexado"

requirements-completed: [REQ-026, REQ-027, REQ-028, REQ-029, REQ-030, REQ-031, REQ-032, REQ-035, REQ-049, REQ-055]

duration: 95min
completed: 2026-06-11
---

# Phase 9 Plan: Execução, comprovação, tracking público e notificações Summary

**Fechou o ciclo operacional da entrega (ACEITA→FINALIZADA) com comprovação foto+EXIF/GPS antifraude server-side (lendo o GPS do RAW ANTES de strippar — o oposto do KYC), tracking público sem login com mapa MapLibre lazy, notificações multicanal com fallback push→email/SMS, e jobs de ciclo idempotentes — 326 testes backend + 121 frontend verdes, migration 0008 reversível.**

## What was built

19 tasks em 7 waves, executor único sequencial. Backend: `proofs/` (pipeline foto+GPS com ordem obrigatória fetch→magic→EXIF→geofence→strip→transition; geofence via `ST_Distance_Sphere` parametrizado com fallback haversine; número de referência E4 com liberação manual), `tracking/` (endpoint público `# público:` por `public_token` com serializer que minimiza PII por estado; ingestão de localização anti-IDOR com janela ACEITA/COLETADA e retenção 24h), `notifications/` (dispatcher 3 momentos com fallback, SMS só "a caminho", push_subscriptions, payload push zero PII), `payments_direct/` (confirmação RN-026; "não recebi" → ENTREGUE + PaymentDispute), `workers/lifecycle.py` (3 cron idempotentes). Migration 0008 reversível agregando 5 tabelas + `cancel_cost_cents`. Frontend: 8 componentes governados (zero hex), tela 26 (tracking público com mapa lazy), tela 07 (comprovação), tela 13 (loja detalhe), serviços de polling resiliente e upload offline, opt-in de push contextual.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Estrutura real do frontend difere do PLAN**
- **Found during:** T-11/T-12
- **Issue:** PLAN listava `apps/web/src/app/...`; a estrutura real é `apps/web/src/{features,shared,core}`
- **Fix:** componentes em `shared/components/`, telas em `features/`, rotas em `app/app.routes.ts`
- **Files:** todos os componentes/telas do frontend

**2. [Rule 2 - Missing functionality] Coluna `cancel_cost_cents`**
- **Found during:** T-04
- **Issue:** RN-004 exige registrar o custo de cancelamento na entrega; não havia coluna
- **Fix:** adicionada `deliveries.cancel_cost_cents` (na migration 0008) + cálculo por estado
- **Commit:** `f9cad54` / `16a3e7b`

**3. [Rule 3 - Blocking] piexif como dev-dependency**
- **Found during:** T-03
- **Issue:** testes precisam gerar JPEG com EXIF GPS; produção lê EXIF com Pillow (já dep)
- **Fix:** `piexif` em `[dependency-groups].dev` (test-only)
- **Commit:** `111815f`

**4. [Rule 1 - Bug] FastAPI 204 + corpo de resposta**
- **Found during:** T-06/T-09
- **Issue:** endpoints 204 (locations, push DELETE) com response_model implícito quebravam o app ("204 must not have a response body")
- **Fix:** retornar `Response(status_code=204)` explícito
- **Commits:** `8276780`, `ce0c51c`

**5. [Rule 3 - Blocking] `attributionControl: true` (typing MapLibre v5)**
- **Found during:** T-16
- **Fix:** removido (atribuição é default; boolean não aceito pelo tipo)
- **Commit:** `61fd8d0`

## Authentication gates

Nenhum gate de autenticação durante a execução (B2/SMS/SES/push reusam segredos das fases anteriores; dev/test usam stubs sem rede).

## Items para verificação ao vivo (MySQL real)

```
cd apps/api
uv run pytest -m mysql tests/proofs/test_geofence_db.py      # ST_Distance_Sphere dentro/fora + SRID/eixo/unidade
uv run pytest -m mysql tests/db/test_migration_0008.py        # 0008 upgrade->downgrade->upgrade reversível
```

Verificação manual ao vivo recomendada (humano): geofence `ST_Distance_Sphere` com par conhecido; tracking público sem PII proibida no payload por estado; janela de telefones RN-022 por estado.

## Known Stubs

Nenhum stub que impeça o objetivo da phase. ETA (`eta_seconds`) é `None` no serializer público por ora (derivação de rota é concern de UI/Phase futura — degrada para omitir, não é placeholder de dado de entrega). `absent_timeout` usa marcador em `notes` (não coluna dedicada) — decisão consciente M1, automação fina é TD-007 (pós-M1).

## Self-Check: PASSED

- 10/10 arquivos-chave verificados no disco (proofs/tracking/notifications/payments_direct/workers/migration/frontend).
- 15/15 commits de task verificados no git log.
