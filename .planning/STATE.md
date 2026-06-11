---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
last_updated: "2026-06-11T12:00:00.000Z"
last_activity: "2026-06-11 — DEC-004: resequenciamento. Parte financeira pesada de Safe2Pay (ex-Phase 11: fatura/disputas-resolucao/saques/conciliacao) movida para POS-DEPLOY = Phase 15 (MS-06), ultima do projeto. Nova ordem de build (autopilot): 12 (API publica) -> 13 (governanca, religada a [9]) -> 14 (deploy) -> 15 (Safe2Pay back-office). Phase 10 (checkout cartao/PIX) fica live no deploy. ROADMAP/MILESTONES/DECISIONS atualizados. Proximo: Phase 12."
progress:
  total_phases: 14
  completed_phases: 10
  total_plans: 10
  completed_plans: 10
  percent: 71
---

# STATE — Current Execution State

> Documento vivo. Claude Code lê ao iniciar sessão. Atualiza ao fechar plano.
> Populado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/` (36+ arquivos).

---

```yaml
milestone: MS-04
milestone_name: Pagamentos + API publica
status: in_progress
release_target: v1.0 (piloto Pádua)
progress:
  total_phases: 14
  completed_phases: 10
  percent: 71
```

## Project Reference

See: `.planning/PROJECT.md` (ingest em 2026-06-10)

**Core value:** Malha de entregadores por área para o interior do Brasil, integrada ao Menu Certo, com pagamento direto como modalidade de 1ª classe.
**Current focus:** MS-01 (Fundação) completo. Próximo milestone: MS-02 (cadastros + área operável) — começa pela Phase 4 (cadastro de loja).

## Current Position

- **Milestone:** MS-04 (Financeiro checkout + integrações) — em andamento
- **Phase atual:** 13 of 14 — Governança — ✅ COMPLETA dev/test (autopilot). Score explicável (peso 0 no M1), avaliações, suspensão/recurso+SLA, admin plataforma cross-área auditado, shell de disputas. 25+39 testes. Pendente `pytest -m mysql` 0011.
- **Próxima Phase:** 14 of 14 — Hardening, APK, LGPD e release piloto (**deploy**) — depende de [12, 13] ✓
- **Ordem de build pós-DEC-004:** ~~12~~ → ~~13~~ → 14 (deploy) → 15 (Safe2Pay financeiro back-office, pós-deploy)
- **Last activity:** 2026-06-11 — Phase 13 fechada (autopilot): governança completa. ADR-013 isolamento provado. TD-13-01 (revenue share %), TD-13-02/03.

**Progress:** [█████████░] 86%

## MS-01 — entregue

- **Phase 1:** monorepo, FastAPI `/health` (verificado ao vivo: 200), Docker Compose (api/worker/mysql/redis), Alembic, observabilidade, CI, guard naive datetime. 2 bugs runtime pegos no smoke ao vivo e corrigidos (cryptography, arq heartbeat).
- **Phase 2:** areas/users/area_admins/refresh_tokens/audit_log, auth JWT+refresh opaco+argon2id+TOTP+lockout, RBAC 6 papéis, isolamento multi-área, trigger append-only (verificado em MySQL 8 real: errno 1644). 69 testes.
- **Phase 3:** apps/web Angular 19 + Ionic 8, design system claro+dark (DEC-001) via tokens, componentes de estado, login → /v1/auth/login, shell 3 superfícies. ng build 155KB, 25 testes, zero hardcode.

## MS-02 — em andamento

- **Phase 4:** F-01 cadastro de loja no caminho Free. Backend: merchants/merchant_users/subscription_plans/merchant_subscriptions (migration 0003), service E1–E4 (CNPJ inativo, anti-enumeração, pago→pending_payment, Receita down→pending_validation), adapters Receita/SMS/SES/geocoding (Protocol+httpx+Stub+SSRF), OTP/job aware-UTC, seed idempotente. Frontend: wizard tela 02 (stepper, forms BR, persistência sem senha, E1/E2), estado vazio + captura de interesse, plano tela 16 data-driven, banners pending_* + onboarding. 112 testes backend (not-mysql) + 33 frontend, zero hex. TD-014/TD-015 registradas. ✅ verificada ao vivo MySQL.
- **Phase 5:** F-02 cadastro/KYC do entregador. Backend: couriers/courier_documents (migration 0004, AreaScoped, unique (area_id,cpf) → E2), StoragePort (Protocol+Stub FS+B2 boto3 S3v4) com presigned PUT/GET, pipeline media (magic bytes + Pillow WebP + strip total EXIF + SHA-256 do derivado, anti-bomb), endpoints /v1/couriers/* (signup público rate-limited, presign, complete, MEI) + /v1/admin/couriers/* (view-url, PATCH review item-a-item), máquina de estados dupla (422), KYC 2 níveis RN-002, MEI mei_pending RN-024 (E3), jobs aware-UTC (expiração + escalação 48h E5). Frontend: jx-doc-upload/jx-doc-card/jx-kyc-queue-table/jx-kyc-review-row (stories + a11y), wizard Ionic tela 03 (stepper condicional 3/4, draft sem senha E1, upload presign background), painel admin tela 19 (review otimista, CPF mascarado, Score placeholder), em-análise + banner mei_pending. **179 testes backend (not-mysql) + 46 frontend, zero hex.** TD-016 (antivírus PDF) registrada. **Pendente ao vivo:** migration 0004 reversível + FK RESTRICT (`pytest -m mysql`) + integration check B2 (Gate 5, conta real).
- **Phase 6:** Área operável (F-08 + RN-003/RN-015 + REQ-016/017/018). Backend: **migration 0005** (neighborhoods_catalog com `polygon POLYGON NULL SRID 4326` via DDL MySQL-only + courier_coverage_areas + courier_pricing_tables + couriers.is_online/max_concurrent); **AreaConfig** Pydantic tipada (ranges geofence/timeouts/pisos/retorno, `extra=forbid`) substituindo JSON cru + **audit before/after** em config sensível (RN-012/F-08 E2); módulo **neighborhoods/** (CRUD area-scoped, polígono GeoJSON validado por shapely, `point_in_polygon` ST_Contains lat-first via func.ST_* sem GeoAlchemy2 — LOW-1); **cobertura** include/exclude com elegibilidade nos dois pontos (RN-003), **tabela de frete** com piso citado na rejeição (RN-015 — plataforma nunca fixa preço), **disponibilidade** online/offline só para active + busy derivado (REQ-018), rotas self-only. Frontend: **jx-data-table** primitivo governado, tela 21A config da área (máscara monetária pt-BR + confirmação sensível before→after), tela 21B catálogo de bairros (CRUD + GeoJSON + remoção bloqueada), tela 10 entregador cobertura+preços (modo bairro/km + validação de piso citando o valor), **jx-availability-toggle**. **206 testes backend (not-mysql) + 65 frontend, zero hex.** TD-017 (SPATIAL INDEX nullable) + TD-018 (piso retroativo) + SUG-008/009 registradas. **Pendente ao vivo:** migration 0005 reversível + `ST_Contains` ponto-em-polígono dentro/fora (`pytest -m mysql tests/neighborhoods/test_spatial.py`) + smoke visual das telas 21/10.

## MS-03 — em andamento

- **Phase 7:** Criação de entrega F-03 (modalidade direta) + máquina de estados (REQ-021/022/023 + REQ-011 parcial). Backend: **migration 0006** (deliveries area-scoped 7-state máquina + money em centavos inteiros + separação RN-013 endereço completo × bairro/distância + public_token ULID-like opaco; delivery_state_transitions **append-only** via trigger MySQL SIGNAL 45000; recipients só cpf_hash, sem CPF puro). **Máquina de 7 estados** (RN-019) dict-de-sets, transição inválida → 422 (testada exaustivamente — produto cartesiano); **`transition()`** único ponto de escrita de state com `SELECT ... FOR UPDATE` (lock pessimista LOW-1). **Estimativa mediana** (RN-030) compondo `is_eligible` da Phase 6 (preço efetivo por trecho bairro/km LOW-2). **Limite de plano** (RN-028) COUNT server-side excluindo CANCELADA (LOW-3); 3ª Free → 402 upgrade. Endpoints `/v1/deliveries` (POST/GET/{id}/cancel) com `merchant_scope` → IDOR 404, rate limit 30/min/loja, telefone mascarado, PII fora de log. Frontend: **jx-state-badge** (7 estados texto+ícone+cor, 7 vars --state-* derivadas de color.delivery_state claro+dark), **jx-estimate-box**, **jx-upgrade-modal** (E4 anti-dark-pattern foco preso/Esc), **jx-delivery-row** (Cancelar só CRIADA); **tela 12** form nova entrega (máscaras BR, direto único habilitado, E1/E2/E4), **tela 14** lista (jx-data-table + filtros), **tela 11** dashboard (KPIs mono + em curso + H1 italic). **242 testes backend (not-mysql) + 80 frontend, zero hex.** **Pendente ao vivo:** migration 0006 reversível + trigger append-only delivery_state_transitions (errno 1644) + concorrência FOR UPDATE (`pytest -m mysql tests/deliveries`).

- **Phase 8:** Despacho / oferta / aceite (F-05). Cascata re-enqueuável no arq (favoritos → ranking → E1 exaurido), oferta por TTL no Redis (ADR-104), aceite único via Lock + FOR UPDATE (10/10 stress: 1 vencedor, 0 penalidade). PushPort/PushMessage payload zero PII. Migration 0007 (favoritos/bloqueios). 266 backend + 104 frontend. ✅ verificada ao vivo.

- **Phase 9:** Execução, comprovação, tracking público e notificações (F-06 — a MAIOR do MS-03, 19 tasks). Backend: **pipeline de comprovação foto+EXIF/GPS (o OPOSTO do KYC)** — `extract_gps_from_raw` lê o GPS do RAW ANTES de qualquer reprocess/strip; `{lat,lng}` client é evidência principal (A3), EXIF reforço; **geofence server-side** via `ST_Distance_Sphere` parametrizado (POINT(lng,lat) SRID 4326) + haversine fallback; 3 falhas → `low_confidence` + revisão admin (CTA destrava, RN-005). **Tracking público** `# público:` por `public_token` SEM auth, 404 genérico (anti-enum), serializer **minimiza PII por estado** (endereço só pós-COLETADA RN-013, courier anônimo, telefone nunca no payload público, posição aproximada). **Ingestão de localização** anti-IDOR (ownership na query → 404; janela ACEITA/COLETADA → 409); `delivery_locations` retenção 24h. **Notificações multicanal** (push→email fallback; SMS só "a caminho" RN-018; cada tentativa em `notifications`); `push_subscriptions`; **confirmação de pagamento direto** RN-026 ("não recebi" → ENTREGUE + `payment_dispute`); **número de referência** E4 + liberação manual auditável. **Jobs arq** (FINALIZADA 24h sem disputa / purge_locations 24h LGPD / absent 10min) idempotentes aware-UTC. **Migration 0008 reversível** (5 tabelas + `cancel_cost_cents`; downgrade FK-order sem drop_index redundante — lição 0006). Frontend: **8 componentes** (jx-proof-capture wrapper de jx-doc-upload+GPS, jx-geofence-pill, jx-tracking-timeline/banner, **jx-live-map MapLibre LAZY** — import dinâmico, fora do main 162KB, LCP é a timeline, dark via filtro, jx-notice, jx-pending-upload-banner, jx-direct-payment-confirm); **tela 26** tracking público (/r/:token sem guard), **tela 07** comprovação, **tela 13** loja detalhe (cancelar declara custo RN-004, link /r/{token}); polling resiliente (Page Visibility pausa, filtro 50m, A5/TD-020) + upload offline (D-04). **326 testes backend (not-mysql) + 121 frontend, zero hex.** TD-019/TD-020 registradas. **Pendente ao vivo:** geofence ST_Distance_Sphere dentro/fora + migration 0008 reversível (`pytest -m mysql tests/proofs/test_geofence_db.py tests/db/test_migration_0008.py`).

## Atenção para MS-02+

1. **OQ-3 (contrato Safe2Pay) bloqueia a Phase 10** — resolver antes de chegar lá; Phases 4–9 podem prosseguir.
2. **OQ-1 (revenue share admin de área)** — idealmente decidir antes da Phase 10/13.
3. Valores de planos/taxas são `[ASSUMIDO]` — implementar parametrizado (seeds), nunca hardcoded.
4. **Seed de admin de plataforma** ainda não existe — necessário para smoke de login end-to-end e provavelmente para a Phase 4 (onboarding de loja).
5. Sem GitHub remote configurado — CI não validado em execução remota (item de release).

## Próximo passo

```

# Verificar Phase 7 ao vivo (MySQL real) — migration 0006 + trigger append-only + concorrência:

cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
cd apps/api && uv run pytest -m mysql tests/deliveries

# (trigger SIGNAL 45000 em delivery_state_transitions: UPDATE/DELETE → errno 1644;

#  FOR UPDATE: 2 transições simultâneas → 1 vence, 1 → 422)

# Smoke visual (telas 11/12/14) claro+dark; estimativa mediana + badge dos estados.

# Depois:

/gsd:reconcile-state 7      # reconciliação prometido vs. código
/gsd:discuss-phase 8        # Despacho / oferta / aceite
```
