# Agent Orchestration — GSD + agentes especializados

> Referência normativa. Define como workflows GSD invocam agentes orchestrator para fazer trabalho pesado em paralelo, mantendo gates e enforcement centralizados no GSD.

## Princípio central

**GSD não substitui agentes. Orquestra eles.**

- **GSD** = camada de processo (gates, skills enforcement, reconcile, métricas)
- **Agentes orchestrator** = camada de execução (implementação paralela especializada)

Um sem o outro perde valor:
- GSD sem agentes = processo rigoroso, mas execução serial e lenta
- Agentes sem GSD = rápido, mas sem disciplina — hex hardcoded, skill ignorada, PLAN fantasioso

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│  HUMANO                                         │
│  /gsd-plan-phase sprint-03                      │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│  GSD WORKFLOW (plan-phase.md)                   │
│  ┌──────────────────────────────────────────┐   │
│  │  Gate 1: bootstrap ok?                   │   │
│  │  Gate 2: Visual Contract válido?         │   │
│  └──────────────────────────────────────────┘   │
│                   │                             │
│                   ↓ (paralelo, se configurado)  │
│  ┌───────────────┬───────────────┬───────────┐  │
│  │ AGENT         │ AGENT         │ AGENT     │  │
│  │ backend-      │ frontend-     │ ui-ux-    │  │
│  │ architect     │ developer     │ designer  │  │
│  │               │               │           │  │
│  │ desenha       │ propõe        │ valida    │  │
│  │ endpoints +   │ componentes   │ UX flow   │  │
│  │ schema        │               │           │  │
│  └───────┬───────┴───────┬───────┴─────┬─────┘  │
│          │               │             │        │
│          └───────┬───────┴─────────────┘        │
│                  ↓                              │
│  ┌──────────────────────────────────────────┐   │
│  │  Planner consolida em PLAN.md            │   │
│  │  Gate 3: skills citadas corretamente?    │   │
│  │  Gate 4: security baseline ok?           │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

GSD invoca, GSD valida, GSD arquiva. Agentes são braços, não cérebro do processo.

## Agentes orchestrator típicos

Nomes variam por instalação. Os mais comuns e suas responsabilidades em termos GSD:

| Agente | Fase GSD onde é invocado | O que produz |
|--------|--------------------------|--------------|
| `backend-architect` | plan-phase | Endpoints, schemas, migrations esboço |
| `backend-developer` | execute-phase | Implementação de endpoints + testes |
| `frontend-developer` | execute-phase | Implementação de componentes + páginas |
| `ui-ux-designer` | ui-phase | Flow review, validação de copy, a11y |
| `mobile-developer` | execute-phase (se mobile) | Implementação Ionic/RN + Capacitor |
| `test-writer` | execute-phase | Testes unitários + integration |
| `security-reviewer` | plan-phase (gate 4) | Baseline de segurança, validação OWASP |
| `performance-analyst` | ui-phase / post-execute | Análise de Core Web Vitals, bundle |
| `api-designer` | plan-phase | Contratos de API, OpenAPI |
| `database-architect` | plan-phase | Schema design, migrations |
| `devops-engineer` | execute-phase | CI/CD, deploy |
| `docs-writer` | post-execute | Documentação, ADRs |

**Se você não tem esses agentes instalados:** os workflows GSD continuam funcionando com Claude principal executando inline — mais lento, mas funcional. Ver `fallback_mode` abaixo.

## Como workflows invocam agentes

### Padrão básico (um agente)

Workflow passa contexto estruturado e coleta output:

```markdown
# Em plan-phase.md, Gate 5 (planning)

[INVOKE backend-architect]
context:
  sprint_id: {sprint_id}
  sprint_narrative: {ler de SPRINT.md > Narrativa}
  visual_contract: {ler de SPRINT.md > Visual Contract}
  existing_tables: {ler de specs/database.yaml}
  existing_endpoints: {grep em backend/app/api/*.py}
task: "Para este sprint, proponha: (a) tabelas novas ou alteradas, (b) endpoints novos
com response_model, (c) error codes novos. Não escreva código — descreva contrato.
Aplique skill product/api-design-contracts."
output: PLAN.md > sections [Backend Architecture, Endpoints, Migrations]
```

Output do agente entra no PLAN.md. Gate 3 posterior valida skill coverage no texto consolidado.

### Padrão paralelo (múltiplos agentes)

Para sprints que tocam várias camadas, rodar em paralelo conforme `config.json > parallelization`:

```markdown
# Em plan-phase.md, se parallelization.enabled && tasks_span_multiple_areas

[PARALLEL INVOKE]
  - backend-architect
  - frontend-developer  
  - ui-ux-designer

shared_context:
  sprint_id: {sprint_id}
  sprint_file: {path to SPRINT.md}

max_concurrent: {config.parallelization.max_concurrent_agents}  # default 3

[WAIT all complete]

[MERGE outputs into single PLAN.md]
conflict_resolution:
  - if backend-architect says X and frontend-developer assumes Y that contradicts X → ESCALATE to human
  - if ui-ux-designer flags a11y issue → BLOCK PLAN até resolver
```

**Crítico:** não rodar paralelo se as propostas têm **dependências fortes**. Ex: componente frontend depende do shape da response do endpoint — primeiro backend, depois frontend.

### Padrão de delegação (workflow → subworkflow via agente)

Para trabalhos grandes, um agente pode rodar sub-ciclos:

```
plan-phase → invoca api-designer
  api-designer internamente faz:
    - lê specs existentes
    - desenha OpenAPI
    - valida contra api-design-contracts skill
    - produz artifact
  retorna artifact ao workflow pai
```

## Integração com skills

**Agentes invocados carregam as skills relevantes no contexto.** Exemplo do `plan-phase`:

```markdown
[INVOKE backend-architect]
skills_to_load:
  - product/api-design-contracts
  - quality/observability-production
  - quality/error-ux-patterns  # para error codes
  - br/brazilian-forms  # se envolve CPF/CNPJ/CEP
```

Agente recebe o contéudo dessas skills como parte do prompt. Produz output que **deve** aderir às regras.

**Skill-load matrix** por tipo de agente (resumo):

| Agente | Skills default carregadas |
|--------|---------------------------|
| `backend-architect` | `api-design-contracts`, `observability-production`, `error-ux-patterns` |
| `frontend-developer` | `component-library-governance`, `accessibility-pro`, `error-ux-patterns`, `ux-copywriting-ptbr` |
| `mobile-developer` | `offline-first`, `accessibility-pro`, `push-notifications-architecture` |
| `ui-ux-designer` | `accessibility-pro`, `ux-copywriting-ptbr`, `error-ux-patterns`, `micro-animations-delight` |
| `test-writer` | `visual-regression-testing`, skills citadas no PLAN.md |
| `security-reviewer` | `owasp-security`, `lgpd-compliance`, `observability-production` |

Matriz customizável em `.planning/config.json > agent_skills`.

## Fallback mode (sem agentes disponíveis)

Se instalação não tem agentes, workflows seguem adiante com Claude principal executando as responsabilidades inline.

`.planning/config.json`:
```json
{
  "orchestrator": {
    "enabled": true,           // ou false se não tem agentes
    "available_agents": [       // lista dos que existem
      "backend-architect",
      "frontend-developer",
      "ui-ux-designer"
    ],
    "fallback_mode": "inline",  // "inline" | "block"
    "parallelization_when_possible": true
  }
}
```

- `fallback_mode: "inline"` = Claude principal faz o trabalho quando agente não existe (mais lento, funcional)
- `fallback_mode: "block"` = workflow para e avisa que agente falta (útil em times que exigem o padrão)

## Gates não são dispensáveis por agente

Ainda que 10 agentes tenham dito "tudo ok", gates do GSD rodam independente:

- Gate 3 (skills) valida PLAN.md textualmente — não confia em "o agente aplicou a skill"
- Gate 5 (integration) roda grep/AST contra código — não confia em "o agente escreveu direito"
- Gate 6 (reconcile) compara PLAN vs código final — agente pode ter mentido ou errado

**Por quê:** agentes podem alucinar, pular regras, não ler skill inteira. Gates são a rede.

## Paralelismo: quando sim, quando não

### Sim (paralelismo traz ganho real)

- Sprint toca **múltiplas camadas independentes** (backend + frontend + infra)
- Pesquisas que podem rodar em paralelo (ex: "pesquisar 3 gateways de pagamento")
- Análises independentes (ex: security review + performance review simultaneamente)

### Não (serial é melhor)

- **Dependências de dados** — frontend precisa da response shape que backend vai definir
- **Decisões arquiteturais sequenciais** — "primeiro decide schema, depois decide endpoints que usam o schema"
- **Revisões em cadeia** — "designer revisa, dev implementa baseado na revisão"
- **Debugging** — um agente de cada vez, causa-efeito claro

### Configuração

`.planning/config.json > parallelization`:
```json
{
  "enabled": true,
  "plan_level": true,
  "task_level": false,          // experimental — deixar false
  "max_concurrent_agents": 3,    // iOS/Android têm limites de IPC
  "min_plans_for_parallel": 2    // abaixo disso, custo > ganho
}
```

## Anti-patterns

- **Confiar no agente para aplicar skill** sem validar no PLAN.md — gate 3 existe por isso
- **Paralelizar com dependência forte** — agente A faz suposição, agente B faz suposição contraditória, vira merge conflict semântico
- **Agente executando sem receber tokens do Visual Contract** — produz UI com hex hardcoded, ESLint quebra, retrabalho
- **Skipping gates porque "agente é bom"** — agente não substitui reconcile
- **Mais de 3 agentes simultâneos** — overhead de merge + contexto divergente supera ganho
- **Agente recebendo contexto pobre** — "implementa endpoint X" sem dar `SPRINT.md`, `api-design-contracts`, `brand.md` → qualidade ruim

## Checklist ao invocar agente

- [ ] Agente está listado em `config.json > orchestrator.available_agents`?
- [ ] Contexto estruturado (sprint_id, arquivos relevantes) foi passado?
- [ ] Skills relevantes carregadas no prompt do agente?
- [ ] Saída do agente tem formato previsível (seções, paths)?
- [ ] Gate posterior vai revalidar o output (skill coverage, security, integration)?
- [ ] Se paralelo: não há dependências fortes entre os agentes?
- [ ] Se sequencial: contexto do próximo agente inclui output do anterior?

## Related

- Workflow invocador: `workflows/plan-phase.md`, `workflows/execute-phase.md`, `workflows/ui-phase.md`
- Config: `.planning/config.json > orchestrator` + `parallelization` + `agent_skills`
- Enforcement: `references/skills-enforcement.md` (skills ainda aplicam)
- Gates: `references/gates-v3.md` (gates não são bypassed por uso de agente)
