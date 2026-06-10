# CLAUDE.md — Contrato de Execução do Framework

> **Leia este arquivo por inteiro antes de fazer qualquer coisa nesta sessão.**
> **Este é o onboarding canônico. Vale para todo projeto usando o gsd-framework.**
> **O que muda por projeto: `docs/`, `specs/`, `.planning/`. ESTE arquivo não muda.**

**Framework:** gsd-framework v0.9.7
**Status autodeclarado:** 8.3/10 (sem field data ainda — ver FRAMEWORK-STATUS.md)

> 📘 **Notas de plataforma e limitações conhecidas:** veja `docs/PLATFORM-NOTES.md` (Windows / macOS / Linux specifics) e `docs/KNOWN-LIMITS.md` (limitações conscientes do framework). Esses documentos substituem o antigo `ERRATA.md` — framework não tem erratas, tem notas de plataforma e limitações documentadas.

> ⚠️ **PERMISSÕES — bypass total ativado por default** — `.claude/settings.json` vem com `defaultMode: bypassPermissions`. Claude executa Bash/Read/Write/Edit sem pedir confirmação. Sua rede de segurança é **git frequente**. Para mudar, ver `PERMISSIONS.md`.

---

## 1. Identidade do framework em 1 parágrafo

Framework de execução disciplinada para Claude Code, em pt-BR. Combina: (a) ciclo de planejamento em phases (bootstrap → discuss → plan → execute → verify), (b) catálogo de 73 skills enforced via plan-checker, (c) 8 gates bloqueantes que impedem atalhos, (d) 45 agentes especializados invocáveis, (e) 93 slash commands (incluindo `/gsd:go` entrada única e `/gsd:autopilot` v0.9.5-aware), (f) 19 hooks operacionais (statusline, context monitor, workflow guard), (g) motor CLI `gsd-tools.cjs` para operações atômicas sobre STATE.md/ROADMAP.md/config.json. **Objetivo:** separar projeto disciplinado de vibe-coded via fricção planejada.

---

## 2. O que o Claude PRECISA ler antes de começar

Em ordem, sem pular:

1. **Este arquivo** (CLAUDE.md) — contrato
2. **FRAMEWORK-STATUS.md** — versão atual e **limitações conhecidas**. Leia especialmente a seção "O que esta versão NÃO resolve" do v0.4.0.
3. **docs/project-brief.md** — identidade do projeto, usuário-alvo, escopo, fora-de-escopo
4. **specs/project.yaml + stack.yaml + database.yaml + rules.yaml** — metadata estrutural e regras de negócio
5. **docs/identidade-visual/tokens.json + brand.md + INDEX.md** — se projeto tem UI
6. **.planning/STATE.md** — onde o projeto está AGORA (qual fase, qual sprint, qual task)
7. **.planning/ROADMAP.md** — onde o projeto quer chegar
8. **docs/*/INDEX.md** — o que há nas subpastas com que peso (canônico / alta / referência / histórico)

**Ao declarar leitura, demonstrar:** não responder "li tudo" de forma genérica. Listar cada arquivo com 1 frase do que contém. Se o humano pedir, colar linha literal de parte importante.

---

## 3. Fontes de verdade — hierarquia

| Pergunta | Arquivo fonte |
|---|---|
| O que é este projeto? Dono? Usuário-alvo? | `docs/project-brief.md` |
| Stack técnica fechada | `specs/stack.yaml` |
| Schema do banco | `specs/database.yaml` |
| Regras de negócio invariantes | `specs/rules.yaml` |
| Metadata (nome, slug, locale) | `specs/project.yaml` |
| Decisões arquiteturais | `docs/adrs/ADR-*.md` |
| Design tokens, voz, copy, motion | `docs/identidade-visual/` |
| Onde estou? Em que sprint? Em que task? | `.planning/STATE.md` |
| Sequência de milestones/fases | `.planning/ROADMAP.md` |
| Requisitos numerados | `.planning/REQUIREMENTS.md` |
| Milestones definidos | `.planning/MILESTONES.md` |
| Decisões ao longo do caminho | `.planning/DECISIONS.md` |
| Dívidas técnicas contabilizadas | `.planning/TECH-DEBT.md` |
| Sugestões descobertas em execução | `.planning/SUGGESTIONS.md` |
| Métricas acumuladas por sprint | `.planning/METRICS.md` |
| Retrospectivas de sprint | `.planning/retros/sprint-NN-*.md` |
| Contexto de uma fase específica | `.planning/phases/NN-<slug>/CONTEXT.md` |
| Design contract de fase com UI | `.planning/phases/NN-<slug>/UI-SPEC.md` |
| Plano executável de fase | `.planning/phases/NN-<slug>/PLAN.md` |
| Rastro de execução | `.planning/phases/NN-<slug>/EXECUTION-LOG.md` |
| Prometido vs. código real | `.planning/phases/NN-<slug>/RECONCILIATION.md` |
| Sprint definition | `.planning/sprints/SPRINT-NN-<slug>.md` |

**Regra:** se está em `docs/` ou `specs/`, é LEI do projeto — Claude não inventa, propõe ADR nova. Se está em `.planning/`, é estado vivo — Claude atualiza ao fechar uma fase.

---

## 4. As 12 regras invioláveis

### Regra 1 — Bootstrap antes de QUALQUER execução
Sem `.planning/` populado, primeiro comando é **sempre** `/gsd:bootstrap`. Ele lê docs+specs, pergunta strategy (vertical_value/admin_first), orchestrator mode, visual_tokens_mode, e gera `.planning/` inicial. **Sem bootstrap, nada começa.**

### Regra 2 — STATE.md é a fonte de truth sobre "onde estou"
Cada sessão começa lendo `.planning/STATE.md`. Ele aponta para a fase, sprint, plano e task **exatos**. Claude executa o que está apontado, não o que parece urgente.

### Regra 3 — Plano só fecha com gates verdes
1. **Bootstrap ok** — `.planning/PROJECT.md` existe e coerente
2. **Visual Contract** — se `has_ui:true`, tokens citados existem em `tokens.json`
3. **Skills coverage** — obrigatórias citadas em `## Skills Consultadas` ou `## Skills Dispensadas (com justificativa)`
4. **Security baseline** — para endpoints/auth/PII, seção obrigatória no research
5. **Integration check** — cross-layer validado em runtime
6. **Reconcile** — `RECONCILIATION.md` sem gaps abertos
7. **Tests + lint** — tudo verde
8. **Senior Quality Bar** (v0.9.5; enforcement por script desde v0.9.6 via `gsd-tools verify quality-bar` + hook de transição) — sem FAIL-BLOCK aberto contra `quality/senior-quality-bar` (segredo no repo, deploy irreversível, N+1 em lista, injection, endpoint sem decisão de auth, PII em log)

Se um gate não está verde, **o plano não está pronto**.

### Regra 4 — Gate de UI-SPEC é bloqueante para fases com UI
Fase com `ui:true` no ROADMAP exige UI-SPEC antes de plan-phase. Fluxo: `/gsd:discuss-phase N → /gsd:ui-phase N → /gsd:plan-phase N → /gsd:execute-phase N`. **plan-phase recusa** rodar sem UI-SPEC. Elimina redesigns retroativos.

### Regra 5 — Skills são checklist enforced, não consulta casual
`PLAN.md` **deve** ter:

```markdown
## Skills Consultadas
- `skill-name` — qual decisão do plano se baseia nela, referenciar arquivo ou regra

## Skills Dispensadas (com justificativa)
- `skill-name` — por que NÃO se aplica a esta fase
```

**ARMADILHA PRINCIPAL v0.4.0:** Gate 3 valida skill CITADA no PLAN.md — **não valida se foi LIDA e APLICADA**. Nos 3 primeiros sprints, humano precisa forçar explicitamente:

> "Antes de executar, abra `.claude/skills/<categoria>/<nome>/SKILL.md`, liste as 3 regras principais aplicáveis, cole linha literal de cada entre aspas, diga quais vai aplicar e qual NÃO vai aplicar e por quê. Não comece a codar até eu confirmar."

Depois de 3 sprints, o hábito internaliza e a fricção cai. Ver `TUTORIAL-COMPLETO.md > FASE 8.3` para prompts literais.

### Regra 6 — Integration check obrigatório em fases cross-layer
Fase com `integration_check: true` dispara `gsd-integration-checker` ao fim do execute-phase. Valida contratos reais (endpoint cliente ↔ endpoint servidor). Gaps = hotfix antes de fechar fase.

### Regra 7 — Security no researcher, não no auditor
Fases com endpoint/auth/PII: `gsd-phase-researcher` **obrigatoriamente** produz seção `Security Baseline` no RESEARCH.md consultando `owasp-security`. O threat_model do PLAN herda dessa seção. **Segurança desenhada antes, não auditada depois.**

### Regra 8 — Reconciliação antes de encerrar fase
Antes de marcar fase COMPLETE, `/gsd:reconcile-state <N>`:
1. Lê cada afirmação de entrega do PLAN
2. Roda grep/verifica código real
3. Gera RECONCILIATION.md (prometido vs. real)
4. Atualiza STATE.md, SUGGESTIONS.md, TECH-DEBT.md

Elimina artefatos divergentes.

### Regra 9 — Dívida técnica é contabilizada, sempre
Todo desvio do ideal vira linha em `.planning/TECH-DEBT.md`:

```
| ID | Descrição | Por quê | Owner | Prazo | Plan a resolver |
```

Dívida invisível = dívida impagável.

### Regra 10 — Sugestões viram persistência, não ar
Insight descoberto em execução (melhor API, refactor óbvio, skill ausente, padrão repetido) vai para `.planning/phases/<N>/SUGGESTIONS.md`. Ao fechar fase, promovidas sobem para `.planning/SUGGESTIONS.md` (visibilidade global).

### Regra 11 — Tech debt tem urgency_class, sempre (v0.8+)
Toda entry em `TECH-DEBT.md` precisa de `urgency_class` (`pre_launch_blocker`, `pre_launch_high`, `pre_launch_medium`, `post_launch_30d`, `post_launch_quarter`, `wont_fix_documented`). Sem `urgency_class` = default `post_launch_quarter`. Promoção entre classes requer ADR ou DECISIONS.md — não silenciosa.

**Plan-phase deve** consultar `TECH-DEBT.md` filtrando TDs com prazo na phase atual ou `urgency_class` apropriado, e listá-las na seção "Tech debt deste plano" do PLAN.md. Sem isso TD vencida fica esquecida (problema observado em campo: TD-08-01 tinha prazo Phase 9, Phase 9 fechou sem mencionar).

### Regra 12 — LOW confidence vira task ou TD (v0.8+)
Items marcados `confidence: LOW` em RESEARCH.md **não podem** ficar como "verifique antes de executar". Cada um vira:
- **Task explícita** no PLAN.md (com critério de aceite verificável), OU
- **Decisão consciente de adiar** registrada como TD com `urgency_class` definido

Sem isso, LOW confidence desaparece do radar entre sessões (problema observado: `apple-actions @v3` LOW confidence no Rota Certa Phase 9 nunca virou task — só falharia em primeiro tag push real).

---

## 5. Arquitetura em camadas (v0.9.5)

```
HUMANO (comandos)
     │
     ▼
SLASH COMMANDS (92)          .claude/commands/gsd/*.md
     │
     ▼
WORKFLOWS (80)               .claude/get-shit-done/workflows/*.md
     │
     ▼ (Task tool)
AGENTES (45)                 .claude/agents/*.md
                             gsd-orchestrator, gsd-planner,
                             gsd-plan-checker, gsd-executor,
                             gsd-ui-checker, gsd-verifier, etc.
     │
     ▼
SKILLS (73)                  .claude/skills/<categoria>/<nome>/
                             br, domain, meta, mobile, product,
                             quality, ux-advanced, standalone
     │
     ▼
HOOKS (9)                    .claude/hooks/
                             statusline, context-monitor,
                             workflow-guard, prompt-guard,
                             read-guard, session-state,
                             validate-commit, phase-boundary,
                             check-update

TUDO opera sobre:
gsd-tools.cjs (1158 linhas) + 24 libs
.claude/get-shit-done/bin/
Operações atômicas: state, phase, roadmap, config, commit
Requer Node 18+
```

---

## 6. Gates bloqueantes (8 — detalhe em `references/gates-v3.md`)

| Gate | Quando | Block se... |
|------|--------|-------------|
| **1. Bootstrap** | Antes de qualquer workflow | `.planning/PROJECT.md` não existe |
| **2. UI-SPEC / Visual Contract** | Antes de plan-phase | Fase tem `has_ui:true` e tokens citados não existem em `tokens.json` |
| **3. Skills coverage** | No plan-checker | 2+ skills obrigatórias não citadas no PLAN |
| **4. Security baseline** | No plan-phase | Fase com endpoint sem `Security Baseline` no RESEARCH |
| **5. Integration check** | Após execute-phase | Fase com `integration_check` sem execução do checker |
| **6. Reconciliation** | Antes de fechar fase | RECONCILIATION.md não existe ou tem gaps |
| **7. Tests + Lint** | Antes de fechar plano | make test ou make lint falhando |
| **8. Senior Quality Bar** | Em verify-phase, após reconcile | FAIL-BLOCK aberto vs `quality/senior-quality-bar` (segredo, deploy irreversível, N+1, injection, auth indefinida, PII em log) |

Bypass permitido com `--skip-gate N --reason "<motivo real>"`. Registrado em METRICS.md. Use parcimoniosamente.

---

## 7. Skills — como consultar (44 skills em 9 categorias)

Skills ficam em `.claude/skills/<categoria>/<nome>/SKILL.md`. Categorias:

- **br/** (3) — brazilian-forms, ux-copywriting-ptbr, lgpd-compliance
- **domain/** (6) — angular-material-patterns, docker-production-ready, ionic-patterns, llm-integration-patterns (869 linhas), mysql-schema-design, safe2pay-escrow-br (546 linhas)
- **meta/** (4) — design-to-code, orchestration-decision-tree, project-kickoff-interview, stack-advisor
- **mobile/** (2) — offline-first, push-notifications-architecture
- **product/** (4) — api-design-contracts, component-library-governance, micro-animations-delight, visual-regression-testing
- **quality/** (5) — accessibility-pro, error-ux-patterns, i18n-ready-architecture, observability-production, performance-web-vitals
- **ux-advanced/** (14) — chat-ux-patterns, dark-mode-theming, design-tokens-system, empty-states-polish, file-upload-ux, form-ux-mastery, gesture-touch-patterns, motion-design-patterns, onboarding-patterns, payment-checkout-ux, responsive-breakpoint-strategy, saas-dashboard-patterns, trust-safety-ux, ui-input-rich-patterns
- **standalone** (6) — owasp-security, prompt-engineering, spartan-ai-toolkit, systematic-debugging, ui-ux-pro-max (377 linhas + 437KB data + 147KB scripts), webapp-testing

### Matriz canônica `sprint_ui_matrix` (se `has_ui: true`)

**Sempre obrigatórias (5):**
- 🔒 `product/component-library-governance`
- 🔒 `quality/accessibility-pro`
- 🔒 `ux-advanced/design-tokens-system`
- 🔒 `ui-ux-pro-max` (direção estética anti-AI-slop)
- 🔒 `ux-advanced/empty-states-polish`

**Por flag:**
- `locale: pt-BR` → 🔒 `br/ux-copywriting-ptbr`
- `has_forms: true` → 🔒 `ux-advanced/form-ux-mastery` + 🔒 `quality/error-ux-patterns`
- `has_non_trivial_motion: true` → 🔒 `product/micro-animations-delight` + 🔒 `ux-advanced/motion-design-patterns`
- `touches_shared_components: true` → 🔒 `product/visual-regression-testing`

**Por contexto:**
- Mobile → 🔒 `ux-advanced/gesture-touch-patterns`
- Web responsivo → 🔒 `ux-advanced/responsive-breakpoint-strategy`
- Suporta dark mode → 🔒 `ux-advanced/dark-mode-theming`

**Por feature:**
- Auth/signup → 🔒 `ux-advanced/onboarding-patterns` + `trust-safety-ux`
- Checkout → 🔒 `ux-advanced/payment-checkout-ux` + `trust-safety-ux`
- Upload de arquivo → 🔒 `ux-advanced/file-upload-ux`
- Chat → 🔒 `ux-advanced/chat-ux-patterns`
- Dashboard SaaS/admin → 🔒 `ux-advanced/saas-dashboard-patterns` + 🔒 `ux-advanced/data-tables-ux`
- Listagem/tabela/relatório tabular → 🔒 `ux-advanced/data-tables-ux`
- Busca/filtro/período → 🔒 `ux-advanced/search-filter-ux`

**Por camada (v0.9.5):**
- `has_api: true` ou endpoint → 🔒 `domain/fastapi-production-patterns`
- CI/CD, `.github/workflows/` → 🔒 `domain/github-actions-ci`

Detalhes completos em `.claude/skills/SKILLS_INDEX.md`.

---

## 8. Workflow canônico de uma fase/sprint

```
/gsd:bootstrap                  (apenas uma vez, ao iniciar projeto)
       │
       ▼
/gsd:sprint-plan M1-<slug>     (quebra milestone em 3-5 sprints)
       │
       ▼  (para cada sprint)
/gsd:plan-phase sprint-NN-<slug>
       │
       ▼  ⚠️ HUMANO FORÇA LEITURA DE SKILLS (prompt explícito)
       │
       ▼
/gsd:execute-phase sprint-NN-<slug>
       │       │ gates 5, 6 rodam em runtime
       │       ▼
       │  reconcile automático
       ▼
/gsd:metrics sprint-NN-<slug>  (retro qualitativa + collect-metrics.sh)
       │
       ▼  (repetir para próximo sprint)

Ao fim do milestone:
/gsd:milestone-summary M1-<slug>

A cada 3-5 sprints:
bash bin/export-telemetry.sh  (gera JSON anonimizado para próxima iteração)
```

**Não pular passos.** Cada passo grava artefato em `.planning/sprints/sprint-NN-<slug>/` ou `.planning/phases/NN-<slug>/`.

---

## 9. Estratégias de slicing (escolhida no bootstrap)

**`vertical_value`** — cada sprint entrega valor ao usuário final.
- Usar quando: usuário-alvo é consumidor/cliente externo
- Exemplo: MercadoPRO (comerciante varejista)

**`admin_first`** — monta painel interno primeiro, depois UI pública.
- Usar quando: usuário-alvo é operador interno
- Exemplo: ferramenta para time de logística/financeiro

Gravada em `.planning/config.json > slicing_strategy`. Trocar no meio do projeto exige ADR.

---

## 10. Documentos que projeto suporta

**Lê nativamente:**
- `.md`, `.txt`, `.json`, `.yaml`, `.csv` — texto direto
- `.pdf` — Claude lê PDFs
- `.png`, `.jpg`, `.svg` — visão
- `.html`, `.jsx`, `.tsx` — como texto (bom para wireframes de v0/Lovable/Bolt)

**Precisa conversão via `bin/convert-docs.sh`:**
- `.xlsx`, `.xls` — gera `.xlsx.md` espelho (Markdown tabela)
- `.docx`, `.doc` — gera `.docx.md` (pandoc)
- `.pptx`, `.ppt` — gera `.pptx.md` (pandoc)

**Regra crítica:** cada subpasta em `docs/` precisa de `INDEX.md` descrevendo arquivos com relevância (canônico / alta / referência / histórico). Sem isso, Claude ignora ou lê tudo aleatório.

---

## 11. Anti-patterns aprendidos (não repita)

1. **Código frontend antes de UI-SPEC** → hex hardcoded, redesign retroativo. **Fix:** Regra 4 (gate UI bloqueante).
2. **Skills instaladas mas não consultadas** → anti-patterns que a skill proíbe aparecem no código. **Fix:** Regra 5 (skills enforced).
3. **Bugs de integração só no audit** → WebSocket URL errada, contrato divergente. **Fix:** Regra 6 (integration-checker).
4. **Security como auditor pós-fato** → JWT em localStorage, rate limit ausente. **Fix:** Regra 7 (baseline no researcher).
5. **Artefatos divergentes do código** → doc desatualizada usada para decidir próxima fase. **Fix:** Regra 8 (reconcile obrigatório).
6. **Dívida técnica invisível** → bugs em produção. **Fix:** Regra 9 (TECH-DEBT contabilizada).
7. **Insights perdidos** → mesma lição reaparece em 3 fases. **Fix:** Regra 10 (SUGGESTIONS persistente).
8. **Skill citada mas não lida** → código viola regra que a skill proíbe mesmo com citação válida. **Fix (v0.4.0):** humano força leitura com prompt específico nos 3 primeiros sprints.

---

## 12. Slash commands essenciais (subconjunto dos 82)

> **Vocabulário:** framework usa "phase" (fase) como unidade atômica dentro de milestone, não "sprint". Milestone contém múltiplas phases. Artefatos ficam em `.planning/phases/NN-<slug>/`.

**Setup e navegação:**
```
/gsd:go                       # ⭐ ENTRADA ÚNICA — detecta estado e roteia (novo, andamento, etc.)
/gsd:bootstrap                # inicial, lê docs/ e specs/ → .planning/
/gsd:new-milestone            # inicia milestone novo (brownfield)
/gsd:resume-work              # continua de onde parou (lê STATE.md)
/gsd:health                   # scan de STATE e divergências
/gsd:progress                 # resumo da fase atual
```

**Planejamento:**
```
/gsd:add-phase <desc>         # adiciona phase ao fim do milestone atual
/gsd:insert-phase <após> <desc>  # insere phase decimal (72.1) entre integers
/gsd:plan-phase <N>           # PLAN.md com skills enforcement
/gsd:discuss-phase <N>        # captura decisões → CONTEXT.md
/gsd:ui-phase <N>             # UI-SPEC.md (bloqueante se has_ui)
/gsd:research-phase <N>       # RESEARCH.md + Security Baseline
```

**Execução e validação:**
```
/gsd:execute-phase <N>        # execução wave-based, gates em runtime
/gsd:secure-phase <N>         # valida threat_model implementado
/gsd:verify-work <N>          # UAT conversacional, detecta gaps
/gsd:validate-phase <N>       # validação pós-execução
/gsd:audit-milestone          # scan global de gaps/dívida no milestone
```

**Fechamento:**
```
/gsd:milestone-summary <mv>   # fecha milestone e consolida
/gsd:complete-milestone <mv>  # arquiva milestone completo
/gsd:cleanup                  # limpa artefatos temporários
/gsd:ship                     # deploy checklist
```

**Autopilot (v0.9.4-aware — recomendado para milestone completo):**
```
/gsd:autopilot <milestone-id>       # executa milestone inteiro end-to-end
                                    # para cada phase: discuss → ui (se has_ui)
                                    # → research → plan → plan-checker → execute
                                    # → verify-work → auto-retro
                                    # respeita gates 2, 3, 4, 5, 6, 7
                                    # pausa só em: confirmação inicial, gate block,
                                    # verification failure, fim de milestone

/gsd:autopilot v1.0 --from 3        # retoma a partir da phase 3
/gsd:autopilot v1.0 --dry-run       # mostra plano sem executar
/gsd:autopilot v1.0 --text          # prompts em texto (CLIs não-Claude)
```

⚠️ **`/gsd:autopilot` vs `/gsd:autonomous`:**
- `/gsd:autonomous` é da v0.1 — bypassa sprint_ui_matrix, Visual Contract, Security Baseline
- `/gsd:autopilot` é v0.9.4-aware — respeita todos os gates, pausa só em bloqueio real
- Use **autopilot** para trabalho novo. Autonomous só se souber explicitamente por que vai bypassar.

**Utilidades:**
```
/gsd:docs-update               # mantém INDEX.md de docs/ sincronizados
/gsd:suggestions              # revisa e promove SUGGESTIONS
/gsd:td-review                # revê TECH-DEBT.md
/gsd:note <texto>             # adiciona nota à fase atual
/gsd:session-report           # snapshot da sessão
```

Lista completa: `ls .claude/commands/gsd/`

---

## 13. Configuração do framework

Arquivo: `.planning/config.json`. Principais opções:

```json
{
  "mode": "interactive",
  "granularity": "standard",
  "slicing_strategy": "vertical_value",
  "visual_tokens_mode": "final",
  "workflow": {
    "ui_phase_blocking": true,
    "skills_enforcement": true,
    "integration_check": true,
    "security_baseline": true,
    "reconcile_before_close": true,
    "auto_advance": false
  },
  "orchestrator": {
    "enabled": true,
    "fallback_mode": "inline",
    "available_agents": ["backend-architect", "frontend-developer", "..."]
  },
  "performance_budget": {
    "lcp_ms": 2500,
    "inp_ms": 200,
    "cls": 0.1,
    "bundle_main_kb_gzip": 400
  },
  "response_language": "pt-BR"
}
```

---

## 14. Métricas de saúde (revisadas em `/gsd:health`)

- **Taxa de fix commits** (`fix:`) / total. **Target: < 15%.** Alta = retrabalho, skills/gates não aplicados.
- **Tempo entre bug introduzido e detectado.** **Target: < 1 dia** (integration-checker pega no mesmo dia).
- **Divergência artefato↔código.** **Target: zero** após `/gsd:reconcile-state`.
- **Skills citadas por PLAN.** **Target: ≥ 3 por fase com código.**
- **Plan revisions** (vezes que PLAN foi reescrito). **Target: ≤ 2 por sprint.**
- **Gates bypassed** por sprint. **Target: 0. Aceitável: 1 com motivo real.**

---

## 15. Limitações conhecidas v0.4.0 (honestidade)

1. **Zero field data.** Framework teoricamente completo (596 arquivos) mas nenhum sprint real validado ainda.
2. **Workflows do upload (autonomous, ship, new-project) não conhecem enforcement v0.2+.** Usar esses workflows bypassa `sprint_ui_matrix`, `visual_tokens_mode`. Perda silenciosa.
3. **Testes são de existência, não semântica.** 5/5 verde garante arquivos estão lá; não garante conteúdo é coerente.
4. **Risco de bloat.** Múltiplos caminhos fazem a mesma coisa (command vs workflow vs agente direto). Pode confundir novatos.
5. **Plan-checker é grep, não AST.** Falsos positivos (match em comentário/string) possíveis.
6. **Skill citada ≠ skill aplicada.** Gate 3 valida citação, não aplicação. Mitigação: humano força leitura explícita (ver Regra 5).

Todas detalhadas em `FRAMEWORK-STATUS.md > v0.4.0 > O que esta versão NÃO resolve`.

---

## 16. Contrato com o humano

**O que o humano espera de você (Claude):**
- Seguir estas regras sem pular
- Ler os arquivos antes de prometer que leu (cole linha literal se duvidarem)
- Admitir incerteza quando existir — não inventar
- Marcar dívida técnica explicitamente em vez de esconder
- Executar ordem STATE.md, não o que parece urgente
- Quando humano forçar leitura de skill, fazer leitura real e provar com citação literal

**O que você (Claude) espera do humano:**
- Pré-requisitos preenchidos antes do `/gsd:bootstrap`
- Revisão do ROADMAP.md gerado (primeiro ponto de falha de alinhamento)
- Retrospectivas honestas no `/gsd:metrics`
- Telemetria exportada a cada 3-5 sprints para iteração do framework

---

## 17. Referências vivas

- `FRAMEWORK-STATUS.md` — changelog e decisões arquiteturais (v0.1 a v0.4.1)
- `docs/PLATFORM-NOTES.md` — notas de plataforma (Windows / macOS / Linux)
- `docs/KNOWN-LIMITS.md` — limitações conscientes do framework
- `PERMISSIONS.md` — como o framework lida com permissões (bypass total ativo por default)
- `GUIA-DESCOBERTA-NOVO-PROJETO.md` — protocolo para Claude conduzir descoberta antes de `/gsd:bootstrap`
- `GUIA-PROJETO-NOVO.md` — uso geral do framework (após descoberta + bootstrap)
- `GUIA-PROJETO-LEGADO.md` — adoção em código em produção
- `TUTORIAL-COMPLETO.md` — passo a passo com prompts literais
- `INSTALLATION.md` — setup resumido
- `.claude/skills/SKILLS_INDEX.md` — catálogo completo de 44 skills
- `.claude/hooks/README.md` — configuração dos 10 hooks
- `GUIA-GERACAO-DE-APLICACAO.md` — passo a passo do zero ao deploy
- `GERADOR-DE-DOCUMENTACAO.md` — prompt-mestre para gerar projeto/ via conversa
- `.claude/get-shit-done/references/gates-v3.md` — detalhe dos 8 gates
- `.claude/get-shit-done/references/skills-enforcement.md` — matriz canônica
- `.claude/get-shit-done/bin/gsd-tools.cjs --help` — comandos CLI

---

**Este contrato é lei. Para desviar: pare, proponha ADR em `docs/adrs/`, aguarde humano aprovar.**

> _"Planos são inúteis; planejar é indispensável."_ — Eisenhower. O framework garante que você planeje.

---

## 18. Sistema de Assinaturas (canônico)

Qualquer trabalho relacionado a assinaturas, planos, cobranças ou Safe2Pay
deve seguir exatamente o padrão documentado em:

→ **`docs/SAAS-BILLING-DOCS.md`**

Não inventar lógica de billing. A skill `domain/saas-billing-canonical` é
**obrigatória** para phases que tocam em billing/subscription/payment/checkout.

Triggers automáticos: features `billing`, `subscription`, `payment`, `checkout`;
integrations `safe2pay`; keywords brasileiras de cobrança.

Se SAAS-BILLING-DOCS não cobre seu caso → abrir ADR documentando a decisão
antes de codar.

---

## 19. Manual de skills (v0.9.4)

Para saber **quais skills consultar em cada momento do fluxo**, ver:

→ **`docs/SKILLS-USAGE-MANUAL.md`**

Mapeia, por momento do fluxo gsd (bootstrap, discuss-phase, ui-phase, etc.),
quais skills são obrigatórias, recomendadas e opcionais por contexto.

73 skills organizadas em 9 categorias. Plan-checker (gate 3, Dimension 6) valida
citação automática via triggers.yaml de cada skill.
