---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: completed
last_updated: "2026-06-10T21:30:00.000Z"
last_activity: 2026-06-10 — Phase 4 (cadastro de loja, F-01) executada. Backend E1–E4 + adapters/SSRF + seed + frontend wizard. 112 testes backend + 33 frontend verdes.
progress:
  total_phases: 14
  completed_phases: 4
  total_plans: 1
  completed_plans: 1
  percent: 29
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
- **Phase atual:** 4 of 14 — Cadastro e ativação de loja — ✅ EXECUTADA (verificação ao vivo MySQL pendente)
- **Próxima Phase:** 5 of 14 — Cadastro/KYC de entregador
- **Last activity:** 2026-06-10 — Phase 4 executada (F-01 completo no caminho Free + adapters/SSRF + seed + wizard).

**Progress:** [███░░░░░░░] 29%

## MS-01 — entregue

- **Phase 1:** monorepo, FastAPI `/health` (verificado ao vivo: 200), Docker Compose (api/worker/mysql/redis), Alembic, observabilidade, CI, guard naive datetime. 2 bugs runtime pegos no smoke ao vivo e corrigidos (cryptography, arq heartbeat).
- **Phase 2:** areas/users/area_admins/refresh_tokens/audit_log, auth JWT+refresh opaco+argon2id+TOTP+lockout, RBAC 6 papéis, isolamento multi-área, trigger append-only (verificado em MySQL 8 real: errno 1644). 69 testes.
- **Phase 3:** apps/web Angular 19 + Ionic 8, design system claro+dark (DEC-001) via tokens, componentes de estado, login → /v1/auth/login, shell 3 superfícies. ng build 155KB, 25 testes, zero hardcode.

## MS-02 — em andamento

- **Phase 4:** F-01 cadastro de loja no caminho Free. Backend: merchants/merchant_users/subscription_plans/merchant_subscriptions (migration 0003), service E1–E4 (CNPJ inativo, anti-enumeração, pago→pending_payment, Receita down→pending_validation), adapters Receita/SMS/SES/geocoding (Protocol+httpx+Stub+SSRF), OTP/job aware-UTC, seed idempotente. Frontend: wizard tela 02 (stepper, forms BR, persistência sem senha, E1/E2), estado vazio + captura de interesse, plano tela 16 data-driven, banners pending_* + onboarding. 112 testes backend (not-mysql) + 33 frontend, zero hex. TD-014/TD-015 registradas. **Verificação ao vivo MySQL pendente** (migration 0003, seed 2x, pytest -m mysql, cadastro E1–E4).

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
