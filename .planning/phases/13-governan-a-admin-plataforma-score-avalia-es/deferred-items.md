# Deferred items — Phase 13 (descobertas fora de escopo)

## Pré-existente (NÃO causado pela Phase 13)

- **`tests/test_health.py::test_health_logs_request_with_required_fields` — flaky sob suíte completa.**
  Falha quando rodado na suíte inteira (interferência de captura de stdout/structlog entre
  testes), mas **passa isolado**. Já falhava no baseline ANTES de qualquer mudança da Phase 13
  (verificado: 428 passed / 1 failed antes; 453 passed / 1 failed depois — mesmo teste).
  É um teste de logging da Phase 1, não tocado por esta phase. Fora de escopo (Scope boundary).
  Sugestão de fix futuro: usar `structlog.testing.capture_logs()` em vez de `capsys`
  (mesmo padrão já aplicado no teste de reversão SLA da Phase 13).
