# INSTALLATION — do zip ao primeiro sprint rodando

Tutorial passo a passo, ordem fixa. Siga linha por linha. Tempo estimado: **45-90 minutos** (preenchimento de docs é a parte que demora).

---

## Pré-requisitos

Antes de começar, confirme:

- [ ] **Claude Code instalado** (ou Claude.ai com projeto)
- [ ] **Node.js 18+** (para os hooks)
- [ ] **Python 3.10+** (para `bin/convert-docs.sh` e scripts de `ui-ux-pro-max`)
- [ ] **pandoc** opcional mas recomendado: `brew install pandoc` / `apt install pandoc`
- [ ] **Git** configurado
- [ ] **GSD base instalado** ✨ crítico — ver seção abaixo

---

## PARTE 0 — Entender o que você tem vs. o que precisa

**Este framework contém:**
- ✅ 44 skills em `.claude/skills/`
- ✅ 1 agente orchestrator em `.claude/agents/meta-orchestration/gsd-orchestrator.md`
- ✅ 9 hooks em `.claude/hooks/`
- ✅ Workflows, templates, references em `.claude/get-shit-done/`
- ✅ Specs templates em `specs/`, `docs/`
- ✅ Scripts em `bin/`

**Este framework NÃO contém (precisa instalar separado):**
- ❌ ~35 outros agentes GSD (`gsd-planner`, `gsd-plan-checker`, `gsd-ui-checker`, `gsd-executor`, etc.)
- ❌ ~73 slash commands GSD (`/gsd:bootstrap`, `/gsd:plan-phase`, `/gsd:execute-phase`, etc.)

**Como instalar o GSD base:**

Se você tem o GSD em outro projeto seu, copie `.claude/agents/` e `.claude/commands/` dele. Ou instale globalmente em `~/.claude/` (o Claude Code encontra skills/agents em `~/.claude/` antes de `.claude/` do projeto).

Se você não tem o GSD, **o framework ainda funciona como biblioteca de referência** (skills + hooks + workflows manuais), mas você perde a automação dos slash commands. Neste caso, pula para "Modo fallback" no final deste doc.

---

## PARTE 1 — Descompactar e posicionar (5 minutos)

### 1.1 Descompactar

```bash
cd ~/projetos        # ou onde você guarda projetos
unzip gsd-framework.zip
cd gsd-framework
```

### 1.2 Renomear para o nome do seu projeto

```bash
cd ..
mv gsd-framework meu-projeto-real
cd meu-projeto-real
```

### 1.3 Inicializar git

```bash
git init
git add .
git commit -m "chore: inicializar projeto a partir do gsd-framework v0.3.0"
```

### 1.4 Validar integridade do framework

```bash
bash tests/framework/run-all.sh
```

**Esperado:** `11/11 suites passed`. Se quebrar, não prossiga — me avise antes de investir tempo preenchendo docs.

---

## PARTE 2 — Preencher documentação obrigatória (30-60 min)

Esta é a parte longa. O framework **depende** desses arquivos para funcionar. Sem eles preenchidos, o bootstrap falha.

### 2.1 Documentação do projeto — `docs/project-brief.md` (10-15 min)

Abrir o arquivo. Tem 12 seções com placeholders `{ex: ...}`. Preencher cada uma. Não pular.

**Campo crítico:** "Usuário-alvo". Decide a estratégia de slicing depois.

- Se é consumidor externo (cliente, paciente, aluno, etc.) → slicing `vertical_value`
- Se é operador interno (atendente, financeiro, gerente) → slicing `admin_first`

### 2.2 Specs estruturadas (10 min)

Editar os 4 arquivos em `specs/`:

- `specs/project.yaml` — nome, slug, locale (`pt-BR` ou outro), plataformas
- `specs/stack.yaml` — backend/frontend/mobile/DB/infra
- `specs/database.yaml` — tabelas principais + colunas
- `specs/rules.yaml` — regras de negócio críticas

### 2.3 Identidade visual — OBRIGATÓRIO SE TEM UI (15-30 min)

```bash
cd docs/identidade-visual
```

Editar os 3 canônicos:

#### `tokens.json`

**Crítico.** Sprints com UI bloqueiam se este arquivo estiver incompleto.

Preencher mínimo com categorias `color` + `space`. Se não tem design pronto, inventar 5 cores + 5 espaçamentos razoáveis — refinar depois.

Estrutura esperada (Style Dictionary):
```json
{
  "color": {
    "brand": { "500": { "value": "#3b82f6" } },
    "text": { "primary": { "value": "#111827" } },
    "surface": { "default": { "value": "#ffffff" } },
    "border": { "default": { "value": "#e5e7eb" } },
    "semantic": { "danger": { "value": "#ef4444" } }
  },
  "space": {
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" }
  }
}
```

Completar depois com `radius`, `typography`, `motion` conforme design amadurecer.

#### `brand.md`

Voz, tom, vocabulário canônico. Skill `br/ux-copywriting-ptbr` consome este arquivo — sem ele, copy vira adivinhação.

#### `design-system.md`

Documentação humana dos tokens. Opcional no dia 1, preenchido durante os primeiros sprints.

### 2.4 Arquivos extras em `docs/` (variável)

Tem pitch em PDF? Pesquisa em XLSX? Brief do founder em DOCX? Pode jogar em `docs/business/`, `docs/research/`, etc.

**Para XLSX/DOCX/PPTX:** rodar conversão antes:

```bash
bash bin/convert-docs.sh
```

Gera espelho `.md` ao lado de cada arquivo binário. O Claude lê o `.md`.

### 2.5 Wireframes em HTML/JSX (opcional)

Se gerou wireframes no v0/Lovable/Bolt, salva em:

```
docs/identidade-visual/wireframes/create-listing-mobile.html
docs/identidade-visual/wireframes/checkout-desktop.jsx
```

**Listar no INDEX.md** da pasta:

```bash
# docs/identidade-visual/wireframes/INDEX.md já tem template
# Editar para listar seus wireframes
```

### 2.6 Rodar organizador de docs

```bash
# Após adicionar arquivos, rodar:
/gsd:docs-update
```

Detecta arquivos sem descrição em INDEX.md, pede pra você descrever, organiza.

---

## PARTE 3 — Configurar hooks (5 min)

Os hooks rodam via `.claude/settings.json`. Verificar se o arquivo tem a seção de hooks:

```bash
cat .claude/settings.json | head -50
```

Se não tem seção `"hooks": {...}`, copiar do `.claude/hooks/README.md` (tem exemplo completo de `settings.json` pronto).

Dar permissão aos scripts bash:

```bash
chmod +x .claude/hooks/*.sh
chmod +x bin/*.sh
```

---

## PARTE 4 — Primeiro prompt no Claude (10 min)

Abrir o projeto no Claude Code (ou Claude.ai) e rodar **na ordem**:

### 4.1 — Bootstrap

```
/gsd:bootstrap
```

**O que vai acontecer:**
- Claude lê `docs/project-brief.md`, `specs/*.yaml`, `docs/identidade-visual/*`
- Apresenta síntese: nome do projeto, stack, docs detectados, gaps
- Pede confirmação: prossigo?
- **Pergunta estratégia de slicing** (A vertical_value / B admin_first) — com sugestão baseada em quem é o usuário-alvo
- **Pergunta sobre orchestrator** — recomendo escolher **opção 2 (fallback inline)** para começar
- **Pergunta sobre `visual_tokens_mode`** — se tokens.json está incompleto, você escolhe `final` (completo), `provisional` (OK começar, revisar antes sprint 3), ou para e preenche

Depois de tudo confirmado, gera:
- `.planning/PROJECT.md` — síntese consolidada
- `.planning/ROADMAP.md` — roadmap inicial com milestones
- `.planning/STATE.md` — estado zerado
- `.planning/REQUIREMENTS.md`, `MILESTONES.md`, `DECISIONS.md`

**Tempo esperado:** 3-5 minutos de conversa + 1-2 min de geração.

### 4.2 — Revisar o roadmap gerado

Abrir `.planning/ROADMAP.md`. Conferir se os milestones fazem sentido. Se não, editar manualmente **antes** de prosseguir. É mais barato corrigir agora.

### 4.3 — Quebrar primeiro milestone em sprints

```
/gsd:sprint-plan M1-<slug-do-primeiro-milestone>
```

**O que vai acontecer:**
- Workflow lê o milestone do ROADMAP.md
- Aplica a estratégia escolhida (vertical_value ou admin_first)
- Gera 3-5 arquivos `SPRINT-NN-<slug>.md` em `.planning/sprints/`
- **Valida cada sprint** antes de persistir: Visual Contract presente (se UI), skills obrigatórias citadas, DoD testável em 30 min
- Mostra lista dos sprints com narrativa curta

**Tempo esperado:** 5-10 min.

### 4.4 — Revisar sprints gerados

Abrir cada `SPRINT-NN-*.md` em `.planning/sprints/`. Conferir:

- A narrativa reflete o que você quer? (1 parágrafo em linguagem de usuário)
- A Definition of Done é **testável por humano em 30 min**? Se precisa rodar script pra saber se passou, é grande demais
- Os tokens citados em `## Visual Contract` existem no seu `tokens.json`?

Se algum sprint não bate, editar manualmente ou rodar `/gsd:sprint-plan` de novo com `--force-strategy`.

### 4.5 — Planejar primeiro sprint

```
/gsd:plan-phase sprint-01-<slug>
```

**O que vai acontecer:**
- Gate 1 (bootstrap) — ok?
- Gate 2 (Visual Contract válido) — re-valida tokens
- Gate 4 (security baseline) — identifica risco de segurança
- Invoca `gsd-phase-researcher` + (se disponível) agentes orchestrator `backend-architect`, `frontend-developer`, `ui-ux-designer`
- Gera `PLAN.md` detalhado com tasks, contratos de API, componentes, schema
- Gate 3 (skills coverage) — plan-checker valida que todas as skills obrigatórias foram citadas

**Se bloquear:** mensagem clara com motivo. Ajustar PLAN.md ou SPRINT.md e re-rodar.

**Tempo esperado:** 10-20 min (primeira fase é mais lenta — Claude está aprendendo o projeto).

### 4.6 — Executar sprint

```
/gsd:execute-phase sprint-01-<slug>
```

**O que vai acontecer:**
- Invoca agentes de execução (`backend-developer`, `frontend-developer`, `test-writer`)
- Implementa tasks em ordem
- Gate 5 (integration check) roda durante a execução, pegando inconsistências cedo
- Testes rodam
- Gate 6 (reconcile) compara PLAN.md com código real, reporta divergências
- Gate 7 (tests/lint) bloqueia se falha

**Tempo esperado:** varia muito — 30 min para sprint pequeno, 2-3h para sprint grande.

### 4.7 — Fechar sprint com métricas

```
/gsd:metrics sprint-01-<slug>
```

**O que vai acontecer:**
- Valida: tasks completadas, gates passados, DoD cumprida
- Gera `.planning/retros/sprint-01-<slug>.md` a partir do template de retrospectiva
- **Pausa** para você preencher 3 campos qualitativos (o que funcionou, o que atrapalhou, o que faltou) + 2 scores 1-5
- Roda `bin/collect-metrics.sh` coletando dados automaticamente
- Anexa entrada em `.planning/METRICS.md`
- Pergunta se quer exportar telemetria anonimizada para compartilhar

**Tempo esperado:** 15 min (10 min de retro + 5 de coleta).

---

## PARTE 5 — Ciclo contínuo

Depois do sprint 1 fechado, o ciclo para cada próximo sprint:

```
/gsd:plan-phase sprint-02-<slug>
/gsd:execute-phase sprint-02-<slug>
/gsd:metrics sprint-02-<slug>
```

Quando o milestone acaba:

```
/gsd:sprint-plan M2-<slug-do-proximo-milestone>
# e repete
```

---

## O que esperar nas primeiras 2 semanas

**Dia 1 (hoje):** setup + sprint 1 planejado. Talvez sprint 1 executando.

**Dia 2-3:** sprint 1 executando. Vai aparecer **fricção real** — skill citada não foi lida a fundo, gate bloqueia por motivo inesperado, reconcile reporta divergência. **Isso é o framework trabalhando.** Anotar o que atrapalhou para a retro.

**Dia 4-5:** sprint 1 fechado. Primeiras métricas em `.planning/METRICS.md`. Fazer retro honesta.

**Semana 2:** sprint 2 planejado usando aprendizado do sprint 1. Deve fluir mais rápido — você já sabe o que Claude sabe ler e o que precisa explicitar.

**Sinal de saúde:**
- `fix_iterations` (PRs de correção pós-close) caindo ao longo dos sprints
- `plan_revisions` (reescritas do PLAN) estabilizando em 1-2
- `gates_bypassed` aparecendo raramente e sempre com `--reason` real

**Sinal de problema:**
- Skills citadas em PLAN mas não aplicadas no código — reconcile deveria pegar, mas pode não pegar em falhas sutis. **Pedir explicitamente ao Claude: "liste as 3 regras da skill X que você aplicou neste sprint"**
- Plan-checker bloqueando por matéria bobeira repetida — ajustar `sprint_ui_matrix` em `skills-enforcement.md`
- `fix_iterations` > 2 em vários sprints — framework não está puxando peso, possível motivo: planner não está lendo as skills, só citando

---

## Quando algo quebra

### `command not found: /gsd:bootstrap`

GSD base não está instalado. Duas opções:

1. Instalar GSD em `~/.claude/` global
2. Usar o **modo fallback** (próxima seção)

### Sprint bloqueia em "token_not_in_design_system"

Token citado no SPRINT.md não existe em `tokens.json`. Ou adicionar o token ao JSON, ou trocar a citação por um que existe.

### Hook avisa "CRITICAL: context 25%"

Claude está ficando sem contexto. Salvar estado do sprint (`.planning/STATE.md`) e começar sessão nova. O hook `gsd-context-monitor` avisa antes de virar problema.

### Skill foi citada mas código viola regra dela

Rodar `/gsd:reconcile-state` (ou `reconcile-state` workflow). Se não pegar, reportar — é problema que queremos detectar com dados reais para v0.4.

---

## Modo fallback (sem GSD base instalado)

Se você não tem o GSD base e não quer/pode instalar, o framework funciona como **biblioteca de referência manual**:

1. Abrir Claude e passar manualmente:
   ```
   Leia .claude/get-shit-done/workflows/bootstrap.md e execute o fluxo 
   descrito ali lendo meus docs/ e specs/.
   ```

2. Para planejar sprint:
   ```
   Leia .claude/get-shit-done/workflows/gsd:sprint-plan.md e .claude/get-shit-done/references/sprint-slicing.md.
   Depois, para o milestone M1, quebre em sprints seguindo a estratégia 
   vertical_value. Use o template .claude/get-shit-done/templates/SPRINT.md.
   ```

3. Para cada sprint:
   ```
   Implemente o sprint-01 seguindo o plano em .planning/sprints/sprint-01.md.
   Antes de codar, leia e aplique: quality/accessibility-pro, 
   product/component-library-governance, br/ux-copywriting-ptbr, 
   ux-advanced/design-tokens-system, ui-ux-pro-max.
   ```

Mais verbose, mais manual, mas funciona. Você mantém toda a disciplina do framework (skills, gates conceituais, visual contract, reconcile) — só perde a automação dos slash commands.

---

## Checklist da primeira semana

- [ ] Zip descompactado, git inicializado
- [ ] `bash tests/framework/run-all.sh` → 5/5 verde
- [ ] `docs/project-brief.md` preenchido
- [ ] `specs/*.yaml` preenchidos (4 arquivos)
- [ ] `docs/identidade-visual/tokens.json` com mínimo de `color` + `space`
- [ ] `docs/identidade-visual/brand.md` preenchido
- [ ] Arquivos extras (PDFs, XLSX) jogados em `docs/business/` ou `docs/research/` e listados nos INDEX.md
- [ ] `bash bin/convert-docs.sh` rodado (se tem binários)
- [ ] Hooks configurados em `.claude/settings.json` + `chmod +x` nos `.sh`
- [ ] GSD base instalado (ou decisão consciente de usar modo fallback)
- [ ] `/gsd:bootstrap` rodado com sucesso
- [ ] Estratégia de slicing escolhida (vertical_value ou admin_first)
- [ ] `.planning/ROADMAP.md` revisado e ajustado
- [ ] `/gsd:sprint-plan M1-<slug>` rodado
- [ ] 3-5 SPRINT.md revisados e aprovados
- [ ] `/gsd:plan-phase sprint-01-<slug>` rodado
- [ ] Primeiro sprint executando ou executado
- [ ] `/gsd:metrics sprint-01-<slug>` rodado com retro preenchida honestamente

Se você chegou no último item, parabéns — o framework está respirando no seu projeto. A próxima conversa comigo pode ser baseada em dados reais (`.planning/METRICS.md`) em vez de especulação.

---

## Perguntas que você provavelmente vai ter

**"Posso pular o bootstrap e ir direto pro sprint planning?"**
Não. Bootstrap gera `config.json > slicing_strategy` que é consumido pelo sprint-plan. Pular faz o workflow falhar ou usar defaults errados.

**"Preciso preencher TODOS os ADRs antes de começar?"**
Não. Só os que já tem decisão. Outros vão surgir durante sprints e são adicionados incrementalmente.

**"Minha stack não é Python/Angular — o framework serve?"**
Serve. Skills `domain/mysql-schema-design`, `domain/angular-material-patterns` e `domain/ionic-patterns` são específicas mas ignoráveis se não aplicam. As outras 41 skills são stack-agnósticas ou adaptáveis.

**"Devo commitar `.planning/` no repo?"**
Sim. É o log decisório do projeto. Sem ele, perde histórico de por que cada escolha foi feita.

**"Posso modificar as skills?"**
Sim, são suas. Mas se customizar muito, dificulta upgrade para v0.4/0.5. Prefiro: adicionar skills novas em `.claude/skills/custom/` em vez de editar as core.

**"E se o Claude citar uma skill mas não aplicar as regras dela?"**
Problema real e conhecido. Mitigação: explicitamente peça "antes de codar, abra e liste as 3 regras principais de skill X" nos primeiros sprints. Em 2-3 sprints vira automático.
