# /gsd-sprint-plan — quebrar milestone em sprints testáveis

> Workflow invocado depois que o milestone está definido no `ROADMAP.md` mas antes de iniciar execução. Produz uma sequência de `SPRINT-NN.md` testáveis, seguindo a estratégia de slicing escolhida no `bootstrap` e registrada em `.planning/config.json > slicing_strategy`.

## Quando invocar

- Após `bootstrap` concluído e `.planning/config.json > slicing_strategy` definido
- Com um milestone selecionado (arg obrigatório)
- Antes de começar o primeiro sprint do milestone
- Ao replanejar um milestone que já foi parcialmente executado (discard sprints futuros, refaz a partir do próximo)

## Inputs

- `milestone_id`: ID do milestone (ex: `M2-crud-anuncios`)
- Opcional: `--max-sprints N` para cap (default 8)
- Opcional: `--force-strategy {vertical_value|admin_first}` para override da config

## Outputs

- N arquivos `.planning/sprints/SPRINT-NN-<slug>.md` (numerados sequencialmente após o último sprint global)
- Atualização de `.planning/SPRINTS.md` (tabela de visão geral)
- Resumo conversacional com narrativa de cada sprint + critério de aceite testável

## Pré-condições validadas

Antes de produzir qualquer SPRINT.md, este workflow checa:

1. **`.planning/config.json` existe** e tem `slicing_strategy` definida
2. **Milestone existe** em `.planning/ROADMAP.md`
3. **Identidade visual preenchida** (`docs/identidade-visual/tokens.json` tem pelo menos categorias `color` + `space`) — senão, sprints com UI serão bloqueados no execute
4. **Skills obrigatórias disponíveis** no framework (`.claude/skills/SKILLS_INDEX.md`)
5. **Sprint anterior fechado** (se aplicável) — sprints não se sobrepõem

Falha em qualquer pré-condição = **BLOCK** com mensagem acionável. Ex:

```
BLOCK: docs/identidade-visual/tokens.json está vazio.
→ Preencha com pelo menos color + space antes de planejar sprints com UI.
→ Ver referência: .claude/get-shit-done/references/visual-fidelity.md
```

## Passos

### 1. Carrega contexto

- Lê `.planning/config.json` → `slicing_strategy` + `locale` + `platforms`
- Lê `docs/project-brief.md` → domínio, usuário-alvo, complexidade
- Lê `ROADMAP.md > {milestone_id}` → escopo bruto, features previstas
- Lê `.planning/METRICS.md` (se há entradas anteriores) → média de duration_days, fix_iterations — calibra estimativas

### 2. Aplica estratégia

#### Se `vertical_value`:

Para cada feature do milestone, pergunta:
- Quem é o usuário externo cuja vida fica melhor?
- Qual é a ação de valor mínima dele? (verbo curto: criar, enviar, ver, pagar)
- Que 1-2 regras críticas acompanham essa ação?

Agrupa em sprints seguindo o fluxo natural do usuário: **ação principal → mutação de estado → pagamento/transação → colaboração/compartilhamento → filtros/busca avançada → dashboards**. Admin aparece **puxado** quando sprint de operação real demanda.

#### Se `admin_first`:

Para cada feature do milestone, pergunta:
- É entidade de cadastro (mestre) ou entidade de negócio (transacional) ou regra de negócio?
- Quais entidades dependem de quais?

Agrupa em sprints seguindo: **cadastros mestres (usuário, permissão, categoria, tenant) → cadastros de negócio (cliente, produto, pedido como enum) → regras críticas (transições de estado, workflows) → filtros/junções/relatórios**.

### 3. Monta SPRINT-NN.md de cada sprint

Para cada sprint identificado:

1. Copia `.claude/get-shit-done/templates/SPRINT.md`
2. Preenche front-matter YAML: `sprint_id`, `milestone`, `slicing_strategy`, `duration_days_planned`, flags de `has_*` e `touches_shared_components`
3. Preenche **Narrativa** (1 parágrafo em linguagem de usuário final)
4. Preenche **Definition of Done** (3-6 verificações binárias)
5. Se `has_ui: true`, preenche **Visual Contract** com tokens específicos
   - Consulta `docs/identidade-visual/tokens.json` para validar que cada token citado existe
   - Se token necessário não existe, sinaliza para usuário adicionar antes do kickoff
6. Preenche **UX Skills Applied** com output concreto por skill aplicável
   - Não é lista abstrata — é "skill X produz artefato Y neste sprint"
7. Preenche **Tasks** ordenadas (T1-TN)
8. Marca **Skills Consultadas** + **Skills Dispensadas** com justificativa
9. Identifica **Dependências** entre sprints
10. Lista **Riscos** com probabilidade/impacto/mitigação

### 4. Valida cada SPRINT.md

Antes de persistir, passa cada arquivo pelo `plan-checker` em modo sprint:

- Seções obrigatórias presentes e não vazias
- Visual Contract cita tokens que existem em tokens.json (se `has_ui`)
- Matriz de skills obrigatórias aplicada (`sprint_ui_matrix` em `skills-enforcement.md`)
- DoD tem 3-6 itens, cada um binário e em linguagem de usuário
- Tasks têm 3-12 itens (sprint pequeno demais ou grande demais = repensar)

Falha = bloqueio do sprint específico, não dos outros. Workflow reporta quais passaram e quais precisam de ajuste.

### 5. Persiste

- Cria `.planning/sprints/SPRINT-NN-<slug>.md` para cada sprint aprovado
- Atualiza `.planning/SPRINTS.md` com nova linha na tabela de visão geral
- NÃO executa nenhum sprint automaticamente — usuário escolhe quando começar

### 6. Reporta ao humano

Output conversacional:

```
Milestone M2-crud-anuncios quebrado em 4 sprints (vertical_value):

Sprint 03 — Prestador cria anúncio (5d)
  DoD: prestador faz login, cria anúncio, vê na sua lista; cliente anônimo busca e vê detalhes
  UI: sim · forms: sim · toca shared: sim (app-empty-state)
  Visual Contract: 7 tokens citados, todos existem em tokens.json ✓
  Skills: 8 obrigatórias citadas, 5 dispensadas com justificativa

Sprint 04 — Prestador edita e remove anúncio (3d)
  DoD: ...

Sprint 05 — Cliente contata prestador (inicia conversa) (5d)
  DoD: ...
  ⚠ depende de Sprint 04 fechado

Sprint 06 — Sistema de denúncia + moderação (7d)
  DoD: ...
  ⚠ primeira aparição de admin: tela de moderação

Total planejado: 20 dias úteis (~4 semanas)
Arquivos criados em .planning/sprints/

Próximo passo: /gsd-plan-phase sprint-03-prestador-cria-anuncio
(ou `/gsd-sprint-plan M3-...` para próximo milestone)
```

## Relação com outros workflows

```
bootstrap
  ↓ escolhe slicing_strategy
ROADMAP.md (milestones brutos)
  ↓
/gsd-sprint-plan M<N>     ← este workflow
  ↓ produz sprints testáveis
SPRINT-NN.md validado
  ↓
/gsd-plan-phase sprint-NN  ← plan-phase agora opera sobre sprint
  ↓ produz PLAN.md do sprint (mais detalhado)
/gsd-execute-phase
  ↓ gates rodam durante execução
reconcile-state
  ↓ ao fim, verifica SPRINT.md ↔ código
/gsd-metrics sprint-NN     ← fecha sprint com retrospectiva
  ↓
PLAN.md arquivado, SPRINT.md marcado closed em .planning/SPRINTS.md
```

## Anti-patterns deste workflow

- Gerar 10+ sprints de uma vez para um milestone grande — melhor gerar 3-4, executar, re-planejar próximos com aprendizado
- Sprint sem dependências explícitas (some depender de todo sprint anterior sem dizer)
- Sprint que só tem backend ou só tem frontend — não atravessa camadas = não é testável por humano
- Sprint com DoD vago ("feature funciona") — rejeita no checker
- Sprint com 15+ tasks — partir em dois
- Sprint com 2 tasks — juntar com adjacente ou reenquadrar como micro-task em outro sprint
- Ignorar `slicing_strategy` da config.json e fazer do jeito que acha melhor — bootstrap perguntou por um motivo, respeitar a decisão

## Edge cases

### Milestone pequeno (cabe em 1 sprint)
- Gerar 1 SPRINT.md único. Avisa usuário: "Milestone pequeno — talvez valha agregar com adjacente no ROADMAP antes."

### Milestone gigante (>6 sprints estimados)
- Gera os primeiros 4-5 sprints + avisa: "Milestone grande. Recomendo re-planejar após sprint 4 com aprendizado adquirido. Não gerei os últimos 3 para evitar falso planejamento."

### Replanejamento no meio do milestone
- Se já há sprints fechados, workflow só re-planeja do próximo em diante
- Sprints futuros anteriores são marcados `deprecated: true` no SPRINTS.md, não apagados (histórico)
- Mensagem explícita sobre o que mudou e por quê

### Strategy conflito com projeto
- Se `slicing_strategy: admin_first` mas `project-brief.md` indica B2C, workflow **avisa** mas não força mudança:
  > "Config diz admin_first mas projeto parece B2C (usuário-alvo: consumidor). Tem certeza? Use --force-strategy vertical_value ou mude config.json."

## Checklist para o workflow

- [ ] Config e identidade visual validadas
- [ ] Milestone existente e bem definido
- [ ] Cada sprint tem narrativa, DoD, Visual Contract (se UI), Skills, Tasks, Deps, Riscos
- [ ] Cada sprint validado pelo plan-checker
- [ ] Arquivos persistidos em `.planning/sprints/`
- [ ] `.planning/SPRINTS.md` atualizado
- [ ] Usuário informado do próximo passo
