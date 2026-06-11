# Phase 14 — Execution Log

## Wave 1 — LGPD + LLM infra + ETA (backend) · 2026-06-11

Executor: gsd-executor (Opus 4.8). Escopo: `apps/api`, Wave 1 (T-01, T-02, T-03).
Waves 2-3 (CI/APK/auditoria/checklist) NÃO executadas neste passo.

### T-01 — Jobs LGPD (REQ-048) ✓
- `app/workers/lifecycle.py`: `anonymize_inactive` (12m) + `delete_ephemeral` (30d),
  aware-UTC, idempotentes, best-effort por linha, auditados (`audit_log`).
- Anonimização irreversível: nome→placeholder, cpf/cpf_hash→tombstone, phone→null/tombstone
  (colunas NOT NULL), email→tombstone; `anonymized_at` carimbado; agregados preservados.
- Retenção legal (D-02): courier/user com trilha financeira (`escrow_ledger`,
  `direct_payment_confirmations`, `payment_disputes`) nunca anonimizado.
  (`platform_charges` não tem `courier_id` — link via delivery/escrow.)
- `delete_ephemeral`: signups abandonados (>30d, inativos, sem vínculo area/merchant/courier,
  sem trilha financeira) + refresh tokens vencidos → hard-delete.
- Registrados em `WorkerSettings.cron_jobs` (03:30 / 03:50 UTC).
- Testes (`tests/workers/test_lgpd.py`, dados sintéticos, clock controlado): 7 passando.
- Commit: `57c03af`.

### T-02 — Infra LLM (REQ-053) ✓ — SÓ INFRA, sem feature/endpoint
- `app/ai/`: `LLMProvider` Protocol + `LLMResult` + `TaskClass`; `StubProvider`
  determinístico; `ClaudeAdapter` (SDK anthropic lazy-import — TD-14-01); `LLMRouter`
  (REASONING→opus, BULK→haiku, D-03); `factory` (Stub em dev/test/M1).
- Migration `0012_ai_usage_log`: tabela GLOBAL (ADR-001, sem `area_id`), reversível.
  Sem PII (provider/model/task/tokens/custo/latência/request_id/ok/error_kind).
- Settings: `ANTHROPIC_API_KEY` só em env/secret (TH-01, nunca log); `llm_provider='stub'`
  default → nenhum endpoint de IA montado no M1.
- Testes (`tests/ai/test_router.py`): 6 passando; reversibilidade da migration
  (`tests/ai/test_migration_0012.py`) marcada `@pytest.mark.mysql` (não roda em -m 'not mysql').
- Commit: `628bda1`.

### T-03 — Refino fallback ETA (REQ-054) ✓
- `app/deliveries/eta.py`: `EtaResolver` envolve `RoutingPort` (OSRM httpx já degrada +
  timeout 5s) com circuit breaker (abre após N falhas, cool-off, half-open). Nunca
  levanta, nunca bloqueia criação (D-04/TH-08). Métrica `eta_source` (osrm|fallback)
  via structlog, sem PII.
- Ponto de extensão formalizado (TD-14-02): preço ainda usa a estimativa mediana intocada.
- Testes (`tests/deliveries/test_eta_fallback.py`, clock controlado): 5 passando.
- Commit: `6e3c542`.

### Verificação
- `uv run pytest -m "not mysql"`: **472 passed, 22 deselected** (inclui 18 testes novos +
  migration 0012 deselecionada). 0 falhas.
- `uv run ruff check .`: **All checks passed**.
- A falha pré-existente conhecida de `tests/test_health.py` (flaky/capsys) passou neste run.

### Desvios / notas
- `ai_usage_log` definido SEM `area_id` (instrução explícita "GLOBAL, sem area_id — ADR-001"),
  divergindo de um comentário do mixin que listava a tabela como global mas mencionava
  `area_id` em outras globais — seguida a instrução literal da task.
- `PlatformCharge` não tem `courier_id` (descoberto em leitura): retenção legal por courier
  usa `EscrowLedger`/`DirectPaymentConfirmation`/`PaymentDispute` (Rule 1 — correção factual).
- TDs registradas: TD-14-01 (SDK anthropic deferido), TD-14-02 (ETA rodoviário não consumido).

### TDD gate
Plano não é `type: tdd`; tasks `type=auto`. Cada task entregou código + testes no mesmo commit
de feature (`feat(14): ...`), com testes inclusos. Sem violação de gate.
