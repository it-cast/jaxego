# GUIA — Projeto Novo (do zero)

**Quando usar este documento:** você vai começar um projeto do zero e quer aplicar o framework desde o dia 1. Não tem código, não tem docs, não tem nada.

**Tempo estimado:** 3-5 horas na primeira vez (maior parte é preencher docs do projeto, não do framework).

**Pré-requisitos:**
- Node 18+ (`nvm install 20 && nvm use 20` se não tiver)
- Python 3.10+
- Git configurado
- Claude Code instalado (https://docs.claude.com/en/docs/claude-code)
- Opcional: pandoc (só se você for ter .docx/.pptx nos docs)

---

## ORDEM DE EXECUÇÃO

```
FASE 1: Instalar framework (10 min)
FASE 2: Preencher docs do projeto (60-90 min)
FASE 3: Preencher identidade visual, se tem UI (30-60 min)
FASE 4: Configurar hooks (5 min)
FASE 5: Primeiro prompt no Claude (30 min)
FASE 6: Quebrar primeiro milestone em sprints (20 min)
FASE 7: Executar primeiro sprint (30 min a 3h)
FASE 8: Fechar sprint e métricas (15 min)
FASE 9: Ciclo contínuo (repete 6-8)
```

---

## FASE 1 — Instalar framework (10 min)

### Passo 1.1 — Descompactar em pasta nova

```bash
cd ~/projetos
unzip gsd-framework.zip
mv gsd-framework meu-projeto      # nome do seu projeto em kebab-case
cd meu-projeto
```

### Passo 1.2 — Git init

```bash
git init
git add .
git commit -m "chore: inicializa projeto com gsd-framework v0.9.4"
```

### Passo 1.3 — Validar integridade

```bash
bash tests/framework/run-all.sh
```

Resultado esperado: `11/11 suites passed`. Se falhou, descompacte de novo em pasta limpa.

### Passo 1.4 — Permissões

```bash
chmod +x bin/*.sh
chmod +x .claude/hooks/*.sh
chmod +x .claude/get-shit-done/bin/*.cjs 2>/dev/null || true
```

### Passo 1.5 — Testar o motor

```bash
node .claude/get-shit-done/bin/gsd-tools.cjs --help
```

Esperado: lista de comandos. Se deu erro, Node < 18.

---

## FASE 2 — Preencher docs do projeto (60-90 min)

**Atenção:** essa fase parece burocrática mas é o fundamento. Vagueza aqui vira imprecisão depois.

### Passo 2.1 — `docs/project-brief.md`

Abra o arquivo. Tem 12 seções. Preencha cada uma. **Campos mais importantes:**

- **Seção 2 (usuário-alvo):** define a strategy de slicing. Se usuário é externo (cliente, paciente, aluno), será `vertical_value`. Se é operador interno (atendente, gerente), será `admin_first`.
- **Seção 8 (fora de escopo):** mais importante que a seção 7. É o que evita scope creep.
- **Seção 11 (decisões já tomadas):** se você já decidiu stack, arquitetura, abordagem — documenta. Essas viram ADRs.

Se não souber alguma resposta, escreve `a definir` — o bootstrap detecta e pergunta. Nunca invente.

### Passo 2.2 — `specs/project.yaml`

Metadata básica:

```yaml
name: "Meu Projeto"
slug: "meu-projeto"
description: "1 frase sobre o que o projeto faz"
locale: "pt-BR"
platforms:
  - web
  - mobile
  - api
owner: "Seu Nome"
created: "2026-04-23"
```

### Passo 2.3 — `specs/stack.yaml`

Seja específico. Nada de "talvez X ou Y":

```yaml
backend:
  language: "python"
  version: "3.11"
  framework: "fastapi"
  framework_version: "0.109"
  orm: "sqlalchemy"

frontend_web:
  framework: "angular"
  version: "19"
  ui_kit: "angular-material"

frontend_mobile:
  framework: "angular"
  version: "19"
  ui_kit: "ionic"
  wrapper: "capacitor"
  targets: ["android", "ios"]

database:
  primary: "mysql"
  version: "8.0"
  migrations: "alembic"

infra:
  hosting: "vps"
  container: "docker"
  ci: "github-actions"

auth:
  strategy: "jwt"

payment:
  psp: "pagarme"
  methods: ["pix", "boleto"]
```

### Passo 2.4 — `specs/database.yaml`

Esboço das tabelas principais. Não precisa ser final — vai evoluir:

```yaml
tables:
  users:
    description: "Autenticação base"
    columns:
      - id: "uuid, PK"
      - email: "string 255, unique"
      - password_hash: "string 255"
      - status: "enum(pending, active, suspended)"
    indexes: ["email"]
```

### Passo 2.5 — `specs/rules.yaml`

Regras de negócio críticas numeradas:

```yaml
rules:
  - id: R-001
    description: "Usuário só pode fazer compra se email foi verificado"
    criticality: high
  - id: R-002
    description: "Desconto máximo por pedido é 30% do valor"
    criticality: high
```

### Passo 2.6 — Commit

```bash
git add docs/project-brief.md specs/
git commit -m "docs: preenche project-brief e specs iniciais"
```

---

## FASE 3 — Identidade visual (30-60 min, obrigatório se tem UI)

Sem isso preenchido, **sprints com UI bloqueiam** no gate de Visual Contract.

### Passo 3.1 — `docs/identidade-visual/tokens.json`

**Mínimo aceitável:** categorias `color` + `space`. Template completo:

```json
{
  "color": {
    "brand": {
      "500": { "value": "#3b82f6" },
      "600": { "value": "#2563eb" }
    },
    "text": {
      "primary": { "value": "#111827" },
      "secondary": { "value": "#6b7280" }
    },
    "surface": {
      "default": { "value": "#ffffff" },
      "elevated": { "value": "#f9fafb" }
    },
    "border": {
      "default": { "value": "#e5e7eb" }
    },
    "semantic": {
      "success": { "value": "#10b981" },
      "warning": { "value": "#f59e0b" },
      "danger": { "value": "#ef4444" }
    }
  },
  "space": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" },
    "xl": { "value": "32px" }
  }
}
```

**Sem designer?** Use geradores: coolors.co (paletas), tailwindcss.com/docs/customizing-colors (escalas), fontpair.co (fontes).

**Regra:** token provisório é 10x melhor que token ausente.

### Passo 3.2 — `docs/identidade-visual/brand.md`

Voz, tom, vocabulário canônico. Template guiado no arquivo. Seções essenciais:

- Voz da marca (é / não é)
- Tom por contexto (onboarding, erro, confirmação)
- Vocabulário (usar / evitar)
- Gramática (tratamento, pronomes)

Sem isso, copywriting vira adivinhação.

### Passo 3.3 — Commit

```bash
git add docs/identidade-visual/
git commit -m "docs: identidade visual inicial (tokens + brand)"
```

---

## FASE 4 — Configurar hooks (5 min)

Hooks rodam via `.claude/settings.json`. Framework já vem com template.

### Passo 4.1 — Verificar

```bash
cat .claude/settings.json | head -30
```

Deve ter bloco `"hooks"`. Se não, copie do `.claude/hooks/README.md`.

### Passo 4.2 — Testar um hook

```bash
echo '{}' | node .claude/hooks/gsd-statusline.js
```

Retorna JSON. Se erro, Node < 18.

### Passo 4.3 — Commit

```bash
git add .claude/settings.json
git commit -m "chore: configura hooks"
```

---

## FASE 5 — Primeiro prompt no Claude (30 min)

### Passo 5.1 — Abrir Claude Code

```bash
cd ~/projetos/meu-projeto
claude
```

### Passo 5.2 — Prompt de validação inicial

**Copie e cole exatamente isto como primeiro prompt:**

```
Estou iniciando um projeto novo usando o gsd-framework v0.9.4.

Antes de qualquer coisa, faça em ordem:
1. Leia CLAUDE.md integralmente
2. Leia FRAMEWORK-STATUS.md — especialmente seção "O que esta versão NÃO resolve" do v0.4.0
3. Liste arquivos em docs/ e specs/ com 1 frase descrevendo cada um
4. Me confirme explicitamente: "li CLAUDE.md, li FRAMEWORK-STATUS, entendi que estamos em v0.4.0 com as seguintes limitações conhecidas: [liste 3 principais]"

Só prossiga para o próximo passo após eu confirmar.
```

**Por que esse prompt:** estabelece o padrão de interação. Se você aceitar "eu li" sem prova, vai aceitar depois. Se o Claude fizer resumo genérico sem colar trechos, **insista**.

### Passo 5.3 — Rodar bootstrap

Depois da confirmação de leitura:

```
/gsd:bootstrap
```

### Passo 5.4 — O que vai acontecer

Claude vai:

1. Ler `docs/project-brief.md`, `specs/*.yaml`, `docs/identidade-visual/*`
2. Apresentar síntese do projeto para você validar
3. Perguntar **strategy de slicing** (`vertical_value` ou `admin_first`)
4. Perguntar **orchestrator mode** — responda `2` (inline) para começar
5. Perguntar **visual_tokens_mode** — responda `final` se preencheu tudo, `provisional` se está incompleto
6. Gerar `.planning/PROJECT.md`, `ROADMAP.md`, `STATE.md`, `REQUIREMENTS.md`, `MILESTONES.md`, `DECISIONS.md`

### Passo 5.5 — CRÍTICO: revisar o roadmap

Abra `.planning/ROADMAP.md`. Este é o documento mais importante gerado.

**Perguntas:**
- A ordem de milestones faz sentido?
- A duração é realista?
- Faltou algum milestone crítico?
- Algum está grande demais (> 3 semanas)?

Se errado, peça ajuste específico:

```
Revisei ROADMAP.md. Preciso de ajustes:
1. M3 (Pagamento) deveria vir antes de M2 (Catálogo) porque X
2. M5 está grande demais — quebra em M5a e M5b
3. Adicione M0 antes de M1: "Setup infra e CI"

Atualize ROADMAP.md e me mostre o diff.
```

### Passo 5.6 — Commit

```bash
git add .planning/ .claude/
git commit -m "chore: bootstrap — ROADMAP com N milestones"
```

---

## FASE 6 — Quebrar primeiro milestone em sprints (20 min)

### Passo 6.1 — Identificar primeiro milestone

Abra `.planning/ROADMAP.md`. Anote o slug (ex: `M0-setup-infra`).

### Passo 6.2 — Quebrar em sprints

```
/gsd:plan-phase M0-setup-infra
```

Workflow vai gerar 3-5 `SPRINT-NN-<slug>.md` em `.planning/sprints/`. Cada sprint validado: Visual Contract, skills, DoD testável em 30 min.

### Passo 6.3 — Revisar cada sprint

Abra cada `.planning/sprints/SPRINT-NN-*.md` e confira:

- Narrativa clara em linguagem humana?
- Definition of Done testável manualmente em ≤ 30 min?
- Skills citadas batem com o escopo?
- Se `has_ui: true`, Visual Contract usa tokens do `tokens.json`?

Peça ajustes específicos se necessário. Commit:

```bash
git add .planning/sprints/
git commit -m "chore: sprints planejados para M0-setup-infra"
```

---

## FASE 7 — Executar primeiro sprint (30 min a 3h)

### Passo 7.1 — Planejar fase

```
/gsd:plan-phase sprint-01-docker-fastapi
```

Workflow roda gates 1, 2 e 4, invoca `gsd-phase-researcher`, gera `PLAN.md` detalhado.

### Passo 7.2 — **CRÍTICO: forçar leitura de skills**

Este é o passo mais importante do framework inteiro. Gate 3 valida skill **citada** no PLAN — não valida que foi **lida e aplicada**.

**Antes de executar, cole este prompt:**

```
PARE antes de executar. Antes do /gsd:execute-phase, faça em ordem:

1. Abra .claude/skills/domain/docker-production-ready/SKILL.md 
   (arquivo inteiro). Me liste:
   - As 3 regras mais relevantes para este sprint específico
   - Quais delas você vai aplicar no código
   - Alguma que você vai conscientemente NÃO aplicar e por quê
   - Cole uma linha literal de cada regra para provar que leu

2. Abra .claude/skills/domain/mysql-schema-design/SKILL.md 
   e faça o mesmo.

3. Abra .claude/skills/quality/observability-production/SKILL.md 
   e faça o mesmo.

NÃO COMECE A CODAR até ter feito os 3 passos e eu confirmar.
```

Substitua as skills pelas do sprint atual. Se Claude pular ou resumir genericamente, insista:

```
Você não colou linha literal das regras. Refaça passo 1, copiando 
texto EXATO da SKILL.md entre aspas. Se não está conseguindo abrir 
o arquivo, me avise o erro — não invente.
```

**Nos 3 primeiros sprints, nunca pule esse prompt.** Depois vira hábito.

### Passo 7.3 — Revisar PLAN.md

Abra `.planning/sprints/sprint-01-*/PLAN.md`. Confira tasks, dependências, skills aplicadas. Ajuste se necessário.

### Passo 7.4 — Executar

```
/gsd:execute-phase sprint-01-docker-fastapi
```

Claude implementa tasks em ordem. Observe:

- **Statusline** mostra progresso
- **Context monitor** avisa se contexto fica baixo (35% warning / 25% critical)
- **Gate 5** (integration check) roda em runtime
- **Gate 6** (reconcile) compara PLAN vs código ao final
- **Gate 7** (tests + lint) final

Se contexto virar `CRITICAL`:

```
PARE. Salve estado atual em .planning/STATE.md incluindo task exata 
em que paramos. Vou iniciar sessão nova.
```

### Passo 7.5 — Resolver divergências de reconcile

Ao final, gate 6 pode reportar divergências PLAN ↔ código:

```
1. [ALTA] PLAN.md diz pool_size=20
   → Código usa pool_size=5
   → Ação sugerida: alinhar
```

Responda validando cada:

```
1. Código está certo, atualize PLAN.md para pool_size=5
2. Aceitar como dívida técnica, adicionar em .planning/TECH-DEBT.md
```

### Passo 7.6 — Validar DoD manualmente

Antes de fechar, teste você mesmo a DoD do SPRINT.md. Se não passa, corrija antes de `bin/collect-metrics.sh`.

### Passo 7.7 — Commit

```bash
git add .
git commit -m "feat(sprint-01): descrição curta da narrativa"
```

---

## FASE 8 — Fechar sprint e métricas (15 min)

### Passo 8.1 — Rodar métricas

```
bin/collect-metrics.sh sprint-01-docker-fastapi
```

Gera `.planning/retros/sprint-01-*.md` e pausa para você preencher qualitativo.

### Passo 8.2 — Preencher retrospectiva HONESTAMENTE

5 campos qualitativos + 2 scores (1-5). Seja específico:

- **Funcionou bem:** exemplo concreto, não "tudo ok"
- **Atrapalhou:** quando Claude errou, quando framework atrapalhou
- **Faltou:** skill, contexto, ferramenta que você queria ter
- **Score compreensão:** Claude entendeu o que você queria? (1-5)
- **Score qualidade:** código entregue foi bom? (1-5)

Dados honestos de 3 sprints > 10 sprints de "tudo foi ótimo".

### Passo 8.3 — Commit

```bash
git add .planning/retros/ .planning/METRICS.md
git commit -m "chore(sprint-01): retrospectiva e métricas"
```

---

## FASE 9 — Ciclo contínuo

### Loop sprint-a-sprint

Para cada próximo sprint no mesmo milestone:

```
/gsd:plan-phase sprint-02-<slug>
(prompt de forçar leitura de skills)
/gsd:execute-phase sprint-02-<slug>
bin/collect-metrics.sh sprint-02-<slug>
```

### Fim de milestone

```
/gsd:milestone-summary M0-setup-infra
/gsd:plan-phase M1-<proximo-slug>
```

### Rituais semanais (30 min/semana)

```bash
# Atualizar INDEX de docs se adicionou arquivos
/gsd:docs-update

# Converter binários novos
bash bin/convert-docs.sh

# Revisar métricas
cat .planning/METRICS.md
```

### Telemetria (a cada 3-5 sprints)

```bash
bash bin/export-telemetry.sh
```

Guarda o JSON anonimizado para compartilhar em próxima conversa com o Claude — é isso que alimenta iteração do framework.

---

## COMANDOS PRINCIPAIS — referência rápida

### Navegação e status

```
/gsd:bootstrap                    # inicial (apenas uma vez)
/gsd:resume-work                  # continua de onde parou
/gsd:health                       # scan de divergências
/gsd:progress                     # resumo do sprint atual
```

### Planejamento

```
/gsd:plan-phase M<N>-<slug>      # quebra milestone em sprints
/gsd:plan-phase <sprint-id>       # gera PLAN.md com skills
/gsd:discuss-phase <N>            # captura decisões → CONTEXT.md
/gsd:ui-phase <N>                 # UI-SPEC.md (se has_ui)
```

### Execução

```
/gsd:execute-phase <sprint-id>    # execução wave-based
/gsd:secure-phase <N>             # valida threat model
/gsd:reconcile-state <N>          # PLAN vs código real
/gsd:verify-phase <N>             # success criteria
```

### Fechamento

```
bin/collect-metrics.sh <sprint-id>          # retro + collect-metrics
/gsd:milestone-summary M<N>       # fecha milestone
/gsd:ship                         # checklist de deploy
```

### Utilidades

```
/gsd:docs-update                   # sincroniza INDEX.md de docs/
/gsd:suggestions                  # revisa SUGGESTIONS
/gsd:td-review                    # revisa TECH-DEBT
/gsd:note "texto"                 # adiciona nota à fase atual
/gsd:session-report               # snapshot da sessão
```

Lista completa: `ls .claude/commands/gsd/` (73 commands)

---

## PROMPTS ESSENCIAIS — copie e cole

### Para começar sessão nova em projeto já iniciado

```
Abri sessão nova. Leia CLAUDE.md e .planning/STATE.md para entender 
onde paramos. Me diga em 3 linhas: milestone atual, sprint atual, 
task em que estamos agora.
```

### Forçar leitura real de skill

```
PARE antes de executar. Abra .claude/skills/<categoria>/<nome>/SKILL.md 
(arquivo inteiro). Liste as 3 regras mais relevantes para este sprint, 
cole linha literal de cada entre aspas, diga quais vai aplicar e quais 
NÃO vai aplicar e por quê. Não comece a codar até eu confirmar.
```

### Auditoria honesta antes de fechar sprint

```
Antes de fechar este sprint, faça auditoria honesta:
1. Qual skill você citou mas NÃO aplicou de fato?
2. Qual parte do código tem TODO/FIXME que vira dívida?
3. Qual teste você pulou ou simplificou?
Seja autocrítico. Quero saber o que NÃO está pronto.
```

### Salvar estado e pausar

```
Salve estado atual em .planning/STATE.md:
- Milestone/sprint atual
- Task exata em que paramos (com linha se possível)
- O que já foi commitado
- Próximo passo necessário

Depois pare. Vou iniciar sessão nova.
```

### Claude está inventando contexto

```
Pare. Você está inventando informação. Reabra docs/project-brief.md 
e specs/stack.yaml e cole a seção relevante ANTES de continuar. 
Não pode inferir o que não está escrito.
```

### Desfazer última ação

```
Desfaça a última mudança. Reverta para o estado anterior ao meu 
último prompt. Use git se precisar.
```

---

## CHECKLIST DA PRIMEIRA SEMANA

### Antes do Claude

- [ ] Node 18+, Python 3.10+, Git funcionando
- [ ] Framework descompactado e `11/11 suites passed`
- [ ] Scripts com `chmod +x`
- [ ] `docs/project-brief.md` preenchido (12 seções)
- [ ] `specs/project.yaml`, `stack.yaml`, `rules.yaml` preenchidos
- [ ] `specs/database.yaml` se tem DB
- [ ] `docs/identidade-visual/tokens.json` com color + space
- [ ] `docs/identidade-visual/brand.md` se tem UI
- [ ] `.claude/settings.json` com hooks configurados

### No Claude

- [ ] Primeiro prompt de validação enviado (forçou leitura CLAUDE.md + FRAMEWORK-STATUS)
- [ ] `/gsd:bootstrap` executado com sucesso
- [ ] `ROADMAP.md` revisado e ajustado
- [ ] Strategy de slicing escolhida
- [ ] Orchestrator mode escolhido (recomendado: inline)
- [ ] `visual_tokens_mode` definido
- [ ] `/gsd:plan-phase M0-<slug>` executado
- [ ] SPRINT.md revisados
- [ ] `/gsd:plan-phase sprint-01-<slug>` executado
- [ ] **Prompt de forçar leitura de skills enviado** (Claude colou linhas literais)
- [ ] PLAN.md revisado
- [ ] `/gsd:execute-phase sprint-01-<slug>` executado
- [ ] Divergências de reconcile resolvidas
- [ ] DoD testada manualmente
- [ ] `bin/collect-metrics.sh sprint-01-<slug>` executado
- [ ] Retrospectiva preenchida HONESTAMENTE

---

## SINAIS DE QUE ESTÁ FUNCIONANDO

Depois de 3-5 sprints, você deve ver em `.planning/METRICS.md`:

- `Fix Iter` caindo sprint a sprint
- `Plan Rev` estabilizando em 1-2
- `Gates Bypass` raro, com motivo real quando acontece
- Scores de compreensão ≥ 3.5 consistentes

## SINAIS DE PROBLEMA

- `Plan Rev` > 3 repetido → planner não entende o projeto, volte ao project-brief
- `Fix Iter` > 2 → skills citadas não foram aplicadas, insista na Fase 7.2
- `Gates Bypass` frequente → framework está atrapalhando, revise matriz
- Score < 3 → ambiguidade grande em docs/specs
