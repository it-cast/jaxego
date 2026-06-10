# Skills Enforcement — como o plan-checker valida skills

> Referência citada por `CLAUDE.md` (Regra 5), `gates-v3.md` (Gate 3) e `gsd-plan-checker.md` (Dimensão 6).
> **Status (v0.4.1):** ✅ Infraestrutura de enforcement está implementada. Todas as 44 skills têm `triggers.yaml` e o plan-checker tem Dimensão 6 ("Mandatory Skills Coverage") executando a matriz.

## O problema que isto resolve

Em projetos anteriores, dezenas de skills foram instaladas em `.claude/skills/` e **quase nenhuma consultada** durante execução. Anti-patterns que as próprias skills proíbem (JWT em localStorage, hex hardcoded no lugar de tokens, font-family inline em 25 lugares) apareceram no código.

A regra original "qualquer plano que não citar skills relevantes é rejeitado" não tinha enforcement. Era instrução sem dente.

Este documento define como o `gsd-plan-checker` **detecta** tipos de task e **exige** skills apropriadas.

**Limitação conhecida:** o gate 3 valida que a skill foi **citada** no PLAN.md. Não valida que foi **lida e aplicada**. Para isso, ver Regra 5 do `CLAUDE.md` — humano força explicitamente leitura nos primeiros 3 sprints.

---

## Estrutura de uma skill consultável

Cada skill vive em `.claude/skills/<categoria>/<nome>/` e contém pelo menos:

```
.claude/skills/quality/observability-production/
├── SKILL.md              # conteúdo principal — regras, exemplos, anti-patterns
├── keywords.txt          # lista de keywords/paths que ativam esta skill
└── triggers.yaml         # regras estruturadas de when-to-apply
```

### Formato de `triggers.yaml`

```yaml
# triggers.yaml
name: observability-production
category: quality
required_for:
  # Quando uma task tem QUALQUER destes, a skill é obrigatória
  - task_type: new_endpoint
  - task_type: background_job
  - path_pattern: "backend/app/api/**"
  - keyword_any: ["logger", "structlog", "sentry", "opentelemetry", "trace"]

recommended_for:
  # Quando uma task tem QUALQUER destes, a skill é recomendada (FLAG, não BLOCK)
  - task_type: refactor_service
  - keyword_any: ["exception", "error"]

dispensable_if:
  # Situações onde explicitamente não se aplica
  - "task é puramente frontend (path_pattern: 'apps/**', 'admin/**')"
  - "task é de migration de banco sem mudança de comportamento"

conflict_with: []  # skills que são mutuamente exclusivas (raro)
```

---

## Como o plan-checker usa os triggers

### Passo 1 — Ler todas as skills disponíveis

```bash
SKILLS_FOUND=()
for skill_dir in .claude/skills/*/*/; do
  if [ -f "$skill_dir/triggers.yaml" ]; then
    SKILLS_FOUND+=("$skill_dir")
  fi
done
```

### Passo 2 — Para cada task do PLAN.md, detectar skills aplicáveis

Parsear cada task e extrair:
- `type` (new_endpoint, ui_component, migration, test, refactor, etc.)
- `paths` (lista de arquivos que a task vai tocar)
- `keywords` (palavras-chave da descrição)

Comparar com triggers de cada skill:

```python
def skills_required_for_task(task, skills):
    required = set()
    recommended = set()
    for skill in skills:
        triggers = load_triggers(skill)
        if match_any(task, triggers['required_for']):
            required.add(skill.name)
        elif match_any(task, triggers['recommended_for']):
            recommended.add(skill.name)
    return required, recommended

def match_any(task, triggers):
    for trigger in triggers:
        if 'task_type' in trigger and task.type == trigger['task_type']:
            return True
        if 'path_pattern' in trigger and any(fnmatch(p, trigger['path_pattern']) for p in task.paths):
            return True
        if 'keyword_any' in trigger and any(kw in task.description.lower() for kw in trigger['keyword_any']):
            return True
    return False
```

### Passo 3 — Verificar citações no PLAN.md

O `PLAN.md` deve ter:

```markdown
## Skills Consultadas

- `owasp-security` — rate limit 5/min no endpoint /login, Argon2id para hashing de senha (T-03)
- `api-design-contracts` — resposta de erro padronizada `{error:{code,message,field}}` em todos endpoints (T-02, T-04)
- `observability-production` — middleware de request_id injetado, logger estruturado com campos obrigatórios (T-01)

## Skills Dispensadas (com justificativa)

- `brazilian-forms` — este plano não cria formulário com campos BR
- `ionic-patterns` — plano cobre só backend
```

### Passo 4 — Comparar e decidir

Para cada task, coletar:
- `required_for_task` (do passo 2)
- `cited_in_plan` (do passo 3, seção Consultadas)
- `dispensed_in_plan` (do passo 3, seção Dispensadas)

**Regra de decisão:**

```python
for task in plan.tasks:
    req = required_for_task[task.id]
    cited = cited_in_plan
    dispensed = dispensed_in_plan
    
    missing = req - cited - dispensed
    
    if len(missing) >= 2:
        BLOCK(task, missing)
    elif len(missing) == 1:
        FLAG(task, missing)
    else:
        OK(task)

total_missing = sum over all tasks of missing count
if total_missing >= 3:
    PLAN_REJECTED  # planner precisa revisar
```

---

## Matriz de skills obrigatórias (resumo operacional)

Esta matriz é referência **rápida**. A autoridade é `triggers.yaml` de cada skill. Em caso de conflito, `triggers.yaml` vence.

### Backend

| Sinal na task | Skills obrigatórias |
|---|---|
| `@router.post`, `@router.get`, `@app.route`, etc. | `owasp-security` + `api-design-contracts` + `observability-production` |
| `async def login`, `def authenticate`, keyword "jwt", "oauth" | `owasp-security` (obrigatório) |
| Arquivo em `backend/app/models/` + migration novo | `mysql-schema-design` (ou equivalente do stack) |
| Retorno contém campos PII (cpf, email, nome, phone) | `lgpd-compliance` |
| Keyword "webhook" + origem externa | `owasp-security` (validação de assinatura) |
| Integração com gateway de pagamento | skill do gateway específico (`stripe-*`, `asaas-*`, `mercado-pago-*`, `{gateway-pagamento}-*`, etc.) |

### Frontend Web (Angular/React/Vue)

| Sinal | Skills obrigatórias |
|---|---|
| Criar componente novo em `apps/admin/`, `apps/web/`, etc. | Skill de framework (`angular-material-patterns`, `react-patterns`) + `design-to-code` + `error-ux-patterns` |
| Formulário com input de CPF/CNPJ/CEP/telefone | `brazilian-forms` + `ux-copywriting-ptbr` |
| Tela com listagem (tabela, cards) | `empty-states-polish` + `visual-regression-testing` |
| Modal, dialog, overlay | `accessibility-pro` (focus trap) + `micro-animations-delight` |
| Fluxo de erro (4xx, 5xx) visíveis | `error-ux-patterns` |
| Internacionalização ou texto hardcoded em template | `i18n-ready-architecture` + `ux-copywriting-ptbr` |

### Frontend Mobile (Ionic/Capacitor/React Native)

| Sinal | Skills obrigatórias |
|---|---|
| Path em `apps/mobile/` | `ionic-patterns` (ou equivalente) + `mobile/safe-areas` |
| Tela com scroll + input de teclado | `mobile/keyboard-avoidance` |
| Interação com rede (consumo de API) | `mobile/offline-first` + `error-ux-patterns` |
| Notificação local ou push | `mobile/push-notifications-architecture` |
| Gesture (swipe, pull-to-refresh) | `mobile/touch-gestures` |
| Upload de foto/arquivo | `file-upload-ux` + `ionic-patterns` |

### Infra / DevOps

| Sinal | Skills obrigatórias |
|---|---|
| Dockerfile, docker-compose | `docker-production-ready` |
| Nginx config | `nginx-production-hardening` |
| Redis config | `redis-production-config` (requirepass, maxmemory-policy, etc.) |
| Nova migration em produção | `migration-safety` |
| CI/CD pipeline | `ci-cd-patterns` |

### Qualidade / Cross-cutting

| Sinal | Skills obrigatórias |
|---|---|
| Qualquer endpoint que entra em produção | `observability-production` |
| Qualquer componente visual com estado assíncrono | `error-ux-patterns` + `empty-states-polish` |
| Performance-sensitive (listagem grande, dashboard) | `performance-web-vitals` |
| Mudança em componente do design system | `visual-regression-testing` + `component-library-governance` |
| PR para `main` | `accessibility-pro` (a11y lint em CI) |

### Sprint UI Matrix (aplicada a `SPRINT.md` com `has_ui: true`)

Esta matriz é invocada pelo `/gsd-sprint-plan` e pelo plan-checker quando valida um `SPRINT.md`. Mais estrita do que as matrizes por-task acima, porque o sprint é a unidade de entrega testável — não dá para empurrar UX para "depois".

| Flag no front-matter do SPRINT.md | Skill obrigatória | Motivo |
|-----------------------------------|-------------------|--------|
| `has_ui: true` | `product/component-library-governance` | Todo componente novo decide shared-vs-feature com critério explícito |
| `has_ui: true` | `quality/accessibility-pro` | WCAG AA não é opt-in |
| `has_ui: true` + `locale: pt-BR` | `br/ux-copywriting-ptbr` | Microcopy consistente com `brand.md` |
| `has_forms: true` OU `has_error_states: true` | `quality/error-ux-patterns` | Error codes tipados + patterns de retry/empty |
| `has_non_trivial_motion: true` | `product/micro-animations-delight` | Tokens de motion + prefers-reduced-motion |
| `touches_shared_components: true` | `product/visual-regression-testing` | Stories + baselines em Chromatic/Playwright |

Além dessas flags, o sprint também herda matrizes por-task (acima) para qualquer endpoint/modelo/migration/etc. que introduza.

**Obrigatoriedade da seção `## Visual Contract`:** se `has_ui: true`, sprint sem `## Visual Contract` preenchida = BLOCK. Se seção existe mas cita token inexistente em `docs/identidade-visual/tokens.json` = BLOCK. Ver `references/visual-fidelity.md` para detalhes.

---

## Como responder quando o plan-checker bloqueia

O planner (quando recebe feedback "block: skills missing") deve:

1. Reler `SKILLS_INDEX.md` e identificar as skills reportadas
2. Ler o `SKILL.md` de cada uma
3. Absorver as regras aplicáveis
4. Reescrever as tasks afetadas citando a skill no campo `skills_applied`:

```yaml
- id: T-03
  description: "Implementar POST /proposals/{id}/accept"
  type: new_endpoint
  paths: ["backend/app/api/proposals.py"]
  skills_applied:
    - name: owasp-security
      rules_applied:
        - "Rate limit 20/min por IP"
        - "Verificar que o recurso pertence ao workspace/tenant do usuário (multitenancy enforcement)"
    - name: api-design-contracts
      rules_applied:
        - "Response shape sucesso: {resource_id: UUID, status: string}"
        - "Response erro: {error:{code:'PROPOSAL_NOT_FOUND'|'PROPOSAL_NOT_OWNED'|...}}"
    - name: observability-production
      rules_applied:
        - "Logger com request_id, user_id, proposal_id, duration_ms"
```

5. Adicionar à seção `## Skills Consultadas`:

```markdown
## Skills Consultadas

- `owasp-security` — T-03, T-05: rate limit, multitenancy enforcement
- `api-design-contracts` — T-03, T-04: error codes padronizados
- `observability-production` — T-01, T-03: logger estruturado
```

6. Re-submeter para plan-checker.

---

## Quando criar uma skill nova

Se durante o planning, surge padrão que:
- Aparece em múltiplas fases
- Tem regras replicáveis
- Causou bug ou retrabalho em projeto anterior

**Criar skill via `/gsd-skill-creator`** — o workflow guia a criação de `SKILL.md` + `triggers.yaml` + `keywords.txt`.

Skills criadas durante execução ficam em `.claude/skills/<cat>/<nome>/` e são versionadas junto ao projeto. Se forem genéricas (não específicas ao projeto), podem ser movidas depois para o repositório central do framework.

---

## Anti-padrões na citação de skills

### ❌ Citar skill como checkbox vazio
```markdown
## Skills Consultadas
- owasp-security
- brazilian-forms
```

**Problema:** não mostra qual decisão se baseou em qual skill. Plan-checker considera como não-citação.

### ✅ Citação válida
```markdown
## Skills Consultadas
- `owasp-security` — T-03: rate limit 5/min em /login; T-05: Argon2id com custo 12
- `brazilian-forms` — T-07: máscara de CPF no cadastro, validação de dígito verificador
```

### ❌ Citar todas as skills para "cobrir bases"
```markdown
- `angular-material-patterns` — (plano é backend-only)
- `ionic-patterns` — (plano é backend-only)
- `mysql-schema-design` — (plano não tem migration)
```

**Problema:** poluição do plan. Plan-checker vê citação sem task aplicável.

### ✅ Dispensar com justificativa
```markdown
## Skills Dispensadas (com justificativa)
- `angular-material-patterns` — plano é backend-only
- `ionic-patterns` — plano é backend-only  
- `mysql-schema-design` — plano não cria tabela nova
```

### ❌ Inventar regra que não está na skill
```markdown
- `owasp-security` — T-03: usar MD5 para token (decisão minha, skill não fala em MD5)
```

**Problema:** skill `owasp-security` proíbe MD5. Plan-checker deve flagear: "regra citada conflita com skill".

---

## Debug: por que minha task está exigindo skill X?

Rodar:

```bash
/gsd-skill-debug --task T-03
```

Saída:
```
Task T-03: "Implementar POST /proposals/{id}/accept"
  Type detectado: new_endpoint
  Paths: ["backend/app/api/proposals.py"]
  Keywords: ["proposals", "accept", "endpoint"]

Skills que MATCH 'required_for':
  - owasp-security
    → trigger ativado: task_type=new_endpoint
    → fonte: .claude/skills/quality/owasp-security/triggers.yaml:4
  - api-design-contracts
    → trigger ativado: path_pattern "backend/app/api/**"
  - observability-production
    → trigger ativado: task_type=new_endpoint

Skills que MATCH 'recommended_for':
  - error-ux-patterns
    → trigger ativado: keyword "accept" (may return error states)

Para dispensar (se justificável): adicionar ao PLAN.md:
## Skills Dispensadas (com justificativa)
- `<skill>` — <razão técnica clara>
```

Isso torna o sistema auditável e debugável.
