---
gsd_state_version: 1.0
milestone: MS-02
milestone_name: Cadastros + área operável
status: in_progress
last_updated: "2026-06-10T20:10:00.000Z"
last_activity: 2026-06-10 — Phase 5 (cadastro/KYC do entregador, F-02) EXECUTADA. Backend couriers/courier_documents + upload B2 presigned + reprocess server-side (magic bytes/WebP/strip EXIF/SHA-256) + KYC item-a-item + MEI mei_pending + jobs aware-UTC. Frontend wizard Ionic + painel admin + 4 componentes. 179 backend (not-mysql) + 46 frontend verdes. Pendente ao vivo: MySQL (migration 0004 + FK RESTRICT) + integration check B2 (Gate 5).
progress:
  total_phases: 14
  completed_phases: 5
  total_plans: 5
  completed_plans: 5
  percent: 36
---

# STATE — Current Execution State

> Documento vivo. Claude Code lê ao iniciar sessão. Atualiza ao fechar plano.
> Populado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/` (36+ arquivos).

---

```yaml
milestone: MS-02
milestone_name: Cadastros + área operável
status: in_progress
release_target: v1.0 (piloto Pádua)
progress:
  total_phases: 14
  completed_phases: 4
  percent: 29
```

## Project Reference

See: `.planning/PROJECT.md` (ingest em 2026-06-10)

**Core value:** Malha de entregadores por área para o interior do Brasil, integrada ao Menu Certo, com pagamento direto como modalidade de 1ª classe.
**Current focus:** MS-01 (Fundação) completo. Próximo milestone: MS-02 (cadastros + área operável) — começa pela Phase 4 (cadastro de loja).

## Current Position

- **Milestone:** MS-02 (Cadastros + área operável) — em andamento
- **Phase atual:** 5 of 14 — Cadastro do entregador + KYC 2 níveis + documentos B2 — ✅ EXECUTADA (verificação ao vivo MySQL + integration check B2 pendentes)
- **Próxima Phase:** 6 of 14 — Cobertura/bairros + tabela de frete
- **Last activity:** 2026-06-10 — Phase 5 executada (F-02: couriers/KYC item-a-item + upload B2 presigned + reprocess server-side + MEI mei_pending + jobs aware-UTC + wizard Ionic + painel admin).

**Progress:** [████░░░░░░] 36%

## MS-01 — entregue

- **Phase 1:** monorepo, FastAPI `/health` (verificado ao vivo: 200), Docker Compose (api/worker/mysql/redis), Alembic, observabilidade, CI, guard naive datetime. 2 bugs runtime pegos no smoke ao vivo e corrigidos (cryptography, arq heartbeat).
- **Phase 2:** areas/users/area_admins/refresh_tokens/audit_log, auth JWT+refresh opaco+argon2id+TOTP+lockout, RBAC 6 papéis, isolamento multi-área, trigger append-only (verificado em MySQL 8 real: errno 1644). 69 testes.
- **Phase 3:** apps/web Angular 19 + Ionic 8, design system claro+dark (DEC-001) via tokens, componentes de estado, login → /v1/auth/login, shell 3 superfícies. ng build 155KB, 25 testes, zero hardcode.

## MS-02 — em andamento

- **Phase 4:** F-01 cadastro de loja no caminho Free. Backend: merchants/merchant_users/subscription_plans/merchant_subscriptions (migration 0003), service E1–E4 (CNPJ inativo, anti-enumeração, pago→pending_payment, Receita down→pending_validation), adapters Receita/SMS/SES/geocoding (Protocol+httpx+Stub+SSRF), OTP/job aware-UTC, seed idempotente. Frontend: wizard tela 02 (stepper, forms BR, persistência sem senha, E1/E2), estado vazio + captura de interesse, plano tela 16 data-driven, banners pending_* + onboarding. 112 testes backend (not-mysql) + 33 frontend, zero hex. TD-014/TD-015 registradas. ✅ verificada ao vivo MySQL.
- **Phase 5:** F-02 cadastro/KYC do entregador. Backend: couriers/courier_documents (migration 0004, AreaScoped, unique (area_id,cpf) → E2), StoragePort (Protocol+Stub FS+B2 boto3 S3v4) com presigned PUT/GET, pipeline media (magic bytes + Pillow WebP + strip total EXIF + SHA-256 do derivado, anti-bomb), endpoints /v1/couriers/* (signup público rate-limited, presign, complete, MEI) + /v1/admin/couriers/* (view-url, PATCH review item-a-item), máquina de estados dupla (422), KYC 2 níveis RN-002, MEI mei_pending RN-024 (E3), jobs aware-UTC (expiração + escalação 48h E5). Frontend: jx-doc-upload/jx-doc-card/jx-kyc-queue-table/jx-kyc-review-row (stories + a11y), wizard Ionic tela 03 (stepper condicional 3/4, draft sem senha E1, upload presign background), painel admin tela 19 (review otimista, CPF mascarado, Score placeholder), em-análise + banner mei_pending. **179 testes backend (not-mysql) + 46 frontend, zero hex.** TD-016 (antivírus PDF) registrada. **Pendente ao vivo:** migration 0004 reversível + FK RESTRICT (`pytest -m mysql`) + integration check B2 (Gate 5, conta real).

## Atenção para MS-02+

1. **OQ-3 (contrato Safe2Pay) bloqueia a Phase 10** — resolver antes de chegar lá; Phases 4–9 podem prosseguir.
2. **OQ-1 (revenue share admin de área)** — idealmente decidir antes da Phase 10/13.
3. Valores de planos/taxas são `[ASSUMIDO]` — implementar parametrizado (seeds), nunca hardcoded.
4. **Seed de admin de plataforma** ainda não existe — necessário para smoke de login end-to-end e provavelmente para a Phase 4 (onboarding de loja).
5. Sem GitHub remote configurado — CI não validado em execução remota (item de release).

## Próximo passo

```
# Verificar Phase 4 ao vivo (MySQL real) — ver EXECUTION-LOG da Phase 4:
cd apps/api && uv run alembic upgrade head && uv run pytest -m mysql && uv run python -m tools.seed

# Depois:
/gsd:reconcile-state 4      # reconciliação prometido vs. código
/gsd:discuss-phase 5        # Cadastro/KYC de entregador
```
