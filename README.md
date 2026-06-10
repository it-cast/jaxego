# GSD Framework — Get Shit Done universal, com gates que funcionam

> Framework de execução disciplinada para Claude Code. Mesmo framework em qualquer projeto — o **contexto do projeto** vive em arquivos separados, editáveis.

**Versão:** v0.9.7 — fidelidade de wireframe enforced ponta a ponta (`wireframe-contract` + ui-phase 2.5 + Dimension 7 + Gate 8), sobre a base de enforcement da v0.9.6: Gate 8 validado por script (`gsd-tools verify quality-bar` + hook bloqueante), partição de waves determinística (`gsd-tools partition`), fingerprints de aplicação 73/73 skills, owasp-security reescrita em profundidade sênior, drift docs↔código corrigido e prevenido por teste. 73 skills, 45 agentes, 93 commands, 8 gates (7 enforced por código), 10 suites de teste. **Ainda sem field data validado em projeto real** — esta versão melhora a verificabilidade, não a validação; o próximo passo continua sendo rodar um projeto ponta a ponta e exportar telemetria. Ver `FRAMEWORK-STATUS.md > v0.9.6`.

### Começando em 1 comando

```
# 1. jogue tudo que você tem do projeto em projeto/ (docs, wireframes, regras, stack)
# 2. rode:
/gsd:go
```

`/gsd:go` detecta o estado do projeto e roteia: projeto novo → ingest → bootstrap → autopilot, com pausas só onde decisão humana é obrigatória. Projeto em andamento → continua do ponto exato. Você não precisa decorar os 93 comandos.

## O que resolve

Frameworks anteriores (GSD v1/v2) tinham bons agentes e workflows mas **sem enforcement**. Skills instaladas nunca consultadas, UI-SPECs pulados em favor de código ad-hoc, bugs de integração só no audit semanas depois, documentação divergindo do código.

Este framework:
- **Separa framework de projeto** — `CLAUDE.md` é genérico, `docs/` e `specs/` são do projeto
- **Aplica 8 gates bloqueantes** — UI-SPEC antes de PLAN, skills enforcement, security baseline, integration check, reconciliation, senior quality bar (Gate 8)
- **Grava todo passo** — `.planning/phases/<N>/EXECUTION-LOG.md` é rastro completo
- **Reconcilia artefato ↔ código** — `/gsd:reconcile-state` verifica afirmações no código real

---

## Arquitetura

```
seu-projeto/
├── CLAUDE.md                     ← contrato do framework (genérico, não editar)
├── .claude/                      ← framework (copy-paste entre projetos)
│   ├── get-shit-done/
│   │   ├── workflows/            ← bootstrap, plan-phase, execute-phase, ui-phase, reconcile-state, ...
│   │   ├── references/           ← gates-v3.md, skills-enforcement.md
│   │   └── templates/            ← PLAN.md, UI-SPEC.md, SUGGESTIONS.md, ...
│   ├── skills/                   ← catálogo com triggers.yaml
│   └── agents/                   ← agentes gsd-* (herdados do GSD base)
├── docs/                         ← PROJETO — você preenche
│   ├── project-brief.md          ← visão, público, valor único, fases propostas
│   ├── adrs/                     ← decisões arquiteturais de longo prazo
│   └── identidade-visual/
│       ├── design-system.md      ← tokens, tipografia, componentes canônicos
│       ├── tokens.json           ← mesmo conteúdo, machine-readable
│       └── brand.md              ← tom de voz, vocabulário
├── specs/                        ← PROJETO — você preenche
│   ├── project.yaml              ← nome, owner, locale, domínio
│   ├── stack.yaml                ← linguagem, framework, banco, observability
│   ├── database.yaml             ← convenções de schema
│   └── rules.yaml                ← regras de negócio invariantes
└── .planning/                    ← GERADO pelo framework a partir de docs/ + specs/
    ├── PROJECT.md                ← síntese do projeto
    ├── ROADMAP.md                ← fases, plans, flags (ui/mobile/integration_check)
    ├── STATE.md                  ← onde estou, próximo passo
    ├── REQUIREMENTS.md
    ├── MILESTONES.md
    ├── DECISIONS.md              ← log de decisões cotidianas
    ├── SUGGESTIONS.md            ← sugestões descobertas durante execução
    ├── TECH-DEBT.md              ← dívida contabilizada
    ├── config.json               ← gates ativos, perf budget
    └── phases/<NN>-<slug>/       ← artefatos por fase
        ├── CONTEXT.md
        ├── UI-SPEC.md            ← obrigatório se fase tem ui:true
        ├── RESEARCH.md           ← com Security Baseline se fase tem risco
        ├── PLAN.md               ← com Skills Consultadas + Threat model + Observ checklist
        ├── EXECUTION-LOG.md
        ├── RECONCILIATION.md     ← obrigatório antes de fechar fase
        ├── SUGGESTIONS.md        ← promovidas para global ao fechar fase
        └── REVIEW.md
```

### Por que esta separação?

- **Trocar projeto** = substituir `docs/` + `specs/` e rodar `/gsd:bootstrap`. Framework intocado.
- **Atualizar framework** = pull do repo de framework. Contexto de projeto intocado.
- **Contrato mestre** (`CLAUDE.md`) não muda, não conflita, não diverge entre projetos.

---

## Os 8 gates bloqueantes

| Gate | Bloqueia | Onde é aplicado | Override |
|------|----------|-----------------|----------|
| **1. Bootstrap** | Qualquer workflow | Entrada de todo workflow | Não existe |
| **2. UI-SPEC** | `plan-phase` de fase com ui:true sem UI-SPEC.md | plan-phase entry | `--skip-ui --reason "..."` (DECISIONS.md) |
| **3. Skills coverage** | Plano com 2+ skills obrigatórias não citadas | plan-checker | Dispensar em `## Skills Dispensadas` com justificativa |
| **4. Security baseline** | plan-phase de fase com endpoint/auth/PII sem Security Baseline | plan-phase entry | `--skip-security --reason "..."` |
| **5. Integration check** | execute-phase com integration_check declarado e gaps | pós-execute-phase | Não existe (gap = hotfix) |
| **6. Reconciliation** | verify-phase sem RECONCILIATION.md CLEAN | verify-phase entry | Resolver gaps ou documentar em DECISIONS |
| **7. Tests + Lint** | Fechar plano sem `make test` + `make lint` verdes | Antes do commit | Não existe |

Detalhes completos em `.claude/get-shit-done/references/gates-v3.md`.

---

## Primeiro uso (projeto novo)

### 1. Copiar framework para o projeto

```bash
# Em projeto novo
cd meu-projeto/
# Copiar CLAUDE.md e .claude/ do framework
cp -r /caminho/do/gsd-framework/CLAUDE.md ./
cp -r /caminho/do/gsd-framework/.claude ./
# Copiar templates de docs/ e specs/ (vai preencher)
cp -r /caminho/do/gsd-framework/docs ./
cp -r /caminho/do/gsd-framework/specs ./
```

### 2. Preencher docs/ e specs/

Arquivos obrigatórios (bootstrap bloqueia sem eles):
- `docs/project-brief.md` — visão, público, diferenciais, fases
- `specs/project.yaml` — nome, owner, locale, domínio
- `specs/stack.yaml` — linguagem, framework, banco

Arquivos recomendados (ativam skills extras):
- `specs/database.yaml` — se projeto tem banco
- `specs/rules.yaml` — regras de negócio invariantes
- `docs/identidade-visual/design-system.md` — se projeto tem UI
- `docs/identidade-visual/brand.md` — tom de voz

### 3. Rodar bootstrap

```bash
claude-code /gsd:bootstrap
```

O bootstrap:
1. Lê todos os arquivos em `docs/` + `specs/`
2. Apresenta síntese ao humano
3. Gera `.planning/PROJECT.md`, `ROADMAP.md` (com flags), `STATE.md`
4. Gera `.planning/config.json` com gates apropriados
5. Commit inicial

### 4. Começar a trabalhar

```
/gsd:discuss-phase 1       # captura decisões
/gsd:ui-phase 1            # se fase tem ui:true (obrigatório)
/gsd:research-phase 1      # se fase tem endpoints/auth/PII
/gsd:plan-phase 1          # gate de UI-SPEC + skills + security aplicados aqui
/gsd:execute-phase 1       # waves paralelas + integration check auto
/gsd:reconcile-state 1     # prometido vs código real (obrigatório antes de fechar)
/gsd:verify-phase 1        # success criteria do ROADMAP
```

---

## Como plugar em projeto existente

Se você já tem um projeto rodando e quer adotar este framework:

1. **Copiar framework (sem docs/ e specs/):**
   ```bash
   cd projeto-existente/
   cp /path/framework/CLAUDE.md ./
   cp -r /path/framework/.claude ./
   ```

2. **Criar `docs/` e `specs/` a partir do projeto atual:**
   - Se já tem `docs/project-spec/adrs/` → mover para `docs/adrs/`
   - Se já tem identidade visual → mover para `docs/identidade-visual/`
   - Escrever `docs/project-brief.md` descrevendo o projeto como está hoje
   - Preencher `specs/*.yaml` conforme a stack real

3. **Rodar bootstrap com reconcile mode:**
   ```
   /gsd:bootstrap --import-existing
   ```
   Isso:
   - Lê `docs/` + `specs/`
   - Detecta código já escrito
   - Gera `PROJECT.md` e `ROADMAP.md` com fases passadas marcadas como COMPLETE
   - Gera `.planning/phases/*/RECONCILIATION.md` inicial mapeando o que já existe

4. **Primeiro `/gsd:reconcile-state` completo:**
   - Verifica toda afirmação declarada no bootstrap contra o código
   - Popula `TECH-DEBT.md` com gaps encontrados
   - Popula `SUGGESTIONS.md` com melhorias observadas

5. **Seguir normalmente** — próxima fase começa com `/gsd:discuss-phase <next>`.

---

## Como adicionar skill nova

1. Decidir categoria: `.claude/skills/{quality, product, mobile, br, meta}/`
2. Criar `SKILL.md` com seções padrão (ver skill existente como exemplo)
3. Criar `triggers.yaml` declarando quando a skill é obrigatória:
   ```yaml
   name: minha-skill
   category: quality
   required_for:
     - task_type: new_endpoint
     - path_pattern: "backend/app/**"
     - keyword_any: ["cache", "redis"]
   recommended_for: []
   dispensable_if: []
   ```
4. Atualizar `.claude/skills/SKILLS_INDEX.md`
5. Se skill é 🔒 obrigatória para algum tipo de task, atualizar matriz em `.claude/get-shit-done/references/skills-enforcement.md`

Pronto. Próximo `gsd-plan-checker` já vai reconhecer.

---

## Métricas de saúde

Rodar `/gsd:health` para scan completo. Métricas alvo:

- Taxa de fix commits por fase: **< 15%**
- Tempo bug → detecção: **< 1 dia**
- Divergências pós-reconcile: **zero**
- Skills citadas por plano com código: **≥ 3**
- Revisions do plan-checker por fase: **≤ 3**

Métricas degradadas indicam gates desregulados — revisar e ajustar.

---

## O que NÃO está neste framework (e por quê)

- **Agentes gsd-*** (gsd-planner, gsd-phase-researcher, gsd-ui-researcher, etc.) — herdam do GSD base. Copiar de projeto GSD existente para `.claude/agents/`.
- **Workflows originais** (discuss-phase.md, research-phase.md, verify-phase.md, etc.) — idem, copiar de GSD base. Este framework modifica apenas **3 workflows críticos**: `plan-phase.md`, `execute-phase.md`, `ui-phase.md`. Os outros continuam funcionando como no GSD v2.
- **Skills antigas** (`ui-ux-pro-max`, `owasp-security`, `design-to-code`, etc.) — idem, copiar. Este framework adiciona 10 skills novas para cobrir os gaps identificados (performance, error-ux, observability, a11y, etc.).

Resumo: **este framework é a camada de enforcement + novas skills + separação de contexto, aplicada sobre o GSD base existente.**

---

## Arquivos-chave para revisar antes de adotar

Leitura obrigatória:
1. `CLAUDE.md` — contrato mestre
2. `.claude/get-shit-done/references/gates-v3.md` — os 8 gates em detalhe
3. `.claude/get-shit-done/references/skills-enforcement.md` — como skills são enforced
4. `.claude/get-shit-done/workflows/bootstrap.md` — primeiro workflow a rodar

Leitura recomendada:
5. `.claude/get-shit-done/workflows/plan-phase.md` — como Gates 2, 3, 4 se aplicam
6. `.claude/get-shit-done/workflows/execute-phase.md` — Gate 5 em ação
7. `.claude/get-shit-done/workflows/reconcile-state.md` — Gate 6 em ação
8. `.claude/skills/SKILLS_INDEX.md` — catálogo de skills

---

## Troubleshooting

**"Bootstrap bloqueia porque docs/project-brief.md está vago"** → é por design. O framework não inventa projeto. Preencha antes.

**"Plan-checker entra em loop"** → limite 3 iterações. Se escalar ao humano, revisar triggers.yaml das skills envolvidas (pode haver matching errado).

**"Integration-checker falsa-positivo"** → grep pegou comentário. Usar `--skip-integ-verify INTEG-01 --reason "..."` uma vez; se recorrente, melhorar heurística do checker.

**"Reconciliation sempre encontra gaps"** → código divergindo do plan é normal no começo. Com o tempo, a disciplina melhora. Monitorar a métrica "divergências por reconcile" — deve cair.

**"Quero customizar perf budget ou observability fields"** → editar `.planning/config.json`. Registrar mudança em DECISIONS.md.

---

## Próximos passos sugeridos

Depois de rodar este framework em 1-2 fases:

1. Expandir as skills esqueleto mais relevantes ao seu projeto (ex: se projeto é mobile, expandir `mobile/offline-first`)
2. Adicionar skills específicas do seu domínio em `.claude/skills/<seu-dominio>/`
3. Ajustar thresholds de `config.json` com base em métricas reais
4. Criar ADRs para decisões importantes que surgirem

---

**Licença:** Framework é template/structural. Adote, modifique, evolua conforme seu contexto.

**Feedback:** o framework é evolutivo. Sugestões descobertas durante uso vão para `.planning/SUGGESTIONS.md` — revisitar mensalmente.
