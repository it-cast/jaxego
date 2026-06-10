---
phase: 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2
title: Cadastro do entregador + KYC 2 níveis + documentos B2
generated_by: gsd-planner
generated_at: 2026-06-10
status: draft
plans: 5
waves: 3
parallel_hint: back-front  # Plan 01 (back) e Plan 03 (front) rodam em paralelo (Wave 1)
requirements: [REQ-013, REQ-014, REQ-015, REQ-019]
integration_check: true   # B2 (presigned PUT/GET), Receita (MEI), SMS — validados por stub (Gate 5)
has_ui: true
has_pii: true
files_modified:
  - apps/api/pyproject.toml
  - apps/api/app/core/config.py
  - apps/api/.env.example
  - apps/api/migrations/versions/0004_couriers_kyc.py
  - apps/api/app/couriers/
  - apps/api/app/integrations/base.py
  - apps/api/app/integrations/storage.py
  - apps/api/app/integrations/storage_stub.py
  - apps/api/app/integrations/factory.py
  - apps/api/app/media/
  - apps/api/app/workers/document_expiry.py
  - apps/api/app/workers/settings.py
  - apps/api/tests/couriers/
  - apps/api/tests/media/
  - apps/api/tests/integrations/test_storage_stub.py
  - apps/web/src/shared/components/doc-upload/
  - apps/web/src/shared/components/doc-card/
  - apps/web/src/features/admin/kyc/
  - apps/web/src/features/entregador/cadastro/
---

# PLAN — Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Entregar o fluxo F-02: backend de cadastro de entregador (`couriers`/`courier_documents`), upload de documentos KYC para Backblaze B2 **privado** via presigned URL com reprocessamento server-side obrigatório (magic bytes + Pillow WebP + strip EXIF + SHA-256), KYC 2 níveis com aprovação **item-a-item** do admin de área, MEI via adapter Receita com flag `mei_pending`, jobs de expiração e escalação 48h aware-UTC; e o frontend (wizard mobile Ionic do entregador — tela 03 — e painel admin — tela 19) consumindo esses contratos. **Reuso máximo** dos padrões da Phase 4 (adapter Protocol+Stub, SSRF guard, máscaras PII, máquina de estados, OTP aware-UTC, AreaScoped, audit_log).

**Fora de escopo (deferido):** cobertura/bairros e tabela de frete (etapa 7 do F-02 → Phase 6); online/offline/ofertas (Phase 8); bloqueio de repasse por MEI RN-010 + saques (Phase 10/11); score (Phase 13); recurso de suspensão (Phase 13).

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] **Bucket KYC inacessível sem URL assinada** — `pytest tests/couriers/test_documents.py::test_no_public_access` verde contra o Stub (nenhum acesso direto sem presign).
- [ ] **F-02 E1** — retomada de wizard por 30 dias (draft server-side) testada.
- [ ] **F-02 E2** — CPF na MESMA área bloqueia (anti-enumeração, mensagem única); CPF em OUTRA área permite (novo vínculo).
- [ ] **F-02 E3** — MEI inativo/CNAE incompatível → `mei_pending=True`; só pagamento direto.
- [ ] **F-02 E4** — reenvio item-a-item: reprovar a CNH **não invalida** a selfie já aprovada (status independente por item).
- [ ] **F-02 E5** — escalação 48h: documento `pending` há ≥48h sobe na fila + sinaliza admin plataforma (job com clock fake).
- [ ] **Upload seguro** — valida **magic bytes** (não extensão/content-type declarado), **strip EXIF total**, confirma **SHA-256 do derivado** (`pytest tests/media/test_reprocess.py`).
- [ ] **Transições inválidas** courier/documento → 422 (`pytest tests/couriers/test_state_machine.py`).
- [ ] **IDOR** cross-área no documento → 404 (`pytest tests/couriers/test_authz.py`).
- [ ] **Wireframe-contract** de `03-cadastro-entregador.html` e `19-admin-area-entregador-detalhe.html` coberto (exceto etapa 5/bairros e bloco Score, deferidos).
- [ ] `jx-doc-upload`/`jx-doc-card`/`jx-kyc-review-row`/`jx-kyc-queue-table` com story + baseline visual claro+dark (visual-regression §10 UI-SPEC).
- [ ] `axe-core` sem violações críticas no wizard (tela 03) e no painel admin (tela 19).
- [ ] Todos os testes relacionados passam (`cd apps/api && uv run pytest && uv run ruff check .`; web: `pnpm test` + axe).
- [ ] Commits atômicos com mensagem padronizada.

## REQs referenciados

- **REQ-013** — wizard F-02 (etapas 1-6 + retomada 30d).
- **REQ-014** — validação simples/completa, aprovação item-a-item.
- **REQ-015** — documentos em B2 privado (presigned, hash, compressão).
- **REQ-019 (parcial)** — flag `mei_pending` (RN-024); subconta completa fica para Phase 10.

---

## Skills Consultadas

Cada skill teve regras aplicadas a tasks concretas. Citar sem aplicação é inválido (plan-checker flaga).

- `meta/orchestration-decision-tree` — T-01/T-04/T-09: decisão de orquestração — backend (Plan 01/02) e frontend (Plan 03/04/05) paralelizáveis em waves; spike de B2 isolado como task antes do integration check (Gate 5).
- `quality/observability-production` — T-05/T-06/T-08: todo endpoint loga `request_id`/`status_code`/`duration_ms`; eventos KYC (`kyc.document_viewed`, `kyc.item_approved`, `kyc.item_rejected`, `courier.submitted`) auditados em `audit_log`; **zero PII** (CPF/documento/telefone/email/key/presigned nunca em log).
- `domain/mysql-schema-design` — T-02: migration `0004_couriers_kyc.py` reusa convenções (`AreaScopedMixin`, `UTC_DATETIME` DATETIME(6), `BIG_ID`, FK RESTRICT, índices); `couriers` AreaScoped; `courier_documents` com `storage_key`/`sha256`/`status`/`expires_at`/`anonymized_at` nullable (RN-021).
- `domain/fastapi-production-patterns` — T-05/T-06: routers `/v1/couriers`, Pydantic v2 `extra="forbid"`, enums estreitos, RFC-7807, idempotência; signup público rate-limited (reuso `signup_rate_limit`), etapas autenticadas.
- `product/api-design-contracts` — T-05/T-06: contratos versionados `/v1`, payload de presign `{kind, sha256_client, content_type}` → `{presigned_url, expires_in, headers}`; PATCH item `{approve|reject + motivo}`; documentado para o frontend (Plans 03-05) e integration check.
- `owasp-security` (upload, data-protection, SSRF) — T-03/T-04/T-05/T-06: magic bytes + re-encode Pillow + strip EXIF + `MAX_IMAGE_PIXELS`; bucket privado + presigned curto; ownership+área no WHERE → 404; `assert_safe_url` (allowlist B2, `follow_redirects=False`) no download interno; key server-side (path traversal); SHA-256 com `compare_digest`; segredos B2 só via env. (TH-01..TH-12 → Threat model abaixo.)
- `br/lgpd-compliance` — T-02/T-05/T-12: base legal (execução de contrato + obrigação legal KYC); minimização por nível (simples não pede CNH/CRLV/MEI); finalidade explícita (hint por documento); retenção/anonimização RN-021 (`anonymized_at` nullable já no schema); documento KYC **nunca** público; consentimento registrado antes do submit.
- `br/brazilian-forms` — T-10/T-11: máscara+dígito CPF, telefone BR→E.164, placa Mercosul, CNPJ/MEI; `inputmode="numeric"`, **nunca `type="number"`**.
- `ux-advanced/form-ux-mastery` — T-10: wizard com stepper, validação inline no blur, um erro por campo, persistência parcial (retomada 30d), foco gerenciado entre passos.
- `quality/error-ux-patterns` — T-10/T-12: `jx-error-state` `role="alert"`; `jx-warn-banner` não-bloqueante para `mei_pending`; mensagem acionável (o que houve + o que fazer) nas exceções F-02 E1-E5 e erros de upload.
- `ux-advanced/file-upload-ux` — T-07/T-10: máquina completa de estados (idle/selecionando/comprimindo/enviando%/sucesso/erro), preview, mensagens acionáveis, upload via presigned em background (não bloqueia UI), retomada.
- `ux-advanced/onboarding-patterns` — T-10/T-12: wizard progressivo, retomada parcial com lembretes (dia 3/7), tela "em análise" pós-submit (não modal intrusivo).
- `ux-advanced/trust-safety-ux` — T-07/T-10/T-12: transparência LGPD ("por que pedimos cada documento"), segurança visível do upload (bucket privado), banner `mei_pending` explicativo não-punitivo, motivo verificável na reprovação.
- `ux-advanced/gesture-touch-patterns` (mobile) — T-07/T-10: alvos ≥44px, toque abre câmera (`capture`), feedback de toque (scale .97), foto em tela cheia por tap, sem gesto destrutivo escondido.
- `ui-ux-pro-max` — T-07/T-08/T-10/T-11: editorial-técnica (IDs `cou_…`, CPF mascarado, CNAE, placa, timestamps em mono); Fraunces italic em 1 palavra do H1; persimmon única cor de ação; **anti AI-slop** (sem gradiente/glow/check festivo/badge neon).
- `quality/accessibility-pro` — T-07/T-08/T-10/T-11: AA nos dois temas, foco visível `--focus-ring`, touch ≥44px, upload operável por teclado, erros via `aria-describedby`, progresso por `aria-live`, status por texto+ícone (nunca só cor), `axe-core` zero crítico.
- `product/component-library-governance` — T-07/T-08: 4 novos componentes governados (`jx-doc-upload`, `jx-doc-card`, `jx-kyc-review-row`, `jx-kyc-queue-table`) com story + baseline; reuso dos 4 estados (Phase 3) e `jx-wizard-stepper`/`jx-field` (Phase 4), não reinventa.
- `ux-advanced/design-tokens-system` — T-07/T-08/T-10/T-11: consome só camada semântica (`var(--surface)`, `var(--brand)`); nenhum primitivo nem hex hardcoded (Gate 2 §9 UI-SPEC — zero vars novas).
- `ux-advanced/empty-states-polish` — T-08/T-12: fila de KYC vazia (`jx-empty-state` causa+contexto, sem CTA falso); tela "em análise" pós-submit como empty-state informativo.
- `br/ux-copywriting-ptbr` — T-10/T-11/T-12: sentence case, CTA verbo+objeto sem ponto, erro = o que houve + o que fazer, **anti-enumeração** na colisão de CPF (E2 — mensagem única idêntica).
- `ux-advanced/dark-mode-theming` (DEC-001) — T-07/T-08/T-10/T-11: badges/banner/fila/cards validados claro+dark; fundos `_bg` claros não funcionam no dark → herda padrão Phase 3 (`--surface-elevated` + cor semântica viva).
- `quality/senior-quality-bar` (Gate 8) — todas as tasks: sem segredo B2 no repo (T-01), sem N+1 na fila de KYC (T-08/T-06 — eager load), sem injection, todo endpoint com decisão de auth explícita (T-05/T-06), PII fora de log (T-05/T-09).
- `domain/ionic-patterns` — T-10: wizard do entregador em Ionic (`ion-content`, safe-area, captura nativa via `capture`), tabbar do shell preservada, CTA sticky acima do teclado.

## Skills Dispensadas (com justificativa)

- `domain/safe2pay-escrow-br` / `domain/saas-billing-canonical` / `ux-advanced/payment-checkout-ux` — **dispensadas**: esta phase **não** toca billing/cobrança/escrow/checkout. `mei_pending` apenas registra restrição lógica ao pagamento direto; o bloqueio de repasse (RN-010) e saques são Phase 10/11 (`has_payments: false` no ROADMAP Phase 5).
- `ux-advanced/data-tables-ux` — **citada, não dispensada**: a fila de KYC do admin (`jx-kyc-queue-table`, T-08) é tabela densa com ordenação por "esperando há" e `aria-sort`. Aplicada em T-08.
- `ux-advanced/saas-dashboard-patterns` — **citada, não dispensada**: o painel admin (tela 19, T-11) é superfície dashboard densa. Aplicada em T-08/T-11 (layout sidebar, densidade, mono nos dados).
- `ux-advanced/chat-ux-patterns` — **dispensada**: sem chat nesta phase.
- `mobile/push-notifications-architecture` — **dispensada nesta phase**: notificações de reprovação/escalação (E4/E5) são entregues por e-mail/in-app (reuso do canal Phase 4); push do app do entregador é escopo da Phase 8 (`mobile: true` aqui é só o shell Ionic do wizard, não despacho).
- `mobile/offline-first` — **citada (resiliência parcial), não dispensada**: o upload via presigned é tolerante a falha de rede — arquivo retido no device + `jx-warn-banner` "sobe quando a internet voltar" + retry ao reconectar (T-07/T-10, UI-SPEC §3.4). O offline-first **completo** (fila persistente, polling) é Phase 9; aqui aplica-se só a resiliência de upload.
- `ux-advanced/responsive-breakpoint-strategy` — **dispensada**: wizard é mobile-first ≤480px (Ionic) e admin é desktop-first; ambos herdam os breakpoints já estabelecidos na Phase 3, sem nova estratégia.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

Consultado `.planning/TECH-DEBT.md`. TDs aplicáveis a esta phase:

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (aware-UTC obrigatório) | `urgency_class: pre_launch_high`; expiração de documentos, OTP de telefone e presigned URL têm timestamps. **Mitigado** — todas as colunas usam `UTC_DATETIME`/`ensure_aware_utc`; jobs usam `datetime.now(UTC)`. | T-02, T-06, T-09 |
| TD-015 | OTP de SMS síncrono (sem callback de delivery-status) | A confirmação de telefone do wizard (T-05) é **síncrona** (usuário digita) — alinhada à decisão consciente da Phase 4. Não regride a TD; permanece `post_launch_quarter`. | — (mantida) |
| TD-002 | Nível de validação por área pode defasar | `post_launch_quarter`; gatilho (3ª área / M1+90d) não disparou. Não entra. | — |
| TD-014 | Geocoding Nominatim rate limit | Não aplicável — esta phase não geocodifica (sem endereço de entregador no escopo). | — |

Novas TDs criadas por esta phase (ver "Open questions / LOW confidence"): **TD-016** (antivírus/scan de upload, `post_launch_30d`).

---

## Open questions / LOW confidence do RESEARCH (Regra 12 — destino estruturado)

Os 3 itens LOW confidence do `RESEARCH.md` (`### Tertiary (LOW confidence)`) recebem destino:

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| **B2 quirks de presigned** (addressing style `path` / region / endpoint S3 da B2 — Pitfall 1, A1) | LOW | **Task T-04 (spike):** implementar `StorageB2Adapter` com `Config(signature_version="s3v4", s3={"addressing_style":"path"})` + região derivada do endpoint; **critério de aceite verificável**: contrato `StoragePort` coberto contra o `StorageStubAdapter` em CI (sem rede), e a impl B2 real **validada no integration check (Gate 5)** contra a conta contratada antes de `/gsd:verify-work`. Falha de presign real = hotfix no adapter, contrato não muda. |
| **Antivírus/scan de upload malicioso** (A5 — sobretudo se antecedentes for PDF) | LOW | **Decisão consciente de adiar → TD-016** (`urgency_class: post_launch_30d`). No piloto, a mitigação primária é o **re-encode Pillow** (neutraliza vetores de imagem). **Mitigação adicional no plano (T-03):** antecedentes **restrito a imagem** no M1 (PDF não aceito até haver pipeline de scan próprio) — derruba o vetor de PDF malicioso. Reabrir scan externo (ClamAV) em 30d pós-launch se a área exigir PDF. |
| **Limites numéricos** (tamanho máx, expiração presigned, dimensão — A4) | LOW | **Fixados no plano com derivação (T-03/T-05):** presigned PUT **300s** (5 min — janela de captura+upload móvel), presigned GET admin **180s** (3 min — uma revisão), tamanho máx **10 MB** pré-compressão (foto de celular moderno ~3-8 MB; margem), dimensão máx **1920px** (legibilidade de documento sem custo de banda; integracoes.md §7), `MAX_IMAGE_PIXELS = 40_000_000` (anti decompression-bomb). Constantes em `app/couriers/constants.py` com comentário de derivação. |

---

## Threat model

Herdado da `## Security Baseline` do `RESEARCH.md` (Regra 7). Feature toca PII sensível (selfie, CPF, CNH, CRLV, MEI, antecedentes) + upload + acesso admin.

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|--------|-------|---------|------------|-----------|------|
| TH-01 | Acesso não-autorizado a documento KYC | URL pública / ACL aberta | Alto | Médio | Bucket B2 **privado**; acesso só por presigned GET ≤180s; `require_role("admin_area")` + `area_scope`; só dono + admin da área | T-03, T-04, T-06 |
| TH-02 | Upload malicioso (polyglot/malware/EXIF/formato falso) | PUT de arquivo hostil | Alto | Médio | **Magic bytes** (allowlist jpeg/png/webp; ignora extensão/content-type); **re-encode Pillow** obrigatório; **strip total EXIF**; limite tamanho + `MAX_IMAGE_PIXELS`; servir só o derivado | T-03 |
| TH-03 | IDOR em documento (ler doc de outro entregador/área) | doc_id forjado | Alto | Médio | `WHERE area_id=:scope AND courier_id=:cid` na query (não `if` pós-fetch); **404** (não 403); key = ULID não-sequencial | T-05, T-06 |
| TH-04 | SSRF no download interno do B2 (validação pós-upload) | endpoint/redirect malicioso | Alto | Baixo | `assert_safe_url(url, allowlist=B2_hosts)` antes de conectar e pós-redirect; httpx `follow_redirects=False`; rejeita IP privado/link-local/169.254.169.254 (reuso `integrations/http.py`) | T-04, T-05 |
| TH-05 | PII em log (CPF, documentos, telefone, e-mail) | log de body/key | Alto | Médio | Body nunca logado; `mask_document`/`mask_email`/`mask_phone` (reuso); key sem CPF; acesso a doc logado sem conteúdo (só `doc_id`+`actor`) | T-05, T-09 |
| TH-06 | Presigned URL vazada (compartilhada/interceptada) | leak da URL | Médio | Médio | Expiração curta (PUT 300s, GET 180s); escopo de método (PUT só grava key, GET só lê) e de key; HTTPS only; URL não logada — vazamento expira sozinho | T-03, T-05 |
| TH-07 | Tampering do documento pós-upload | regravação do objeto | Médio | Baixo | **SHA-256 do derivado** registrado (fonte de verdade); cliente declara sha256 do cru (detecta corrupção); regravação muda hash → detectável; `compare_digest` | T-03, T-05 |
| TH-08 | Abuso da consulta MEI/Receita (enumeração CNPJ / DoS) | spam de etapa completa | Médio | Baixo | Rate limit no signup/etapa (reuso `signup_rate_limit`); adapter Receita com timeout+fallback+E4; CNPJ nunca logado | T-05, T-06 |
| TH-09 | Escalonamento cross-área no painel admin | admin vê fila de outra área | Alto | Médio | Fila filtrada por `area_id=:scope` na query; `area_scope` resolve o escopo; admin plataforma cross-área é AUDITADO (nunca silencioso) | T-06, T-08 |
| TH-10 | Brute force / lockout no OTP de telefone | spam de OTP | Médio | Médio | Reuso `merchants/otp.py`: 6 dígitos, TTL 10min aware-UTC, máx 5 tentativas, `compare_digest`, resend 3/15min por conta+IP | T-05 |
| TH-11 | Path traversal via key do objeto | input de usuário na key | Médio | Baixo | Key gerada server-side (`couriers/{courier_id}/{ulid}.webp`), nunca de input; validação de prefixo | T-03, T-05 |
| TH-12 | Segredo B2 no repo | commit de `.env` | Alto | Baixo | `B2_KEY_ID`/`B2_APP_KEY`/`B2_*` só via env (Field default None em `config.py`); `.env` no `.gitignore`; `.env.example` com placeholders; segredo commitado = rotacionar | T-01 |

---

## Performance budget

Herdado de `.planning/config.json > performance_budget`.

**Frontend** (tela 03 wizard mobile, tela 19 admin):
- LCP ≤ 2500 ms (4G) · INP ≤ 200 ms · CLS ≤ 0.1
- Bundle main.js ≤ 400 kb gzip; wizard do entregador e painel admin **lazy por rota**.
- Upload **não bloqueia a UI**: presigned PUT roda em background; compressão client-side (≤1920px) antes do PUT reduz dados móveis; usuário avança no wizard durante o upload.
- Thumbnail do admin via presigned GET com `jx-loading-skeleton` (sem layout shift).

**Backend** (endpoints `/v1/couriers/*`):
- p95 ≤ 200 ms · p99 ≤ 500 ms por endpoint.
- **Presigned PUT/GET é operação local** (boto3 não faz rede ao assinar) → não bloqueia o request.
- **Reprocessamento de imagem (download B2 + Pillow) roda em worker arq**, fora do request HTTP (request de `complete` retorna rápido; status do documento transita assíncrono).
- **Zero N+1** na fila de KYC e no detalhe (eager load de `courier_documents` por courier — Gate 8).
- Job de expiração varre em lote (índice em `expires_at`), não 1 query por documento.

Medição: Lighthouse CI (frontend), pytest-benchmark nos endpoints críticos + structlog `duration_ms`.

---

## Observability checklist

Aplicando `quality/observability-production`:

- [ ] Todo endpoint novo (`/v1/couriers/*`, `/v1/admin/.../documents/*`) loga `request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms`.
- [ ] **Zero PII em log** — CPF/CNPJ/telefone/e-mail mascarados (`mask_*`); body de signup/documento **nunca** logado; `storage_key` e presigned URL **nunca** logados.
- [ ] **Eventos KYC auditados** em `audit_log` (append-only): `courier.submitted`, `kyc.document_viewed` (acesso a PII — só `doc_id`+`actor`, sem conteúdo), `kyc.item_approved`, `kyc.item_rejected` (+motivo), `kyc.escalated_48h`, `courier.activated`, `courier.mei_pending`.
- [ ] Erros 4xx → WARNING; 5xx → ERROR + alert; queries > threshold → WARNING.
- [ ] Worker de reprocessamento e de expiração logam início/fim/falha por `doc_id` (sem PII), com retry/backoff visível.
- [ ] `/healthz` reflete dependência B2 (degradação se adapter B2 inacessível — sem derrubar signup, que não depende de B2 síncrono).

---

## Error UX checklist

Aplicando `quality/error-ux-patterns` (UI — tela 03 e tela 19):

- [ ] **E1** retomada — "Rascunho salvo" discreto; ao reabrir, wizard restaura passo e documentos já enviados (estado, não re-upload).
- [ ] **E2** CPF mesma área — `jx-error-state` `role="alert"`: "Você já tem cadastro nessa cidade. Recupere o acesso." + link recuperar (anti-enumeração, mensagem única).
- [ ] **E3** `mei_pending` — `jx-warn-banner` `role="status"` persistente não-dispensável: explica direto-da-loja + CTA "Como regularizar".
- [ ] **E4** reprovação item-a-item — `jx-doc-card` mostra badge "Reprovado" + motivo específico + reabre upload **só do item**; selfie aprovada permanece aprovada.
- [ ] **E5** escalação — selo "Atrasada · esperando há Nh" (texto+ícone, não só cor) na fila admin.
- [ ] Erros de upload (tipo/tamanho/rede/hash) com mensagem acionável + "Tentar de novo"; falha de rede → arquivo retido + retry automático.
- [ ] Reprovar sem motivo bloqueado → `jx-error-state` "Selecione o motivo antes de reprovar".
- [ ] Validação inline ao blur (CPF/telefone/CNPJ), um erro por campo, não modal ao submit.
- [ ] Documento expirado (URL assinada) no admin → `jx-error-state` + retry que regenera a URL.

---

## Integration contracts

`integration_check: true`. Validados pelo `gsd-integration-checker` (Gate 5) contra **stubs** (B2 Stub, Receita Stub, SMS Stub) — nenhum toca serviço real em CI.

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| `POST /v1/couriers/signup` (etapa N) | `apps/web/.../entregador/cadastro/*.service.ts` | `apps/api/app/couriers/router.py` | body PII nunca logado; resposta `{courier_id, status, next_step}`; CPF mesma área → 409 anti-enumeração |
| `POST /v1/couriers/{id}/documents` | `apps/web/.../shared/components/doc-upload/*.ts` | `couriers/router.py` | body `{kind, sha256_client, content_type}` → resposta `{document_id, presigned_url, method:"PUT", expires_in:300, headers}` |
| `PUT {presigned_url}` (byte direto) | doc-upload component | **Backblaze B2** (Stub em CI) | upload não passa pelo backend; Stub simula PUT em FS temp; sem presign → recusado (test_no_public_access) |
| `POST /v1/couriers/{id}/documents/{d}/complete` | doc-upload component | `couriers/router.py` + worker | dispara reprocess (download→magic bytes→Pillow→strip EXIF→sha256→regrava); status `pending_upload`→`pending` |
| `GET /v1/admin/couriers/{id}/documents/{d}/view-url` | `apps/web/.../admin/kyc/*.service.ts` | `couriers/router.py` | authz `require_role("admin_area")`+`area_scope`; ownership+área no WHERE → 404 fora do escopo; resposta `{url, expires_in:180}` |
| `PATCH /v1/admin/.../documents/{d}` `{action, reason?}` | admin kyc component | `couriers/router.py` | approve/reject item-a-item; reject exige motivo; grava audit_log; todos approved → courier `active` |
| Receita MEI (situação + CNAEs) | `couriers/service.py` | `ReceitaPort` (Stub Phase 4) | CNAE ∈ {4930-2/01, 4930-2/02, 5320-2/02, 5229-0/99} → ativo; senão `mei_pending=True` |
| SMS OTP | `couriers/service.py` | `SmsPort` (Stub Phase 4) | confirmação síncrona de telefone (reuso `merchants/otp.py`) |

---

## Tasks

Cada task tem skills aplicadas e critério de sucesso isolado. Agrupadas em 5 planos por wave (ver "Execution order").

### T-01 — Deps + config de segredos B2 + `.env.example`
- **Type:** infra
- **Files:** `apps/api/pyproject.toml`, `apps/api/app/core/config.py`, `apps/api/.env.example`, `apps/api/uv.lock`
- **Skills aplicadas:**
  - `owasp-security` (Gestão de Segredos / TH-12) — `B2_KEY_ID`/`B2_APP_KEY`/`B2_ENDPOINT_URL`/`B2_REGION`/`B2_KYC_BUCKET`/`B2_ALLOWLIST_HOSTS` como `Field(default=None)` em `config.py`; placeholders no `.env.example`; nada de segredo no repo.
  - `quality/senior-quality-bar` (Gate 8) — segredo no repo é FAIL-BLOCK; verificar `.env` no `.gitignore`.
- **Descrição:** `uv add "boto3>=1.43,<2" "Pillow>=12.2,<13"`; adicionar settings B2 (defaults None); registrar `.env.example` com placeholders e comentário "rotacionar se commitado".
- **Success:** `uv run python -c "import boto3, PIL; from app.core.config import settings"` ok; `grep -r "B2_APP_KEY=" --include=".env" .` → 0 fora de `.env.example`; lockfile commitado.
- **Depends on:** none

### T-02 — Migration 0004 + models `couriers`/`courier_documents`
- **Type:** migration
- **Files:** `apps/api/migrations/versions/0004_couriers_kyc.py`, `apps/api/app/couriers/models.py`, `apps/api/app/couriers/__init__.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — reusa `AreaScopedMixin`/`TimestampMixin`/`UTC_DATETIME`/`BIG_ID`; `couriers` AreaScoped (`area_id`), `status` enum (pending_kyc/active/suspended/banned), `mei_pending` bool, `mei_cnpj` nullable, unique `(area_id, cpf)` para E2; `courier_documents` com `kind` enum, `status` enum, `storage_key`, `sha256`, `content_type`, `expires_at` (UTC_DATETIME nullable), `reject_reason` nullable, `anonymized_at` nullable, índice em `expires_at` e `(courier_id, status)`.
  - `br/lgpd-compliance` (RN-021) — `anonymized_at`/`deleted_at` nullable já no schema (alcançável por jobs Phase 14).
  - `domain/mysql-schema-design` (TD-010) — todas as colunas de tempo via `UTC_DATETIME`.
- **Descrição:** seguir convenções de `0003_merchants_plans.py`; courier vincula `users` (mesmo CPF, vínculo por área) e `areas`.
- **Success:** `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` reversível; `pytest tests/couriers/test_models.py` (unique mesma área, FK RESTRICT).
- **Depends on:** none

### T-03 — Pipeline de mídia: validação + reprocessamento Pillow + SHA-256
- **Type:** new (security-critical)
- **Files:** `apps/api/app/media/validation.py`, `apps/api/app/media/reprocess.py`, `apps/api/app/couriers/constants.py`, `apps/api/tests/media/test_reprocess.py`
- **Skills aplicadas:**
  - `owasp-security` (upload / TH-02, TH-07, TH-11) — `sniff_content_type` por **magic bytes** (allowlist jpeg/png/webp; ignora extensão/content-type); `reprocess_to_webp` re-encode WebP **sem `exif=`** (strip total); `Image.MAX_IMAGE_PIXELS=40_000_000`; SHA-256 do **derivado**; key server-side.
  - `br/lgpd-compliance` (TH-exif / Pitfall 3) — KYC não usa GPS → strip 100% do EXIF; teste afirma `Image.getexif()` vazio no derivado.
- **Descrição:** constantes de limites com derivação documentada (PUT 300s, GET 180s, 10MB, 1920px). **Antecedentes restrito a imagem no M1** (LOW-2 → TD-016): allowlist sem PDF.
- **Success:** `pytest tests/media/test_reprocess.py` — magic bytes rejeita arquivo com extensão falsa; EXIF stripado (getexif vazio); resize ≤1920; sha256 do derivado estável; decompression-bomb (pixels > MAX) rejeitada.
- **Depends on:** T-01

### T-04 — `StoragePort` (Protocol) + `StorageStubAdapter` + `StorageB2Adapter` (spike LOW-1)
- **Type:** new (adapter)
- **Files:** `apps/api/app/integrations/base.py`, `apps/api/app/integrations/storage.py`, `apps/api/app/integrations/storage_stub.py`, `apps/api/app/integrations/factory.py`, `apps/api/tests/integrations/test_storage_stub.py`
- **Skills aplicadas:**
  - `meta/orchestration-decision-tree` (LOW-1) — boto3 S3v4 contra endpoint B2 num único `StoragePort` (reuso futuro Phase 9); `Config(signature_version="s3v4", s3={"addressing_style":"path"})`.
  - `owasp-security` (SSRF / TH-04) — `presign_*` chama `assert_safe_url(url, allowlist=B2_hosts)`; `fetch` (download interno) via httpx `follow_redirects=False`.
  - `quality/senior-quality-bar` — segredo B2 só do `settings`, nunca hardcoded.
- **Descrição:** `PresignResult` dataclass (`url/method/expires_in/headers`); Protocol `presign_put/presign_get/fetch/put_bytes`; Stub usa FS temp + URLs fake (sem rede); `get_storage_adapter()` injeta Stub em dev/test, B2 em prod. **Spike:** a impl B2 é validada no Gate 5 contra a conta real; CI valida só o contrato via Stub.
- **Success:** `pytest tests/integrations/test_storage_stub.py` — contrato do `StoragePort` (presign fake, upload simulado, fetch devolve bytes); `test_no_public_access` (acesso sem presign recusado pelo Stub).
- **Depends on:** T-01

### T-05 — Router/service de signup + documentos (wizard etapas + presign + complete)
- **Type:** new_endpoint
- **Files:** `apps/api/app/couriers/router.py`, `apps/api/app/couriers/service.py`, `apps/api/app/couriers/schemas.py`, `apps/api/app/couriers/documents.py`, `apps/api/app/workers/document_reprocess.py`, `apps/api/tests/couriers/test_wizard.py`, `apps/api/tests/couriers/test_signup.py`, `apps/api/tests/couriers/test_documents.py`, `apps/api/tests/couriers/test_authz.py`, `apps/api/tests/couriers/conftest.py`
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` + `product/api-design-contracts` — `/v1/couriers/signup` (público, `signup_rate_limit`), etapas autenticadas; Pydantic `extra="forbid"`; contratos da seção Integration.
  - `owasp-security` (TH-03/TH-05/TH-06/TH-10/A01) — ownership+área no WHERE → 404; presign PUT 300s; reuso `merchants/otp.py`; máscaras PII; body nunca logado.
  - `br/lgpd-compliance` — minimização por nível (simples não pede CNH/CRLV/MEI); consentimento registrado antes do submit.
  - `quality/observability-production` — eventos auditados; zero PII.
- **Descrição:** signup multi-etapa com draft server-side (retomada 30d, E1); E2 unique `(area_id, cpf)` → 409 anti-enumeração; `POST /documents` emite presign; `POST /documents/{d}/complete` enfileira worker de reprocess (download→validate→reprocess→regrava→`pending`).
- **Success:** `pytest tests/couriers/test_wizard.py tests/couriers/test_signup.py tests/couriers/test_documents.py tests/couriers/test_authz.py` — E1 retomada, E2 mesma/outra área, presign curto, complete transita estado, IDOR cross-área → 404.
- **Depends on:** T-02, T-03, T-04

### T-06 — KYC item-a-item + máquina de estados + admin endpoints + MEI
- **Type:** new_endpoint
- **Files:** `apps/api/app/couriers/state_machine.py`, `apps/api/app/couriers/kyc.py`, `apps/api/app/couriers/router.py` (admin), `apps/api/app/couriers/service.py`, `apps/api/tests/couriers/test_kyc.py`, `apps/api/tests/couriers/test_state_machine.py`, `apps/api/tests/couriers/test_mei.py`
- **Skills aplicadas:**
  - `owasp-security` (TH-09/A01) — `require_role("admin_area")` + `area_scope`; fila e detalhe filtrados por `area_id`; admin plataforma cross-área AUDITADO.
  - `domain/fastapi-production-patterns` — `COURIER_TRANSITIONS`/`DOCUMENT_TRANSITIONS` espelhando `merchants/state_machine.py`; `assert_transition` → 422.
  - `product/api-design-contracts` — `GET .../view-url` (presign 180s), `PATCH .../documents/{d}` `{approve|reject+motivo}`.
  - `br/lgpd-compliance` (RN-024) — MEI reusa `ReceitaPort`; CNAE compatível → ativo, senão `mei_pending=True`; CNPJ nunca logado.
  - `quality/senior-quality-bar` — sem N+1 (eager load `courier_documents`).
- **Descrição:** aprovação item-a-item (status independente por item — E4: reprovar CNH não invalida selfie); reject exige motivo; todos approved + nível atingido (RN-002) → courier `active`; `validate_mei` (E3); `view-url` com ownership na query.
- **Success:** `pytest tests/couriers/test_kyc.py tests/couriers/test_state_machine.py tests/couriers/test_mei.py` — item-a-item independente (E4), transições inválidas → 422, MEI inativo → mei_pending (E3), reject sem motivo recusado.
- **Depends on:** T-05

### T-09 — Jobs aware-UTC: expiração de documentos + escalação 48h
- **Type:** infra (worker)
- **Files:** `apps/api/app/workers/document_expiry.py`, `apps/api/app/workers/settings.py`, `apps/api/tests/couriers/test_escalation.py`, `apps/api/tests/couriers/test_expiry.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` (TD-010) — `datetime.now(UTC)` + `ensure_aware_utc`; índice em `expires_at` (varredura em lote, sem N+1).
  - `quality/observability-production` — job loga início/fim/falha por `doc_id` sem PII; escalação grava `kyc.escalated_48h` em audit_log.
  - `owasp-security` (TH-09) — escalação dá visibilidade ao admin plataforma sem dar acesso a outro admin de área.
- **Descrição:** job de expiração transita CNH/CRLV/MEI vencidos para re-upload (aware-UTC); job de escalação marca documentos `pending` há ≥48h (clock comparado aware-UTC) → sobe na fila + notifica admin plataforma (E5). Registrar no scheduler arq existente.
- **Success:** `pytest tests/couriers/test_escalation.py tests/couriers/test_expiry.py` (clock fake) — documento vencido transita; `pending` ≥48h escala; comparações nunca misturam naive/aware.
- **Depends on:** T-06

### T-07 — Componentes compartilhados: `jx-doc-upload` + `jx-doc-card`
- **Type:** ui_component
- **Files:** `apps/web/src/shared/components/doc-upload/doc-upload.component.ts`, `.../doc-upload/doc-upload.component.scss`, `.../doc-upload/doc-upload.stories.ts`, `apps/web/src/shared/components/doc-card/doc-card.component.ts`, `.../doc-card/doc-card.component.scss`, `.../doc-card/doc-card.stories.ts`, `apps/web/src/shared/components/index.ts`
- **Skills aplicadas:**
  - `ux-advanced/file-upload-ux` — máquina de estados completa (idle/selecionando/comprimindo/enviando%/sucesso/erro); compressão client-side ≤1920px antes do PUT; upload em background.
  - `ux-advanced/gesture-touch-patterns` (mobile) — `capture="environment|user"`, alvos ≥44px, scale .97, foto em tela cheia por tap.
  - `product/component-library-governance` + `product/visual-regression-testing` — stories + baseline (idle/comprimindo/enviando-60/sucesso/erro · claro+dark · mobile).
  - `ux-advanced/design-tokens-system` + `ux-advanced/dark-mode-theming` + `ui-ux-pro-max` — só vars semânticas; badge texto+ícone+cor; anti-slop (sem glow/gradiente); dark herda `--surface-elevated`.
  - `quality/accessibility-pro` — upload por teclado, progresso `aria-live`, status nunca só por cor, preview com `aria-label`.
  - `ux-advanced/trust-safety-ux` — microcopy "por que pedimos" + segurança do upload.
  - `mobile/offline-first` (resiliência) — falha de rede → arquivo retido + `jx-warn-banner` + retry ao reconectar.
- **Descrição:** `jx-doc-upload` (captura/preview/validação/compressão/presign PUT); `jx-doc-card` (status por item §4.2; modo edição compõe doc-upload, modo leitura para admin; reenvio item-a-item E4).
- **Success:** `pnpm test` componentes; stories renderizam todos os estados; `axe` zero crítico nos dois temas; status por texto+ícone (não só cor).
- **Depends on:** none (contrato de presign documentado na Integration; mockado nas stories)

### T-08 — Componentes admin: `jx-kyc-queue-table` + `jx-kyc-review-row`
- **Type:** ui_component
- **Files:** `apps/web/src/features/admin/kyc/queue-table.component.ts`, `.../kyc/queue-table.component.scss`, `.../kyc/queue-table.stories.ts`, `.../kyc/review-row.component.ts`, `.../kyc/review-row.component.scss`, `.../kyc/review-row.stories.ts`
- **Skills aplicadas:**
  - `ux-advanced/data-tables-ux` + `ux-advanced/saas-dashboard-patterns` — fila densa, ordenação por "esperando há" (`aria-sort`), selo "Atrasada" ≥48h (E5), mono nos dados.
  - `product/component-library-governance` + `product/visual-regression-testing` — stories (com-fila/vazia/escalado-48h/loading; aprovar/reprovar-motivo/auto-aprovado/thumb-carregando · claro+dark).
  - `ux-advanced/empty-states-polish` — fila vazia `jx-empty-state` causa+contexto, sem CTA falso.
  - `quality/accessibility-pro` + `ux-advanced/dark-mode-theming` + `ui-ux-pro-max` — `<table>` semântica `<th scope>`, navegação por teclado, CPF mascarado em mono, status texto+ícone, badges dark.
  - `quality/error-ux-patterns` — reprovar sem motivo bloqueado; thumb expirada → erro + retry.
- **Descrição:** `jx-kyc-queue-table` (fila AreaScoped, escalação 48h); `jx-kyc-review-row` (thumb via presign GET, dados mono, aprovar/reprovar com motivo enum+textarea obrigatório, item auto MEI sem botões, bloco Score placeholder inerte).
- **Success:** `pnpm test`; stories cobrem fila/vazia/48h/reprovar-sem-motivo; `axe` zero crítico; CPF mascarado.
- **Depends on:** none (contratos mockados nas stories)

### T-10 — Tela 03: Wizard do entregador (Ionic, mobile-first) — wiring
- **Type:** ui_component
- **Files:** `apps/web/src/features/entregador/cadastro/cadastro.page.ts`, `.../cadastro/cadastro.routes.ts`, `.../cadastro/cadastro.service.ts`, `.../cadastro/steps/*.ts`, `.../cadastro/cadastro.stories.ts`
- **Skills aplicadas:**
  - `domain/ionic-patterns` — `ion-content`, safe-area, CTA sticky acima do teclado, tabbar preservada, rota dedicada `/entregador/cadastro` lazy.
  - `ux-advanced/form-ux-mastery` + `br/brazilian-forms` — `jx-wizard-stepper` dinâmico (3/4 passos por nível), `jx-field` (CPF dígito, telefone→E.164, placa Mercosul, CNPJ), validação no blur, persistência parcial (E1).
  - `ux-advanced/onboarding-patterns` — wizard progressivo, retomada 30d, tela "em análise" pós-submit (empty-state informativo).
  - `br/ux-copywriting-ptbr` + `quality/error-ux-patterns` — E2 anti-enumeração (mensagem única); erros acionáveis; mei_pending banner (E3).
  - `ux-advanced/trust-safety-ux` + `br/lgpd-compliance` — microcopy por documento, linha de confiança do upload, consentimento (checkbox) antes do submit.
  - `quality/accessibility-pro` + `ui-ux-pro-max` + `ux-advanced/dark-mode-theming` — AA dois temas, foco, "Passo N de M" `aria-live`, H1 Fraunces italic.
- **Descrição:** compõe `jx-wizard-stepper` + `jx-field` + `jx-doc-card`/`jx-doc-upload` (T-07); passo 1 área+dados+OTP, passo 2 selfie, passo 3 veículo, passo 4 documentos condicional; submit → `pending_kyc`. **Etapa 5 bairros/preços NÃO entra** (Phase 6).
- **Success:** wireframe-contract de `03-cadastro-entregador.html` coberto (exceto etapa 5); E1/E2/E3 fluem na UI; `axe` zero crítico claro+dark; stories dos estados.
- **Depends on:** T-05, T-06, T-07

### T-11 — Tela 19: Painel de revisão do admin de área — wiring
- **Type:** ui_component
- **Files:** `apps/web/src/features/admin/kyc/kyc-detalhe.page.ts`, `.../kyc/kyc.routes.ts`, `.../kyc/kyc.service.ts`, `.../kyc/kyc-detalhe.stories.ts`
- **Skills aplicadas:**
  - `ux-advanced/saas-dashboard-patterns` + `ux-advanced/data-tables-ux` — layout sidebar, fila (T-08) + detalhe item-a-item, densidade, mono.
  - `product/api-design-contracts` — consome `GET view-url` + `PATCH documents/{d}`; thumb via presign GET com skeleton.
  - `quality/error-ux-patterns` — reprovar sem motivo bloqueado; documento expirado → erro + retry (regenera URL).
  - `br/ux-copywriting-ptbr` + `ui-ux-pro-max` + `quality/accessibility-pro` + `ux-advanced/dark-mode-theming` — CPF mascarado mono, status texto+ícone, AA dois temas, bloco Score placeholder inerte.
  - `quality/observability-production` — ações disparam eventos auditados (servidor grava; UI reflete).
- **Descrição:** compõe `jx-kyc-queue-table` + `jx-kyc-review-row` (T-08); aprovar/reprovar item-a-item otimista com rollback; escalação 48h refletida; "Suspender com motivo" presente (fluxo de recurso é Phase 13).
- **Success:** wireframe-contract de `19-admin-area-entregador-detalhe.html` coberto (exceto bloco Score interativo, deferido); `axe` zero crítico; reprovar sem motivo bloqueia; stories revisão-2-de-4/reprovar-sem-motivo/documento-expirado.
- **Depends on:** T-06, T-08

### T-12 — Estados especiais do entregador: `pending_kyc` + banner `mei_pending`
- **Type:** ui_component
- **Files:** `apps/web/src/features/entregador/inicio.page.ts` (banner), `apps/web/src/features/entregador/cadastro/em-analise.component.ts`
- **Skills aplicadas:**
  - `ux-advanced/empty-states-polish` + `ux-advanced/onboarding-patterns` — tela "Recebemos seu cadastro" (empty-state informativo, sem festividade, `role="status"`).
  - `quality/error-ux-patterns` + `ux-advanced/trust-safety-ux` — `jx-warn-banner` persistente não-dispensável para `mei_pending` (RN-024), copy explicativo não-punitivo + CTA "Como regularizar".
  - `br/ux-copywriting-ptbr` + `accessibility-pro` + `ux-advanced/dark-mode-theming` — sentence case, AA, badge/banner dark.
- **Descrição:** pós-submit mostra documentos em modo leitura "Em análise"; perfil/início do entregador com banner `mei_pending` permanente quando flag ativa.
- **Success:** banner aparece só com `mei_pending=True`; tela "em análise" sem confete; `axe` zero crítico.
- **Depends on:** T-06, T-07

---

## Execution order

Waves (grupos paralelizáveis). **parallel-hint: back-front** — backend (Plan 01) e frontend de componentes (Plan 03) rodam na mesma Wave 1.

- **Wave 1 (paralelo back+front):**
  - **Plan 01 (backend foundation):** T-01, T-02, T-03, T-04
  - **Plan 03 (frontend componentes):** T-07, T-08
- **Wave 2 (backend):**
  - **Plan 02 (backend fluxo):** T-05 → T-06 → T-09
- **Wave 3 (frontend wiring — depende de Wave 1+2):**
  - **Plan 04 (wizard entregador):** T-10, T-12
  - **Plan 05 (admin KYC):** T-11

Dependências intra-wave: T-03/T-04 dependem de T-01; T-05 depende de T-02/T-03/T-04; T-06 depende de T-05; T-09 depende de T-06; T-10 depende de T-05/T-06/T-07; T-11 depende de T-06/T-08; T-12 depende de T-06/T-07.

---

## Reconciliation expectations

Ao fim, `/gsd:reconcile-state 5` verifica:
- Arquivos de cada task existem (migration 0004, `couriers/`, `media/`, `integrations/storage*`, componentes web).
- Endpoints declarados têm handler (signup, documents, complete, view-url, PATCH item).
- Skills aplicadas de fato presentes no código: magic bytes (não só extensão), strip EXIF, ownership no WHERE, máscaras PII, `assert_safe_url`, aware-UTC nos jobs, rate limit no signup.
- Bucket nunca público; presigned curto; CPF mascarado na UI admin.
- Nenhum arquivo-fantasma; nenhuma feature-fantasma (etapa 5/bairros, score, push — devem estar ausentes).

Divergências → `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

- Revert dos commits `feat(phase-5/plan-NN): ...`.
- Migration: `uv run alembic downgrade -1` (remove `couriers`/`courier_documents` — sem dado legado, greenfield).
- Ops: rotacionar `B2_APP_KEY` se vazada; remover bucket de teste se criado; nenhuma feature flag (entidades novas, sem toggle).

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
- Integration contracts: {presente | N/A | incompleto}
- Revision iteration: {1 | 2 | 3 | final}
