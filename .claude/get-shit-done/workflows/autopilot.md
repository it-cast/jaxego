<purpose>

Executa milestone inteiro end-to-end, respeitando todos os v0.4.x gates. Para cada phase, executa o ciclo canônico completo (discuss → ui → research → plan → plan-checker → execute → verify → reconcile → auto-retro) e **valida completude** antes de avançar.

**v0.5.0 changes vs v1.1:**
- Auto-retro agora é **bloqueante**, não opcional
- Antes de avançar entre phases, dispara `gsd-phase-completeness-checker` em modo strict
- Se artefato faltando → bloqueia + sugere `/gsd-recover-retros`
- Output 100% em pt-BR (relatórios e prompts)

</purpose>

<required_reading>
@./.planning/ROADMAP.md
@./.planning/STATE.md
@./.planning/config.json
@./CLAUDE.md
@./.claude/get-shit-done/templates/retrospective.md
</required_reading>

<process>

<step name="0-read-ingestor-handoff">

## 0. Leitura do handoff do ingestor (DECISION-50 — v0.9.1)

**ANTES** do bootstrap check, ler `.planning/INGESTOR-HANDOFF.json` se existir. Isso conecta o output do `/gsd:ingest` ao input do autopilot.

```bash
HANDOFF_FILE=".planning/INGESTOR-HANDOFF.json"

if [ -f "$HANDOFF_FILE" ]; then
  INGESTOR_VERSION=$(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).ingestor_version")
  READY=$(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).next_actions.ready_for_autopilot")
  BLOCKING_Q=$(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).counts.open_questions_blocking")
  CONFLICTS=$(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).counts.conflicts_detected")
  INGESTED_AT=$(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).ingested_at")

  if [ "$READY" = "false" ]; then
    cat << EOF
⚠  HANDOFF DO INGESTOR INDICA NÃO-PRONTIDÃO

   Ingestor rodado em: $INGESTED_AT
   Open Questions bloqueantes: $BLOCKING_Q
   Conflitos detectados: $CONFLICTS

   AÇÃO NECESSÁRIA:
   1. Abra DISCOVERY-REPORT.md na raiz do projeto
   2. Responda as $BLOCKING_Q Open Questions bloqueantes
   3. Resolva os $CONFLICTS conflitos (se houver)
   4. Rode /gsd:ingest novamente
   5. Volte a /gsd:autopilot
EOF
    exit 1
  fi

  # Handoff OK — mostrar banner informativo
  cat << INFO
🔗 HANDOFF DO INGESTOR DETECTADO

   Ingestor: $INGESTOR_VERSION ($INGESTED_AT)
   Pronto para autopilot: SIM
   Open Questions não-bloqueantes: $(node -p "JSON.parse(require('fs').readFileSync('$HANDOFF_FILE')).counts.open_questions_nonblocking")

   Procedendo com milestone $MILESTONE...
INFO
fi
```

**Por que esta step existe:**
- Conecta `/gsd:ingest` ao `/gsd:autopilot` sem ação manual do operador
- Detecta automaticamente se o operador esqueceu de resolver Open Questions bloqueantes
- Marca no `METRICS.md` que esta execução começou de um handoff (telemetria)

**Quando esta step é silenciosa:**
- Projeto bootstrappado manualmente (sem `/gsd:ingest`) — `HANDOFF_FILE` não existe, pula direto para step 1.

</step>

<step name="1-initialize">

## 1. Inicialização

Parse `$ARGUMENTS`:
- Posicional obrigatório: `<milestone-id>` (ex: `v1.0`, `M1`)
- `--from <N>` — pular para phase específica
- `--dry-run` — exibir plano sem executar
- `--text` — prompts em texto (CLIs não-Claude)
- `--skip-transition-guard` — bypass do completeness checker (uso emergencial)

```bash
MILESTONE=$(echo "$ARGUMENTS" | awk '{print $1}')
FROM_PHASE=$(echo "$ARGUMENTS" | grep -oE '\-\-from\s+[0-9]+\.?[0-9]*' | awk '{print $2}' || true)
DRY_RUN=$(echo "$ARGUMENTS" | grep -q '\-\-dry-run' && echo "true" || echo "")
TEXT_MODE=$(echo "$ARGUMENTS" | grep -q '\-\-text' && echo "true" || echo "")
SKIP_GUARD=$(echo "$ARGUMENTS" | grep -q '\-\-skip-transition-guard' && echo "true" || echo "")
```

**Validação:** se `MILESTONE` vazio:
> Uso: /gsd-autopilot <milestone-id> [--from N] [--dry-run] [--text]
> Exemplo: /gsd-autopilot v1.0

**Bootstrap check:**
```bash
INIT=$(node .claude/get-shit-done/bin/gsd-tools.cjs init milestone-op)
```
Se `roadmap_exists: false` → erro pedindo `/gsd-bootstrap`.

**Banner inicial em pt-BR:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTOPILOT v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Milestone: {milestone_version} — {milestone_name}
 Modo: v0.5.0 (gates 2,3,4,5,6,7 ativos + retro bloqueante)
 Tokens visuais: {visual_tokens_mode}
 Auto-retrospectiva: OBRIGATÓRIA por phase (não pode pular)
 Guard de transição: ATIVO (bloqueia avanço se phase anterior incompleta)
```

</step>

<step name="2-discover-phases">

## 2. Descobrir phases

```bash
ROADMAP=$(node .claude/get-shit-done/bin/gsd-tools.cjs roadmap analyze)
```

Filtrar phases incompletas do milestone alvo. Se `--from N`, pular phases anteriores.

**IMPORTANTE — verificação retroativa:**

Antes de listar phases para executar, verificar se **phases anteriores ao --from** têm artefatos completos. Se não tiverem, ALERTAR antes de avançar:

```bash
if [ -n "$FROM_PHASE" ]; then
  ALL_PRIOR=$(seq 1 $((FROM_PHASE - 1)))
  MISSING_RETROS=()
  for prior in $ALL_PRIOR; do
    if [ ! -f ".planning/retros/phase-${prior}.md" ]; then
      MISSING_RETROS+=("phase-${prior}")
    fi
  done

  if [ ${#MISSING_RETROS[@]} -gt 0 ]; then
    cat << WARN
⚠  ATENÇÃO: você está usando --from ${FROM_PHASE} mas as phases anteriores
   têm retrospectivas faltantes:

WARN
    for missing in "${MISSING_RETROS[@]}"; do
      echo "   ✗ .planning/retros/${missing}.md"
    done

    echo ""
    echo "Recomendação: rode antes de continuar:"
    echo "   /gsd-recover-retros --all"
    echo ""
    echo "Ou continue mesmo assim (perda de telemetria) com:"
    echo "   /gsd-autopilot ${MILESTONE} --from ${FROM_PHASE} --skip-transition-guard"
    exit 1
  fi
fi
```

**Tabela de phases:**

```
## Plano de execução para {milestone_version}

| #  | Phase Name              | has_ui | Status      |
|----|-------------------------|--------|-------------|
| 1  | Setup Infra             | false  | Completa    |
| 2  | Auth + User             | false  | Completa    |
| 3  | Admin UI                | true   | A iniciar   |
| 4  | API pedidos             | false  | A iniciar   |
```

</step>

<step name="3-confirm">

## 3. Confirmação única (obrigatória)

```
O autopilot executará o ciclo completo v0.5.0 para cada phase incompleta:
  discuss → ui (se has_ui) → research → plan → plan-checker → execute → verify → reconcile → AUTO-RETRO

Pausará apenas em:
  - Bloqueios de gate
  - Falhas de verificação
  - Phase incompleta detectada na transição (NOVO)
  - Fim do milestone

Retrospectivas serão GERADAS OBRIGATORIAMENTE (campos qualitativos vazios para preenchimento posterior).
```

Via AskUserQuestion (ou `--text`):
- Pergunta: "Prosseguir com autopilot para milestone {milestone_version}?"
- Opções: "Sim, iniciar" / "Não, abortar"

</step>

<step name="4-phase-loop">

## 4. Loop principal de phases

Para cada phase:

### 4.0 Pre-check transição (NOVO em v0.5.0)

**Antes de iniciar a phase, verificar que phase anterior está completa:**

```bash
if [ "$N" -gt 1 ]; then
  PRIOR=$((N - 1))
  CHECK_RESULT=$(Skill skill="gsd-phase-completeness-checker" args="${PRIOR} strict")

  if echo "$CHECK_RESULT" | grep -q "status: incomplete"; then
    handle_blocker "Phase ${PRIOR} está incompleta. Detalhes: $CHECK_RESULT"
  fi
fi
```

### 4.1 Banner da phase

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTOPILOT ▸ Phase {N}/{T}: {name} [{progress}%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.1.5 Env-smoke-check (DECISION-52 — v0.9.2)

**Pega problemas de ambiente ANTES de gastar tokens em discuss/research/plan/execute.**

Origem empírica (retros de campo):
- Rota Certa phase-03: `arq>=0.26 + redis>=7.4.0` conflito silencioso em `uv sync`
- Rota Certa phase-02: `pythonpath = ["src"]` ausente, pytest coletou 0 testes
- Rota Certa phase-04: `alembic/env.py` ignorando `TEST_DATABASE_URL` (issue desde 03-01)
- Alfie phase-31: Tailwind v4 PostCSS sem `.postcssrc.json`
- Rota Certa phases 2-4: TS errors pré-existentes acumulando como "out-of-scope"

```bash
bash bin/env-smoke-check.sh
SMOKE_EXIT=$?

case $SMOKE_EXIT in
  0)
    # Verde — segue
    ;;
  1)
    # Blockers — NÃO PODE seguir
    AskUserQuestion: "Env-smoke-check detectou blockers. Veja output acima. Opções: (1) Resolver agora e relançar autopilot (2) Pular smoke check (--skip-env-smoke) (3) Parar autopilot"
    ;;
  2)
    # Warnings — opera decide
    AskUserQuestion: "Env-smoke-check detectou warnings (não-bloqueantes). Continuar phase? (sim/não)"
    ;;
esac
```

**Variáveis disponíveis para customização:**
- `GSD_ENV_SMOKE_SKIP=python,db` — pula checks específicos
- `GSD_ENV_SMOKE_STRICT=1` — warnings viram blockers (modo CI)

**Por que esta step existe:**
- 43% dos retros analisados mencionam friction de setup que poderia ser pega antes
- Custo: ~5 segundos. Salva: ~30min de phase travada com erro de ambiente
- TD aging (acumulação de pre-existing errors entre phases) é detectada aqui
- Cross-platform: detecta SO e usa comandos certos

### 4.2 Skip se já completa

```bash
PHASE_STATE=$(node .claude/get-shit-done/bin/gsd-tools.cjs init phase-op ${PHASE_NUM})
```

Se phase tem todos artefatos canônicos + retro → skip.

### 4.2.5 Squad-research (DECISION-51 — v0.9.1)

**Antes de discuss-phase**, ler ROADMAP da phase atual para detectar squad recomendado:

```bash
SQUAD_PRE=$(node -e "
  const fs = require('fs');
  const roadmap = fs.readFileSync('.planning/ROADMAP.md', 'utf8');
  const phaseSection = roadmap.split(/^## Phase /m)[${PHASE_NUM}];
  const match = phaseSection?.match(/pre-phase:\s*(squad-research|none)/);
  console.log(match ? match[1] : 'none');
")

if [ "$SQUAD_PRE" = "squad-research" ]; then
  echo "🔀 Squad-research disparado (4 agents em paralelo)..."
  Skill(skill="gsd-squad-orchestrator", args="research --phase=${PHASE_NUM}")
  # Output em docs/squad-outputs/research-phase-${PHASE_NUM}-${date}.md
  # Será citado em CONTEXT.md no próximo step (discuss-phase lê o squad output)
fi
```

**Por que automatizar isto:**
- Operador esqueceria de chamar manualmente
- Skill `meta/orchestration-decision-tree` recomenda squad-research para phases com 3+ flags ou has_ai
- Decisão de "rodar squad ou não" foi pré-feita pelo ingestor — autopilot só obedece
- Custo: ~4x tokens. Compensa apenas em phases que justificam (ROADMAP define).

### 4.3 Discuss (se CONTEXT.md ausente)

```
Skill(skill="gsd-discuss-phase", args="${PHASE_NUM}")
```

### 4.4 UI Phase (gate 2 bloqueante se has_ui)

Se `has_ui: true`:

**Pre-check tokens.json:**
```bash
if [ ! -s docs/identidade-visual/tokens.json ]; then
  handle_blocker "Gate 2: docs/identidade-visual/tokens.json ausente ou vazio"
fi
```

```
Skill(skill="gsd-ui-phase", args="${PHASE_NUM}")
```

### 4.5 Research (gate 4 — Security Baseline se aplicável)

```
Skill(skill="gsd-research-phase", args="${PHASE_NUM}")
```

Se phase toca em endpoints/auth/PII, verificar Security Baseline em RESEARCH.md.

### 4.6 Plan

```
Skill(skill="gsd-plan-phase", args="${PHASE_NUM}")
```

### 4.7 Plan-checker (gate 3 — Skills Coverage)

```
Skill(skill="gsd-plan-checker", args="${PHASE_NUM}")
```

Se bloqueado por skills_coverage:
- AskUserQuestion: "Revisar plano" / "Prosseguir mesmo assim (bypass logado)" / "Parar autopilot"

### 4.8 Execute (gates 5, 6 em runtime)

**Lookahead de paralelismo (v0.9.5):** ler `parallel-hint` da phase no ROADMAP. Se `back-front` ou `module-split` E `parallelization.enabled: true` no config, a execução desta phase opera com `task_level` ligado para esta wave — o `gsd-execute-phase` delega ao `gsd-wave-dispatcher`, que valida a disjunção real de arquivos antes de paralelizar (skill `meta/parallel-orchestration`) e rebaixa para serial se inseguro.

```bash
PARALLEL_HINT=$(node -e "
  const fs = require('fs');
  const roadmap = fs.readFileSync('.planning/ROADMAP.md', 'utf8');
  const phaseSection = roadmap.split(/^## Phase /m)[${PHASE_NUM}];
  const match = phaseSection?.match(/parallel-hint:\s*(back-front|module-split|serial)/);
  console.log(match ? match[1] : 'serial');
")
echo "▶ parallel-hint da phase ${PHASE_NUM}: ${PARALLEL_HINT}"
```

```
Skill(skill="gsd-execute-phase", args="${PHASE_NUM} --no-transition --parallel-hint=${PARALLEL_HINT}")
```

### 4.9 Verify-work (gate 6)

```
Skill(skill="gsd-verify-work", args="${PHASE_NUM}")
```

### 4.9.5 Squad-review (DECISION-51 — v0.9.1)

**Depois de execute + verify**, disparar squad-review se ROADMAP recomenda:

```bash
SQUAD_POST=$(node -e "
  const fs = require('fs');
  const roadmap = fs.readFileSync('.planning/ROADMAP.md', 'utf8');
  const phaseSection = roadmap.split(/^## Phase /m)[${PHASE_NUM}];
  const match = phaseSection?.match(/post-execute:\s*(squad-review|none)/);
  console.log(match ? match[1] : 'none');
")

if [ "$SQUAD_POST" = "squad-review" ]; then
  echo "🔀 Squad-review disparado (4 agents em paralelo: code + security + integration + ui)..."
  Skill(skill="gsd-squad-orchestrator", args="review --phase=${PHASE_NUM}")
  # Output em docs/squad-outputs/review-phase-${PHASE_NUM}-${date}.md
  
  # Se squad-review reportar CRITICAL → bloqueia avanço da phase
  REVIEW_FILE="docs/squad-outputs/review-phase-${PHASE_NUM}-$(date +%Y-%m-%d).md"
  if [ -f "$REVIEW_FILE" ] && grep -q "🔴 CRITICAL" "$REVIEW_FILE"; then
    AskUserQuestion: "Squad-review detectou issues CRITICAL em $REVIEW_FILE. Resolver agora / Marcar como TD e avançar / Parar autopilot"
  fi
fi
```

Routing baseado no status: passed | human_needed | gaps_found.

### 4.10 Auto-retrospectiva (OBRIGATÓRIA — não pode ser pulada)

**Esta etapa é BLOQUEANTE.** Se falhar, phase não fecha.

```
Skill(skill="gsd-metrics", args="${PHASE_NUM}")
```

OU, se `gsd-metrics` não disponível, gerar inline:

```bash
mkdir -p .planning/retros

# Template canônico em pt-BR
cat > .planning/retros/phase-${PHASE_NUM}.md << RETRO_EOF
---
phase: ${PHASE_NUM}
phase_name: ${PHASE_NAME}
milestone: ${MILESTONE}
date: ${ISO_DATE}
auto_generated: true
pending_review: true
---

# Retrospectiva — Phase ${PHASE_NUM} ${PHASE_NAME}

## Dados objetivos (capturados automaticamente)
- Início: ${started_at}
- Fim: ${closed_at}
- Duração: ${duration_hours}h
- Plan revisions: ${plan_revisions}
- Verification retries: ${retries}
- Tasks: ${done_tasks}/${total_tasks}
- Gates bypassados: ${gates_bypassed}
- Tech debt adicionado: ${tech_debt_added}
- Skills citadas: ${skills_cited}
- Skills dispensadas: ${skills_dispensed}

## Auto-observações
${auto_observations}

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem?
[AUTO: preencher depois]

### 2. O que atrapalhou?
[AUTO: preencher depois]

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois]

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]
RETRO_EOF
```

**Validação pós-criação:**
```bash
if [ ! -f ".planning/retros/phase-${PHASE_NUM}.md" ]; then
  handle_blocker "FALHA CRÍTICA: retro não foi gerada para phase ${PHASE_NUM}. Não posso avançar."
fi
```

**Atualizar METRICS.md:**
```bash
cat >> .planning/METRICS.md << METRICS_EOF
- phase: ${PHASE_NUM}
  phase_name: ${PHASE_NAME}
  closed_at: ${ISO_DATE}
  duration_hours: ${duration_hours}
  retro_generated: true
  qualitative_filled: false
METRICS_EOF
```

### 4.11 Display

```
Phase ${PHASE_NUM} ✅ COMPLETA
  Retro: .planning/retros/phase-${PHASE_NUM}.md (qualitativos pendentes)
  Avançando para próxima phase...
```

</step>

<step name="5-milestone-close">

## 5. Fechamento do milestone

Após todas as phases:

### 5.1 Verificação final de completude

```bash
ALL_PHASES=$(ls -d .planning/phases/*/ | sed 's|.planning/phases/||;s|/$||' | grep -oE '^[0-9]+\.?[0-9]*' | sort -u)
INCOMPLETE=()
for phase in $ALL_PHASES; do
  RESULT=$(Skill skill="gsd-phase-completeness-checker" args="${phase} report")
  if echo "$RESULT" | grep -q "status: incomplete"; then
    INCOMPLETE+=("$phase")
  fi
done

if [ ${#INCOMPLETE[@]} -gt 0 ]; then
  echo "⚠  Milestone tem ${#INCOMPLETE[@]} phases incompletas"
  echo "Rode: /gsd-recover-retros --all  para reconstruir retros faltantes"
fi
```

### 5.2 Squad-audit pre-release (DECISION-51 — v0.9.1)

**Antes do milestone-summary**, disparar squad-audit se ROADMAP marca alguma phase como `is_pre_release: true`:

```bash
HAS_PRE_RELEASE=$(grep -q "is_pre_release: true" .planning/ROADMAP.md && echo "true" || echo "false")

if [ "$HAS_PRE_RELEASE" = "true" ]; then
  echo "🔀 Squad-audit disparado (4 auditors em paralelo: perf + a11y + i18n + obs)..."
  Skill(skill="gsd-squad-orchestrator", args="audit --milestone=${MILESTONE}")
  # Output em docs/squad-outputs/audit-${MILESTONE}-${date}.md
  
  # Se squad-audit reportar CRITICAL → bloqueia milestone close
  AUDIT_FILE="docs/squad-outputs/audit-${MILESTONE}-$(date +%Y-%m-%d).md"
  if [ -f "$AUDIT_FILE" ] && grep -q "🔴 CRITICAL" "$AUDIT_FILE"; then
    echo "⚠  Squad-audit detectou issues CRITICAL — milestone NÃO pode fechar."
    AskUserQuestion: "Mostrar audit / Resolver agora / Marcar como TD e fechar mesmo assim / Parar autopilot"
  fi
fi
```

**Por que automatizar isto:**
- Milestone close sem audit é equivalente a "shipping cego"
- 4 auditors (performance, accessibility, i18n, observability) pegam coisas que phase-by-phase review perde
- CRITICAL bloqueia release — vira hard gate

### 5.2.5 Release-auditor pre-deploy (DECISION-55 — v0.9.3)

**Se a phase é pre-release E há intenção de deploy**, disparar release-auditor:

```bash
if [ "$HAS_PRE_RELEASE" = "true" ]; then
  echo "🚀 Release-auditor disparado (checklist de release-safety)..."
  Skill(skill="gsd-release-auditor", args="--milestone=${MILESTONE}")
  # Output em docs/squad-outputs/release-audit-${MILESTONE}-${date}.md
  
  # Release-auditor pega o que os retros mostraram faltando:
  # secrets ausentes, plists com placeholder, app records não criados,
  # migrations não-aplicadas, health checks ausentes, deploy-safety invariantes violadas
  
  RELEASE_AUDIT="docs/squad-outputs/release-audit-${MILESTONE}-$(date +%Y-%m-%d).md"
  if [ -f "$RELEASE_AUDIT" ] && grep -q "🔴 BLOCKER" "$RELEASE_AUDIT"; then
    echo "⚠  Release-auditor detectou BLOCKERS — deploy NÃO está pronto."
    AskUserQuestion: "Mostrar release audit / Resolver blockers agora / Fechar milestone sem deploy (código pronto, deploy depois) / Parar autopilot"
  fi
fi
```

**Diferença vs squad-audit:**
- squad-audit (5.2): qualidade do **código** (perf, a11y, i18n, obs)
- release-auditor (5.2.5): prontidão de **deploy** (secrets, migrations, plists, health checks, deploy-safety invariantes)

São complementares. Código pode passar squad-audit e o deploy ainda falhar por secret faltando — release-auditor pega isso.

**Origem empírica:** Rota Certa phase-09 (plists com placeholder, secrets faltando, app records não criados) e Augur phase-11 (smoke tests, scans pendentes) mostraram que release readiness é categoria distinta de qualidade de código.

### 5.3 Milestone summary com cálculo de produtividade

```
Skill(skill="gsd-milestone-summary", args="${MILESTONE}")
```

### 5.4 Banner final em pt-BR

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTOPILOT ▸ MILESTONE {MILESTONE} CONCLUÍDO ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Phases concluídas: {N}
 Tempo total: {X}h trabalho efetivo
 Estimativa solo-dev (sem framework): {Y} semanas → {Y_HOURS}h
 Ganho de produtividade: {RATIO}x mais rápido
 Gates bypassados: {count}
 Tech debt adicionado: {count} item(s)
 Retrospectivas: {N} (todas geradas, qualitativos pendentes)

 Próximos passos:
   1. Preencher qualitativos das retrospectivas:
        ls .planning/retros/
   2. Revisar dívida técnica:
        cat .planning/TECH-DEBT.md
   3. Commit + tag:
        git add .planning/ docs/ apps/
        git commit -m "feat({MILESTONE}): {summary}"
        git tag -a {MILESTONE}-complete
   4. Exportar telemetria:
        bash bin/export-telemetry.sh
```

### 5.5 Continuar para próximo milestone?

Single-hop recursion. Pergunta: "Continuar autopilot para {NEXT_MILESTONE}?"

</step>

<step name="6-handle-blocker">

## 6. Tratamento de bloqueio

Em caso de falha:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTOPILOT ▸ BLOQUEIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Phase {N} ({nome}): {descrição}

 Opções:
   1. Tentar novamente o passo
   2. Pular esta phase (logged, não recomendado)
   3. Parar autopilot

 Para retomar depois:
   /gsd-autopilot {milestone} --from {next_phase}
```

</step>

</process>

<success_criteria>
- [ ] Output 100% em pt-BR (banners, prompts, mensagens)
- [ ] Auto-retro é OBRIGATÓRIA — phase não fecha sem ela
- [ ] Antes de avançar, chama gsd-phase-completeness-checker em modo strict
- [ ] Detecta retros perdidas em phases anteriores ao --from e sugere /gsd-recover-retros
- [ ] Cálculo de produtividade no summary final
- [ ] Idempotente: rodar 2x não corrompe
- [ ] Suporta --skip-transition-guard como bypass de emergência
</success_criteria>
