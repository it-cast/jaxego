# TECH-DEBT — Jaxegô

> Toda entry exige `urgency_class` (Regra 11): `pre_launch_blocker` | `pre_launch_high` | `pre_launch_medium` | `post_launch_30d` | `post_launch_quarter` | `wont_fix_documented`.
> Promoção entre classes requer ADR ou entry em DECISIONS.md.
> Dívidas abaixo já nascem conhecidas — extraídas dos documentos de origem pelo ingestor em 2026-06-10.

| ID | Descrição | Por quê (consciente) | urgency_class | Owner | Prazo / gatilho | Plan a resolver |
|----|-----------|----------------------|---------------|-------|-----------------|-----------------|
| TD-001 | Sharding do banco não implementado — multi-área lógico em 1 MySQL | Suficiente até 50 áreas de alto volume (`stack.md:57`); custo de sharding injustificado no M1 | wont_fix_documented (revisar no gatilho) | backend | >50 áreas de alto volume | ADR futura de particionamento |
| TD-002 | Nível de validação exigido por área pode ficar defasado (compliance) | ADR-102 trava o gatilho: 3ª área ativa OU 90 dias de operação dispara revisão | post_launch_quarter | admin plataforma | 3ª área OU M1+90d | Processo de revisão por área (v1.1) |
| TD-003 | OTP de comprovação visível porém desabilitado ("em breve") na UI | Decisão de escopo: OTP pós-M1 (ADR-008); badge evita retrabalho de UI | post_launch_quarter | frontend | v1.1 | Implementar RN-007 server-side |
| TD-004 | Score coletado/exibido sem consequência financeira | ADR-013: precisa de 90 dias de dados reais antes de aplicar consequência (risco PLP 152) | post_launch_quarter | produto | v1.1 (M1+90d) | ADR de consequências com base estatística |
| ~~TD-005~~ | ~~Tracking público sem mapa em tempo real~~ **CANCELADA por DEC-002 (2026-06-10): mapa em tempo real entrou no escopo do M1 (Phase 9). Não é mais dívida** | — | resolved | fullstack | — | Entregue na Phase 9 (ADR-101 promovida) |
| TD-006 | APK por distribuição direta (fora da Play Store) | Decisão M1 (ADR-003); lojas oficiais + iOS no M2 | post_launch_30d | mobile | M2 | Publicação Play Store; iOS |
| TD-007 | Corrida parcial em acidente/imprevisto avaliada manualmente pelo admin (F-06 E5) | Volume do M1 não justifica automação; admin local resolve melhor | post_launch_quarter | produto | v1.1 | Política automatizada com dados de casos reais |
| TD-008 | Infra de LLM presente sem nenhuma feature (router + ai_usage_log) | Decisão explícita: features de IA pós-M1 (`integracoes.md:99-102`) | wont_fix_documented | backend | pós-M1 | Triagem de disputas e antifraude de foto na v1.1+ |
| TD-009 | Estimativa de frete (RN-030) usa mediana simples — sem aprendizado de demanda | `[ASSUMIDO]` aguardando validação; mediana é suficiente para liquidez do piloto | post_launch_quarter | backend | v1.1 | Reavaliar com dados de 90 dias |
| TD-010 | Naive datetime: risco recorrente auditado na v1.0 do grupo (`grace_boundary.replace(tzinfo=None)`) | Lição de campo citada em `regras.md:41` e `stack.md:58` — exige vigilância contínua, não é fix pontual | pre_launch_high | backend | Toda phase com timestamps (2, 7, 9, 10, 11) | Lint/teste custom proibindo naive datetime em domínio |
| TD-011 | Broadcast de despacho indisponível (cascata only) | RN-009: broadcast é opt-in pós-M1; nunca default | wont_fix_documented | produto | pós-M1 | Opt-in por entrega quando houver demanda |
| TD-012 | Mensalidade do entregador desligada e sem valor definido | `[DECIDIR]` OQ-2; modelo de receita 3 fica inativo no M1 | post_launch_quarter | negócio | quando uma área quiser ativar | Decisão de pricing + toggle por área |
| TD-013 | Taxas sem versionamento temporal no M1 (mudança de taxa exige cuidado manual) | ADR-103 é v1.1; ver SUG-002 (antecipar schema) | pre_launch_medium | backend | Phase 10 decide | Adotar `effective_from/until` já no schema inicial |
