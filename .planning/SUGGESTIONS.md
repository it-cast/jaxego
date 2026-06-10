# SUGGESTIONS — Jaxegô

> Insights do ingestor (2026-06-10) + futuras descobertas de execução promovidas das phases.

| ID | Sugestão | Contexto | Status |
|----|----------|----------|--------|
| SUG-001 | Implementar valores de planos/taxas como seeds parametrizados desde a Phase 4 | Todos os valores são `[ASSUMIDO]` (`visao-geral.md:45-54`); se o humano mudar os números após validação, não pode exigir deploy | proposta (já refletida em DRV-009) |
| SUG-002 | Antecipar o schema de ADR-103 (`effective_from/effective_until` em planos/taxas) para o M1, mesmo sem UI de edição | ADR-103 é v1.1, mas RN-030 + fatura mensal já precisam saber "qual taxa vigia na criação da entrega"; migrar depois custa mais que nascer certo | proposta (ver TD-013) |
| SUG-003 | Criar lint custom (ruff plugin ou teste) proibindo `datetime.now()` naive e `.replace(tzinfo=None)` em código de domínio | Lição auditada da v1.0 do grupo citada 2× nos docs (`regras.md:41`, `stack.md:58`) — vale automatizar em vez de confiar em revisão | proposta (ver TD-010) |
| SUG-004 | Tratar os 26 wireframes HTML como contratos verificáveis via `gsd-tools wireframe-contract` em toda phase de UI | Wireframes têm estados explícitos (empty/error/loading/warn) e data-actions — fidelidade enforced v0.9.7 já suportada (`wireframes/README.md:33-41`) | proposta |
| SUG-005 | Definir cedo (Phase 10) o comportamento do escrow se o Safe2Pay já retiver repasse de subconta | ADR-009 v2 menciona "ajustar escrow se o provedor já retiver" — se a retenção do PSP ≥ 24h, o escrow interno pode ser redundante (simplificação) ou aditivo (atraso duplo, ruim para o entregador) | aguarda OQ-3 |
| SUG-006 | Padronizar copy de erro/empty de TODAS as telas num arquivo de strings revisável contra brand.md + glossário | brand.md tem tabela tom-por-contexto rigorosa; centralizar evita deriva de vocabulário (ex.: "motoboy" escapando em string solta) | proposta |
| SUG-007 | No piloto, instrumentar desde a Phase 8 a métrica criação→aceite como histograma Prometheus | É o KPI norte secundário (<60s) e a meta de 6 meses depende dele; medir desde o primeiro despacho real | proposta |
