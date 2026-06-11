# Phase 13: Governança - Research

**Status:** Ready for planning · **Date:** 2026-06-11 (autopilot)

## Achados técnicos

### 1. Score explicável (REQ-020) — snapshot diário
- Tabela `courier_score_snapshots` (area-scoped): `courier_id`, `snapshot_date`, `total_score`,
  `level` (enum probation/bronze/prata/ouro/diamante), `components` JSON (cada componente: nome,
  valor_bruto, peso, contribuição). Pesos vêm de seed parametrizado `score_weights` (DRV-009).
- Job arq diário `snapshot_scores` (aware-UTC, idempotente — 1 snapshot por (courier, dia)). Lê
  sinais já existentes: taxa de aceite (dispatch), pontualidade/comprovação (proofs), cancelamentos
  (deliveries), avaliações (novo). **Não** escreve em ranking de despacho (ADR-013 — isolamento
  verificável: `app/dispatch/ranking.py` não importa score).
- **Confidence: HIGH** (snapshot é padrão simples; sinais já existem).

### 2. Avaliações (REQ-033)
- `courier_ratings` (area-scoped, UNIQUE por `delivery_id` → 1 avaliação/entrega). Loja avalia após
  FINALIZADA (1-5 + comentário opcional). Endpoint escopado por merchant_scope (só a loja da entrega).
- **Confidence: HIGH**.

### 3. Suspensão / recurso com reversão automática (REQ-045)
- Reusa estados `suspended` (courier/merchant). Nova tabela `suspension_appeals`: `subject_type`,
  `subject_id`, `area_id`, `reason`, `opened_at`, `sla_due_at`, `decision` (null/upheld/overturned),
  `decided_at`, `decided_by`. Suspensão sempre via audit_log (before/after).
- Job arq `enforce_appeal_sla`: appeals sem decisão com `sla_due_at < now` → **reverte** subject para
  active (transição auditada) + emite **alerta** (structlog + métrica). Idempotente.
- **Confidence: MED** — a reversão automática precisa de teste de SLA com clock controlado (LOW-1).

### 4. Admin de plataforma (REQ-046) — telas 23-25
- `require_platform_admin` já força TOTP (ADR-005) — verificação "admin sem TOTP → bloqueado" já
  garantida. Novo módulo `app/platform_admin/` com endpoints cross-área **read-mostly**: visão geral
  de áreas/volumes, busca de entregadores/lojas cross-área (com score), lista global de disputas/
  suspensões. **Cada acesso cross-área sensível gera audit_log** (A01/RN-012).
- **Confidence: HIGH** (gate de TOTP e audit já existem).

### 5. Revenue share parametrizado (REQ-047 `[DECIDIR %]`)
- Superfície de config `area_revenue_share` (valor `[ASSUMIDO]`, seed editável, versionável tipo
  ADR-103 effective_from). **Não** calcula/move dinheiro nesta phase. OQ-1 = dado do dono.
- **Confidence: HIGH** (é config, não cálculo).

### 6. Disputas no admin de área (REQ-044 completo)
- UI lista `payment_dispute` (Phase 9) + suspensões da área; registra decisão administrativa
  auditada. **Consequência financeira deferida à Phase 15** (DEC-004) — aqui é triagem + registro.
- **Confidence: HIGH**.

## Security Baseline (Gate 4 — owasp-security)

> Admin de plataforma com poder cross-área + ações de suspensão → baseline obrigatório.

| # | Ameaça | Mitigação nesta phase |
|---|---|---|
| TH-01 | Admin plataforma sem MFA (A07) | `require_platform_admin` já exige TOTP enrolled; sem TOTP → bloqueado (ADR-005) |
| TH-02 | Acesso cross-área indevido / vazamento (A01) | toda leitura cross-área do platform_admin gera audit_log; admin de área NUNCA acessa outra área (escopo mantido) |
| TH-03 | Suspensão/banimento abusivo ou silencioso | toda suspensão/reversão via audit_log append-only (before/after + motivo + ator); trigger MySQL impede UPDATE/DELETE |
| TH-04 | Escalonamento de privilégio (A01) | `require_role`/`require_platform_admin` em todos os endpoints; admin de área não chama rotas de plataforma |
| TH-05 | Score manipulável | score é snapshot derivado de sinais auditáveis; sem endpoint de escrita direta de nota; pesos em seed (não input do usuário) |
| TH-06 | Injection em busca/filtro global (A03) | filtros via params validados (Pydantic), SQLAlchemy bound; paginação por cursor |
| TH-07 | PII em log (A09) | breakdown de score e disputas sem CPF/telefone em log; campos proibidos já no config |
| TH-08 | Reversão de SLA não-determinística | job idempotente aware-UTC; teste com clock controlado (LOW-1) |

## LOW confidence → tasks (Regra 12)
- **LOW-1:** reversão automática por SLA precisa de teste com clock controlado → **Task explícita**
  (critério: appeal vencido sem decisão → subject volta a active + alerta emitido; appeal decidido
  no prazo → sem reversão).

## Skills aplicáveis
- `owasp-security` (baseline) · `quality/observability-production` (alerta SLA, audit) ·
  `ux-advanced/saas-dashboard-patterns` · `data-tables-ux` · `search-filter-ux` · `trust-safety-ux`
  (suspensão com recurso) · matriz UI + `br/ux-copywriting-ptbr` · `domain/mysql-schema-design`
