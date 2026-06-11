# Phase 12 — EXECUTION-LOG (backend, Waves 1-2)

**Escopo executado:** SOMENTE backend (`apps/api`), Waves 1 e 2 do PLAN (T-01..T-10).
Frontend (Wave 3 / T-11..T-13) e integration-check (Wave 4 / T-14) NÃO executados.
**Branch:** master · **Data:** 2026-06-11

## Tasks concluídas

| Task | Descrição | Arquivos | Commit |
|------|-----------|----------|--------|
| T-01 | Migration 0010 (4 tabelas area-scoped + `merchants.external_ref`, reversível) | `alembic/versions/0010_public_api_webhooks.py`, `app/api_keys/models.py`, `app/webhooks/models.py`, `app/merchants/models.py` | e67e890 |
| T-02 | Módulo `api_keys` (gerar `jxg_<key_id>_<secret>`, hash argon2id, listar, revogar soft) | `app/api_keys/{schemas,repo,service}.py` | e67e890 |
| T-03 | Dependency `api_key_scope` (parse Bearer/X-API-Key, 401 estável, cache 30s invalidado no revoke) | `app/api_keys/dependencies.py` | e67e890 |
| T-04 | `POST /v1/public/deliveries` (auth por key, Idempotency-Key obrigatório, snapshot 24h, 409/replay, 429+Retry-After) | `app/api_public/{schemas,service,router}.py` | e67e890 |
| T-05 | Job arq purge de idempotência expirada | `app/workers/webhooks.py`, `app/workers/settings.py` | e67e890 |
| T-06 | Webhooks outbound: assinatura HMAC Stripe `t=,v1=` + ULID `X-Jaxego-Event-Id`; serializer com minimização de PII | `app/webhooks/{signing,serializer}.py` | e67e890 |
| T-07 | Hook não-bloqueante em `deliveries.service.transition` | `app/deliveries/service.py`, `app/webhooks/service.py` | e67e890 |
| T-08 | Anti-SSRF da URL de webhook (https + bloqueio loopback/privado/link-local/metadata) | `app/webhooks/ssrf.py` | e67e890 |
| T-09 | Job de entrega com backoff EXATO 8× + `failed`+alerta (LOW-1) | `app/webhooks/delivery.py`, `app/workers/webhooks.py` | e67e890 |
| T-10 | Endpoints admin de área (keys + webhook config + histórico) | `app/api_keys/admin_router.py`, `app/webhooks/schemas.py` | e67e890 |
| — | Suite de testes (59 not-mysql + reversibilidade 0010 mysql) | `tests/api_public/*`, `tests/webhooks/*`, `tests/fixtures_public_api.py`, `tests/db/test_migration_0010.py` | ecaf365 |

## Security baseline (Gate 4) — TH-01..TH-10

- **TH-01** argon2id hash (reuso `core.security.hash_password`), 401 estável (dummy verify em todo caminho de falha, latência constante), revoke efetivo (cache invalidado no revoke + TTL 30s). ✔
- **TH-02** Pydantic `extra='forbid'` no body público; reuso da validação do `create_delivery`. ✔
- **TH-03** resolução de loja SEMPRE escopada por `area_id`; loja/keys de outra área → 404/403 sem vazar existência. ✔
- **TH-04** idempotência 24h: mesma key+body→mesma resposta; key+body divergente→409. ✔
- **TH-05** anti-SSRF: só https + bloqueio de host privado/metadata, revalidado antes de cada POST. ✔
- **TH-06/07** HMAC-SHA256 com `t`+event-id; verificação com `compare_digest` (janela 5min). ✔
- **TH-08** rate limit por API key + 429 com `Retry-After`. ✔
- **TH-09** API key/secret nunca logados; payload de webhook sem phone/CPF/nome (teste assertivo). ✔
- **TH-10** backoff 8× exato → `failed`+alerta; 4xx≠429 = falha permanente. ✔

## Desvios (deviation rules)

1. **[Rule 3 — path da API pública]** O contrato `integracoes.md:42` especifica `POST /v1/deliveries` para a API pública, mas o router interno de loja (auth por sessão) já ocupa esse path. Dois POST no mesmo path são ambíguos no FastAPI. Montei a API pública em `POST /v1/public/deliveries` para evitar colisão sem quebrar a superfície interna. Registrado como **TD-12-01** (pre_launch_medium) para alinhar com o integrador antes do go-live.

2. **[Rule 2 — 4xx permanente]** `integracoes.md:51` define "4xx ≠ 429 = falha permanente (sem retry)". O backoff foi ajustado para tratar 4xx≠429 como `failed` imediato (não consome as 8 tentativas), além do esgotamento normal das 8 em 5xx/timeout.

3. **[Rule 2 — `merchants.external_ref`]** D-03 exige mapear `merchant_external_ref`→loja, mas o modelo `Merchant` não tinha esse campo. Adicionei a coluna `external_ref` (nullable, UNIQUE por área) na migration 0010 — requisito de correção para o endpoint público funcionar.

4. **[Rule 2 — header de Retry-After]** O handler global de `AppError` não propagava headers. Estendi `AppError.headers` + o handler para emitir `Retry-After` no 429 (RFC 7807 + header — D-05). Mudança mínima e retrocompatível.

## Tech debt registrada

- **TD-12-01** — API pública em `/v1/public/deliveries` (pre_launch_medium).
- **TD-12-02** — rate limit + cache de auth in-process, não distribuído (post_launch_quarter).

## Resultados

- `uv run pytest -m "not mysql"`: Phase 12 → **59 passed**. Suite completa: tudo verde EXCETO `tests/test_health.py::test_health_logs_request_with_required_fields` — falha **pré-existente** de isolamento de capsys/structlog (passa isolado; não relacionada à Phase 12; fora de escopo).
- `uv run ruff check app tests`: **All checks passed**.
- `pytest -m mysql tests/db/test_migration_0010.py`: escrito (reversibilidade upgrade→downgrade→upgrade), NÃO executado aqui (requer MySQL live).

## Não feito (fora do escopo desta execução)

- Wave 3 (frontend tela 22 / T-11..T-13).
- Wave 4 (gsd-integration-checker round-trip / T-14).
- Execução do `pytest -m mysql` (precisa de DB live em CI).

---

# Phase 12 — EXECUTION-LOG (frontend, Wave 3 / T-11..T-13)

**Escopo executado:** SOMENTE frontend (`apps/web`), Wave 3 do PLAN (T-11, T-12, T-13).
**Branch:** master · **Data:** 2026-06-11 · **Executor:** Claude Opus 4.8

## T-11 — jx-secret-reveal (componente compartilhado)

- `apps/web/src/shared/components/secret-reveal/` (component + scss + spec + stories).
- Exibe o segredo UMA vez (D-01/D-10): campo `<code>` mono read-only + botão Copiar com
  feedback textual "Copiado" + aviso PERMANENTE em `aria-live="polite"` (UI-SPEC §a11y).
- `focus()` move o foco ao campo do segredo (foco gerenciado pelo modal foco-preso).
- Fallback `execCommand('copy')` quando a Clipboard API não está disponível (contexto
  não-seguro); não marca "Copiado" se a cópia falhar.
- Exportado no barrel `shared/components/index.ts`. **7 testes.** Commit `5666b4e`.

## T-12 / T-13 — Tela 22 + serviço Angular

- `apps/web/src/features/admin/api-keys/` (page ts/html/scss + service + spec + stories).
- **Lista de chaves** (jx-data-table): Nome | key_id (mono) | Escopos | Criada | Último uso |
  Status (pílula ativa/revogada) | Ações. Empty state com CTA "Criar primeira chave".
- **Criar chave** (modal foco-preso, Esc fecha, aria-modal, retorno de foco ao gatilho):
  nome + escopos; sucesso mostra o segredo 1× via jx-secret-reveal. Key nova destacada
  com `--brand-wash` por ~2s.
- **Revogar**: confirmação sensível before→after (padrão Phase 6) com nome + key_id e copy
  "...em até 1 minuto. Esta ação não pode ser desfeita."
- **Painel de webhook**: URL https com validação anti-SSRF inline (`pattern ^https://`),
  eventos (checkboxes pt-BR), secret atual + rotação (segredo novo exibido 1×), e histórico
  de entregas (jx-data-table paginado, badges entregue/pendente/falhou via tokens semânticos).
- **Estados** empty/loading/error em chaves, webhook e histórico (signals + jx-data-table).
- **AdminApiKeysService** + signals; tipos espelham `apps/api/app/api_keys/schemas.py` e
  `apps/api/app/webhooks/schemas.py`. Rota lazy `/admin/api-keys` em `app.routes.ts`.
- **11 testes** (service HTTP + estados de signals). Commit `5043a6a`.

## Desvios (deviation rules)

- Nenhum desvio de arquitetura. Ajuste menor de teste (microtask entre flushes) — não é desvio.
- **Path da API pública (TD-12-01):** o serviço Angular consome as rotas **admin** de área
  (`/v1/admin/areas/{id}/...`), que não sofreram a colisão de path do TD-12-01 (esse afeta só
  o endpoint público de criação). Sem impacto no frontend.

## Resultados (Gate 7)

- `npm run test` (apps/web): **139 passed** (121 anteriores + 18 novos). Verde.
- `npm run build` (ng build): **OK**. Chunk lazy `api-keys-page` 28.39 kB / 6.73 kB transfer.
  (Warning maplibre-gl CommonJS é pré-existente, não relacionado.)
- `npm run lint` (ng lint): **All files pass linting.**
- Zero hex: `grep "#[0-9A-Fa-f]{3,6}" apps/web/src/features/admin/api-keys/` → **0**;
  idem em `shared/components/secret-reveal/` → **0**. Só tokens semânticos.

## Não feito (fora do escopo desta execução)

- Wave 4 (gsd-integration-checker round-trip / T-14).
- Execução do `pytest -m mysql` (precisa de DB live em CI).
