---
phase: 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2
plan: all (T-01..T-12, executor único sequencial)
subsystem: couriers + media + storage (B2) + frontend wizard/admin KYC
tags: [kyc, upload, b2, presigned, state-machine, mei, aware-utc, ionic, admin]
requires:
  - Phase 4 (adapter Protocol+Stub, SSRF guard, máscaras PII, máquina de estados, OTP, Receita, AreaScoped, audit_log)
  - Phase 3 (design system, 4 estados, jx-wizard-stepper, jx-field)
provides:
  - entidades couriers + courier_documents (migration 0004)
  - StoragePort (Protocol) + StorageStubAdapter + StorageB2Adapter (presigned)
  - pipeline media (magic bytes + Pillow WebP + strip EXIF + SHA-256)
  - endpoints /v1/couriers/* + /v1/admin/couriers/*
  - jobs document_reprocess + document_expiry + escalate_stale_reviews (aware-UTC)
  - componentes jx-doc-upload, jx-doc-card, jx-kyc-queue-table, jx-kyc-review-row
  - telas 03 (wizard entregador) e 19 (admin KYC) + estados pending_kyc/mei_pending
affects: [api/v1/router, workers/settings, integrations/factory, core/config, app.routes]
tech-stack:
  added: [boto3==1.43.27, Pillow==12.2.0]
  patterns: [presigned-put-direct, server-reprocess-authority, item-a-item-kyc, kyc-2-niveis]
key-files:
  created:
    - apps/api/app/couriers/{models,schemas,service,documents,state_machine,kyc,view,constants,router}.py
    - apps/api/app/media/{validation,reprocess}.py
    - apps/api/app/integrations/{storage,storage_stub}.py
    - apps/api/alembic/versions/0004_couriers_kyc.py
    - apps/api/app/workers/{document_reprocess,document_expiry}.py
    - apps/web/src/shared/components/{doc-upload,doc-card}/*
    - apps/web/src/features/admin/kyc/* (queue-table, review-row, kyc-detalhe, kyc.service)
    - apps/web/src/features/entregador/cadastro/* (page, service, models, em-analise)
  modified:
    - apps/api/app/core/config.py (B2 settings)
    - apps/api/app/integrations/{base,factory}.py (StoragePort + get_storage_adapter)
    - apps/api/app/api/v1/router.py, app/workers/settings.py
    - apps/web/src/app/app.routes.ts, features/entregador/inicio.page.ts
decisions:
  - boto3 S3v4 (addressing_style=path) num único StoragePort, não b2sdk (reuso Phase 9)
  - presigned PUT (limite de tamanho no pós-upload), não presigned POST — simplicidade no piloto
  - antecedentes restrito a IMAGEM no M1 (PDF deferido → TD-016)
  - MEI não é documento bloqueante: inativo → mei_pending, courier ainda ativa
metrics:
  duration: ~3h
  tasks: 11 (T-01..T-12, T-08 incluso)
  backend_tests: 179 passed (not mysql) + 1 @mysql
  frontend_tests: 46 passed
  completed: 2026-06-10
---

# Phase 5 Plan (all): Cadastro do entregador + KYC 2 níveis + documentos B2 — Summary

Fluxo F-02 completo entregue end-to-end: backend (`couriers`/`courier_documents`,
upload KYC para B2 privado via presigned PUT com reprocessamento server-side
obrigatório — magic bytes + Pillow WebP + strip total de EXIF + SHA-256 do
derivado), KYC 2 níveis com aprovação **item-a-item** do admin de área, MEI via
adapter Receita com flag `mei_pending`, jobs de expiração e escalação 48h
aware-UTC; e o frontend (wizard mobile Ionic tela 03 + painel admin tela 19 +
estados especiais). Reuso máximo dos padrões da Phase 4 (adapter Protocol+Stub,
SSRF guard, máscaras PII, máquina de estados, AreaScoped, audit_log) e Phase 3
(design system, 4 estados, jx-wizard-stepper, jx-field).

## O que foi entregue (por critério de sucesso do PLAN)

- **Bucket KYC inacessível sem URL assinada** — `test_no_public_access` verde
  (Stub: sem caminho de leitura anônimo; presign é string fake, fetch de key não
  escrita levanta). ✅
- **F-02 E1** — draft server-side (courier pending_kyc + documentos enviados
  sobrevivem à retomada) testado. ✅
- **F-02 E2** — CPF na MESMA área bloqueia (unique `(area_id, cpf)` + mensagem
  única anti-enumeração + dummy hash); CPF em OUTRA área permite (novo vínculo). ✅
- **F-02 E3** — MEI inativo/CNAE incompatível/provider-down → `mei_pending=True`. ✅
- **F-02 E4** — reprovar a CNH **não invalida** a selfie aprovada (status
  independente por item; reprovado volta a pending_upload). ✅
- **F-02 E5** — escalação 48h: `pending` há ≥48h → `kyc.escalated_48h` auditado
  (clock fake). ✅
- **Upload seguro** — magic bytes (extensão falsa rejeitada), EXIF zerado
  (`getexif()` vazio no derivado), SHA-256 do derivado, decompression-bomb
  rejeitada. ✅
- **Transições inválidas** courier/documento → 422. ✅
- **IDOR** cross-área no documento → 404 (ownership+área no WHERE). ✅
- **4 componentes** governados com story baseline + specs (a11y/E4/E5). ✅
- **Telas 03 e 19** wiradas (exceto etapa 5/bairros → Phase 6 e Score → Phase 13). ✅

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] conftest.couriers importava storage_stub antes do T-04**
- **Found during:** T-02
- **Issue:** o fixture `storage_stub` no conftest importava um módulo ainda não
  criado (ordem sequencial), quebrando a coleta dos testes de models.
- **Fix:** import lazy dentro do fixture (só carrega quando um teste usa storage).
- **Files:** `apps/api/tests/couriers/conftest.py`
- **Commit:** `0bc8619`

**2. [Rule 1 - Bug] inferência de tipo em `kyc.required_documents`**
- **Found during:** T-05 (basedpyright)
- **Issue:** `list(COMPLETA_REQUIRED)` inferia tipo literal estreito, recusando
  `.append("antecedentes")`.
- **Fix:** anotação explícita `docs: list[str]`.
- **Commit:** `2539b3a`

**3. [Rule 1 - Lint] getter de literal vira readonly field (jx-doc-upload)**
- **Found during:** T-10 (ng lint — `class-literal-property-style`)
- **Issue:** `get idleHint()` retornando string literal.
- **Fix:** `readonly idleHint = '…'`.
- **Commit:** `83810ca`

Nenhum desvio arquitetural (Rule 4). Nenhuma auth gate.

## Decisões de implementação

- **StoragePort único (boto3 S3v4):** Stub FS em dev/test, B2 em prod. `fetch`
  interno passa por `assert_safe_url` + `follow_redirects=False` (TH-04). Segredo
  B2 só de `settings` (Gate 8).
- **Server é autoridade do byte:** `complete` baixa o cru, valida magic bytes,
  reprocessa (resize ≤1920 + WebP sem `exif=` → strip total), confirma SHA-256 do
  derivado, regrava; nunca serve o cru.
- **KYC item-a-item:** cada documento aprova/reprova independente; courier ativa
  só quando todos os required do nível aprovados (RN-002). MEI nunca bloqueia.
- **aware-UTC (TD-010)** em expiração, escalação e `submitted_at` (clock do E5).

## Known Stubs

- **StorageB2Adapter (impl real B2):** validado só por contrato (Stub) em CI. A
  validação contra a conta `jaxego-kyc-prod` real é o **integration check (Gate
  5)** antes de `/gsd:verify-work` (LOW-1 do RESEARCH). Não é stub de UI — é o
  adapter real cuja conexão de rede não roda em CI por design.
- **Áreas no wizard (frontend):** o `<select>` de cidade usa lista mínima
  (Pádua/Itaocara) inline; o endpoint de listagem de áreas ativas será consumido
  quando disponível. Não impede o fluxo (area_id é enviado ao backend, que valida).
- **Painel admin tela 19:** o set de itens de revisão é representativo (a fila
  `jx-kyc-queue-table` e a revisão consomem `AdminKycService`); o hook de
  listagem ao vivo é swap fino quando o endpoint de listagem de couriers/docs
  pendentes existir (fora do escopo dos contratos desta phase).

## Threat Flags

Nenhuma superfície de segurança nova fora do `<threat_model>` do PLAN (TH-01..TH-12
cobertos: bucket privado, magic bytes + re-encode + strip EXIF, ownership no WHERE
→ 404, máscaras PII, SSRF guard, SHA-256, rate limit signup, segredo B2 só env).

## A verificar ao vivo (MySQL 8 + conta B2)

- Migration 0004 reversível: `uv run alembic upgrade head && downgrade -1 && upgrade head`.
- `cd apps/api && uv run pytest -m mysql` (FK RESTRICT em `couriers`).
- Integration check Gate 5: presign PUT/GET reais contra `jaxego-kyc-prod`.
- Fluxo KYC manual: signup → upload selfie → admin aprova item-a-item → courier active.

## Self-Check: PASSED

Arquivos-chave criados (9/9 FOUND) e commits (9/9 FOUND) verificados. Backend
179 passed (not mysql) + ruff/pyright limpos; frontend build OK + lint limpo +
46 passed + zero hex hardcoded.
