# EXECUTION-LOG — Phase 4: Cadastro e ativação de loja

> Rastro de execução do PLAN.md (T-00..T-14), por `gsd-executor`, 2026-06-10.
> Execução SEQUENCIAL (single executor): backend até fixar o contrato → frontend → testes.

## Resultado por task

| Task | Tipo | Commit | Resultado |
|------|------|--------|-----------|
| T-00 | test/infra | `4513df6` | Scaffolds RED (E1–E4, SSRF, OTP, seed) + deps `httpx` (runtime) + `validate-docbr 2.0.0` |
| T-01 | migration | `375f4cf` | Models `merchants`/`merchant_users`/`subscription_plans`/`merchant_subscriptions` + migration `0003` (upgrade/downgrade verde em SQLite) |
| T-05 | infra/integration | `ee27584` | Adapters Protocol + httpx + Stub + `assert_safe_url` (SSRF A10); factory Stub em {dev,test} |
| T-02/03/04 | endpoint+lógica | `69143c0` | Contrato `/v1/merchants` + `/v1/plans` + `/v1/interest`; service E1–E4 + anti-enumeração (`verify_dummy`, tempo ~constante); state machine; OTP aware-UTC; rate limit 5/min/IP; máscara PII + `phone` na denylist |
| T-13 | test/spike | `e8c76ef` | Fixtures Receita (minhareceita/BrasilAPI) + Nominatim; `test_contracts`; CNPJ alfanumérico verde (validate-docbr 2.0.0); TD-014/TD-015 registradas |
| T-07 | worker | `444f367` | Job `revalidate_receita` (retry 6/6/12/24h aware UTC); pending_validation→active via state machine + audit |
| T-08 | infra | `a73c657` | `seed.py` idempotente (Pádua + 4 planos + 2 admins); `.env.example` (raiz + apps/api) com placeholders + allowlists SSRF |
| T-06/T-14 | infra/test | `8597614` | PII fora de log (mask + denylist); acceptance MySQL (`@pytest.mark.mysql`); suíte not-mysql verde |
| T-09 | ui_component | `37a293a` | `jx-wizard-stepper` + `jx-field` + `jx-plan-card` (governados, a11y, data-driven, zero hex) + spec + baseline |
| T-10/11/12 | ui_component | `d66c596` | Wizard tela 02 (4 passos, forms BR, E1/E2, persistência sem senha); estado vazio + captura; plano tela 16; banners pending_* + onboarding hint |

## Desvios (Rules)

- **Rule 3** — `app/core/ratelimit.py` (sliding window in-process) foi criado para satisfazer o rate limit do signup (TH-07) citado no threat model; não havia limiter pré-existente. Limiter distribuído (Redis) é upgrade futuro (mencionado no docstring).
- **Rule 3** — `mask_email`/`mask_phone`/`mask_document` adicionados a `core/logging.py` (parte de T-06) antecipadamente porque T-03 (service) depende deles para o audit sem PII.
- **Decisão de caminho** — o PLAN pede `apps/api/.env.example`; o repo já tinha `.env.example` na RAIZ (lido por settings via cwd `apps/api`). Mantidos os DOIS sincronizados (raiz canônica + `apps/api/.env.example` conforme o plano e o README).
- **Resolução geocoding/área** — resolução POINT-in-area por bounding box (bbox em `area.config`, default Pádua). Polígono preciso chega com a fase de mapas; bbox basta para cobertura vs estado-vazio nesta phase.

## Gate 7 (verificação local)

**Backend** (`apps/api`):
- `uv run ruff check .` → limpo
- `uv run ruff format --check .` → 98 arquivos formatados
- `uv run basedpyright` → 0 errors, 0 warnings
- `uv run pytest -m "not mysql"` → **112 passed, 4 deselected**
- `uv run python tools/check_naive_datetime.py app/ tools/` → OK (sem naive datetime)

**Frontend** (`apps/web`):
- `npx ng build` → OK (initial 158.62 kB transfer; cadastro-page 5.88 kB; orçamento ≤400kb gzip)
- `npm run lint` → All files pass linting
- `npm test` → **33 SUCCESS**
- `grep -rE "#E84E1B|#FAF6EE" apps/web/src --include="*.scss" | grep -v _tokens.scss` → 0 (Gate 2)

## @pytest.mark.mysql (rodar ao vivo contra MySQL 8)

```bash
cd apps/api
uv run alembic upgrade head        # aplica migration 0003 no MySQL real
uv run pytest -m mysql             # acceptance: append-only audit (0002) + UNIQUE composto merchants (0003)
uv run python -m tools.seed        # seed idempotente (rodar 2x não duplica) — verificar contagem
uv run pytest -m mysql tests/merchants/test_mysql_constraints.py -x
```
