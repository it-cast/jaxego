# PLAN — Phase {N} Plan {NN-NN}: {nome}

> Gerado por `gsd-planner` em {date}.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

{1-2 linhas descrevendo o objetivo executável deste plano}

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] {critério 1, verificável via teste ou inspeção}
- [ ] {critério 2}
- [ ] {critério N}
- [ ] Todos os testes relacionados passam (`make test`)
- [ ] Lint limpo (`make lint`)
- [ ] Commit atômico com mensagem padronizada

## REQs referenciados

- REQ-{id} — {descrição resumida do REQUIREMENTS.md}

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano. Citar skill sem aplicação concreta é inválido (plan-checker flaga).

- `{skill-name}` — {task-id(s)}: {regra(s) específica(s) aplicadas}
- `{skill-name}` — {task-id(s)}: {regra(s) específica(s) aplicadas}

## Skills Dispensadas (com justificativa)

Skills que o plan-checker pode sinalizar como "esperadas" mas que não se aplicam a este plano — explicar por quê:

- `{skill-name}` — {razão técnica explícita}

---

## Tech debt deste plano (verificação obrigatória v0.8+)

**Antes de gerar este PLAN.md**, abrir `.planning/TECH-DEBT.md` e listar TDs com:

- `Prazo (Phase)` igual à phase atual, OU
- `urgency_class: pre_launch_blocker` se esta phase é a última antes do launch, OU
- `urgency_class: pre_launch_high` se esta phase está no caminho de launch

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-XX-XX | ... | ex: "prazo Phase 9 == phase atual" | T-NN |
| TD-XX-XX | ... | ex: "deferido — revisitar Phase 11" (justificar) | — |

Se nenhuma TD se aplica: declarar explicitamente `N/A — TECH-DEBT.md não tem itens com prazo nesta phase`.

**Diagnóstico v0.7.x** detectou que TDs com prazo definido eram esquecidas porque o plan-phase
não consultava TECH-DEBT.md. Esta seção fecha esse gap.

---

## Open questions / LOW confidence do RESEARCH (obrigatório se RESEARCH tem itens LOW)

Se `RESEARCH.md` desta phase tem `### Open Decisions` ou itens marcados como `confidence: LOW`,
cada um vira **task explícita** ou **decisão consciente de adiar**:

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| ex: "apple-actions @v3 floating tag — verificar antes de tag push" | LOW | Task T-NN: `verify-action-resolution.sh` antes do primeiro release |
| ex: "Sentry DSN injection deferida" | LOW | Adiada — TD-NN registrada com prazo Phase {N+2} |

Se sem itens LOW: `N/A — RESEARCH.md sem itens com confidence LOW`.

**Diagnóstico v0.7.x:** itens LOW confidence ficavam no RESEARCH.md e desapareciam do radar.
Esta seção força destino estruturado: ou vira task, ou vira tech debt formal.

---

## Threat model

Preenchido com base na seção `## Security Baseline` do `RESEARCH.md` (obrigatória para fases com endpoint/auth/PII). Se esta fase não tem risco de segurança, declarar explicitamente.

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task que implementa |
|----|--------|-------|---------|------------|-----------|---------------------|
| TH-01 | {ex: CSRF em form de auth} | POST sem origin check | Alto | Médio | Double-submit cookie + SameSite=Strict | T-03 |
| TH-02 | ... | ... | ... | ... | ... | ... |

Se sem risco: `N/A — este plano não toca endpoint, autenticação ou PII.`

---

## Performance budget (obrigatório para fases com UI ou endpoint)

Herdado de `.planning/config.json > performance_budget`. Override local se necessário:

**Frontend** (se aplicável):
- LCP ≤ {ms}
- INP ≤ {ms}
- CLS ≤ {val}
- Bundle main.js ≤ {kb} gzip
- Lazy loading: {rotas que devem ser lazy}

**Backend** (se aplicável):
- p95 de latência por endpoint ≤ {ms}
- p99 ≤ {ms}
- N+1 queries: zero toleradas em endpoints de listagem
- Connection pooling dimensionado para {N} req/s simultâneos

Ferramenta de medição:
- Frontend: Lighthouse CI no pipeline
- Backend: pytest-benchmark em testes críticos, Prometheus em prod

Se N/A: `N/A — este plano é {migration / refactor interno / etc.}`

---

## Observability checklist (obrigatório para fases com endpoint ou background job)

Aplicando skill `observability-production`:

- [ ] Todo endpoint novo loga: `request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms`
- [ ] Erros 4xx logados como WARNING
- [ ] Erros 5xx logados como ERROR + alert no canal de monitoramento
- [ ] Queries > {threshold_ms}ms logadas com WARNING
- [ ] Zero PII em logs (nada de cpf/email/password/token em campo de log)
- [ ] `/healthz` endpoint atualizado se serviço novo

Se N/A: `N/A — este plano é {frontend-only / refactor de teste / etc.}`

---

## Error UX checklist (obrigatório para fases com UI)

Aplicando skill `error-ux-patterns`:

- [ ] Todo estado de erro tem mensagem específica (não "Algo deu errado")
- [ ] Todo erro tem ação de recuperação (retry, botão de suporte, link)
- [ ] Erros de validação inline ao blur, não modal ao submit
- [ ] Erros de rede com retry automático + feedback visual
- [ ] 404 customizado (se fase tem rota que pode 404)
- [ ] Toast vs modal vs inline: decisão consistente documentada

Se N/A: `N/A — este plano é backend-only ou não toca UI de erro.`

---

## Integration contracts (obrigatório se fase tem `integration_check` no ROADMAP)

Contratos cross-layer validados pelo `gsd-integration-checker` após execução:

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| POST /{resource}/{id}/{action} | apps/{client}/{path}:L{N} | backend/api/{module}.py:L{N} | body tem `{campo1, campo2}`, resposta tem `{campo_id, status}` |
| ws://{host}/api/v1/ws/{channel} | apps/{client}/core/websocket.service.ts | backend/ws/{module}.py | URL inclui prefixo `/api/v1/`, reverse proxy correto |

Se N/A: `N/A — este plano é single-layer.`

---

## Tasks

Formato estruturado — cada task tem skills aplicadas e critério de sucesso isolado.

### T-01 — {título}

- **Type:** {new_endpoint | ui_component | migration | test | refactor | infra}
- **Files:** {lista de arquivos a tocar}
- **Skills aplicadas:**
  - `{skill}` — {regra específica}
  - `{skill}` — {regra específica}
- **Descrição:** {2-3 linhas}
- **Success:** {critério verificável}
- **Estimate:** {horas}
- **Depends on:** {task IDs ou `none`}

### T-02 — ...

---

## Execution order

Waves (grupos paralelizáveis):
- **Wave 1 (paralelo):** T-01, T-02 (sem dependência)
- **Wave 2:** T-03 (depende de T-01), T-04 (depende de T-02)
- **Wave 3:** T-05 (depende de T-03 + T-04)

---

## Reconciliation expectations

Ao fim da execução, o `/gsd-reconcile-state {N}` verifica:

- Todos os arquivos listados em `files` de cada task existem
- Todos os endpoints declarados têm handler implementado
- Todas as skills citadas foram de fato aplicadas (ex: rate limit realmente presente)
- Nenhum arquivo-fantasma
- Nenhuma feature fantasma (código sem task correspondente)

Divergências entram em `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

Se este plano causar regressão em produção, rollback:
- Revert do commit `feat(phase-{N}/plan-{NN-NN}): ...`
- {Migrations específicas a reverter, se houver}
- {Ações de ops específicas, ex: cache invalidation, feature flag off}

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
- Integration contracts: {presente | N/A | incompleto}
- Revision iteration: {1 | 2 | 3 | final}
