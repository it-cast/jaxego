# EXECUTION-LOG — Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2

> Executor único (sequencial, apesar do parallel-hint back-front). Backend primeiro
> (até fixar contrato), depois componentes/frontend, depois wiring. Commit atômico
> por task. Stubs em CI (B2/Receita/SMS) — nenhum toca rede real.

**Início:** 2026-06-10T19:56:42Z

## Wave 1 — backend foundation + componentes

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| T-01 | Deps boto3+Pillow + config segredos B2 + .env.example | `a78acb6` | import OK; b2_key_id=None (segredo só env) |
| T-02 | Migration 0004 + models couriers/courier_documents | (segundo commit) | unique (area_id,cpf) E2; índices; test_models 4 passed |
| T-03 | Pipeline mídia: magic bytes + Pillow WebP + strip EXIF + SHA-256 | (terceiro) | test_reprocess 7 passed (extensão falsa, EXIF zerado, resize, bomb) |
| T-04 | StoragePort + Stub FS + StorageB2Adapter (spike LOW-1) | (quarto) | test_storage_stub 5 passed (test_no_public_access) |
| T-07 | jx-doc-upload + jx-doc-card (componentes) | (frontend-1) | specs a11y/E4; stories baseline; zero hex |
| T-08 | jx-kyc-queue-table + jx-kyc-review-row | (frontend-1) | specs E5/reprovar-sem-motivo; stories |

## Wave 2 — backend fluxo

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| T-05 | Router/service signup + documentos (presign + complete) + admin | (quinto) | wizard E1, signup E2 mesma/outra área, documents, authz IDOR 404 (16 passed) |
| T-06 | KYC item-a-item + máquina de estados + MEI | (sexto) | E4 reprovar CNH não invalida selfie; 422; E3 mei_pending (28 passed) |
| T-09 | Jobs aware-UTC: expiração + escalação 48h | (sétimo) | clock fake: vencido transita, naive coerced; >=48h escala (10 passed) |

## Wave 3 — frontend wiring

| Task | Descrição | Commit | Resultado |
|------|-----------|--------|-----------|
| T-10 | Wizard entregador (tela 03, Ionic) | (frontend-2) | stepper condicional 3/4; draft sem senha (E1); upload presign background |
| T-11 | Painel admin KYC detalhe (tela 19) | (frontend-2) | review item-a-item otimista; CPF mascarado; Score placeholder inerte |
| T-12 | Estados especiais pending_kyc + banner mei_pending | (frontend-2) | em-análise sem confete; banner permanente RN-024 |

## Verificação final (gate 7)

**Backend** (`apps/api`):
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 131 files already formatted
- `uv run basedpyright` → 0 errors, 0 warnings, 0 notes
- `uv run pytest -m "not mysql"` → **179 passed, 5 deselected**

**Frontend** (`apps/web`):
- `npx ng build` → OK; initial 594.69 kB raw / **160.26 kB transfer** (< 400 kB gzip budget); cadastro/kyc-detalhe/em-analise lazy
- `npx ng lint` → All files pass linting
- `npx ng test --watch=false` → **46 SUCCESS**
- grep `#E84E1B|#FAF6EE` em `*.scss` (exceto `_tokens.scss`) → **0**; grep hex geral nos arquivos novos → **0**

## A rodar ao vivo (MySQL 8) — `@pytest.mark.mysql`

- `tests/couriers/test_models.py::test_fk_restrict_area_delete_blocked` — FK RESTRICT (SQLite não enforce).
- Reversibilidade migration: `cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head`
- Comando: `cd apps/api && uv run pytest -m mysql`

## Integration check (Gate 5) — pendente conta B2 real

- StorageB2Adapter (boto3 S3v4, addressing_style=path) validado só por contrato (Stub) em CI.
- Presign PUT/GET reais contra `jaxego-kyc-prod` → validar antes de `/gsd:verify-work` (LOW-1).
