<purpose>
Executor de fase v3 — aplica Gate 5 (integration checkpoint) automaticamente ao fim do processamento de waves.
Diferença vs. v2: integration-checker agora é BLOQUEANTE (não mais opcional) quando a fase declara integration_check.
</purpose>

<required_reading>
@$CLAUDE_PROJECT_DIR/CLAUDE.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/gates-v3.md
@$CLAUDE_PROJECT_DIR/.planning/ROADMAP.md
@$CLAUDE_PROJECT_DIR/.planning/config.json
</required_reading>

<trigger>
/gsd-execute-phase <N>              # executa todos os plans da fase em ordem
/gsd-execute-phase <N> <plan-id>    # executa apenas plan específico
</trigger>

<process>

## 1. Pré-condições

```bash
# Gate 1
[ -f .planning/PROJECT.md ] || die "Bootstrap não executado"

# Plan deve ter passado plan-checker
PLAN_PATH=".planning/phases/$(padded $PHASE)-*/PLAN.md"
grep -q "Plan-checker report" "$PLAN_PATH" || die "PLAN.md não passou plan-checker"
grep -q "Status: PASS" "$PLAN_PATH" || die "PLAN.md com status BLOCK ou FLAG não resolvido"
```

## 2. Parsear waves e tasks do PLAN.md

Extrair:
- Lista de waves (grupos paralelizáveis)
- Tasks de cada wave
- Files que cada task toca
- Skills aplicadas (pra passar ao executor como contexto)
- Success criteria por task

## 3. Executar waves em ordem

**Modo de execução da wave (v0.9.5):**

```bash
TASK_LEVEL=$(node -e "console.log(require('./.planning/config.json').parallelization?.task_level ?? false)")
```

- **`task_level: true`** → invocar `gsd-wave-dispatcher` via Task tool com a wave inteira. Ele particiona tasks por fronteira de arquivos (skill `meta/parallel-orchestration`), dispara até `max_concurrent_agents` instâncias de `gsd-executor` em paralelo nos grupos disjuntos, serializa o resto (migrations/lockfiles/registros centrais SEMPRE seriais), trata conflitos de lease e fecha a wave com test+lint integrado. Relatório da partição vai para EXECUTION-LOG.md.
- **`task_level: false`** (default) → modo serial clássico: invocar `gsd-executor` para cada task, em ordem, com:
  - Descrição da task
  - Files a tocar
  - Skills aplicadas (executor deve aplicar regras, não só citar)
  - Success criteria
- Em ambos os modos: após wave terminar, rodar `make test` + `make lint` — falha = parar

Commit atômico por task:
```
git add <files>
git commit -m "feat(phase-{N}/plan-{NN-NN}): T-{id} {título curto}

{descrição da task}

Skills aplicadas: {lista}
Success: {critério}
"
```

## 4. Gate 7 — Tests + Lint por plano

Ao fim de cada plano (grupo de tasks relacionadas):

```bash
make test || die "Tests falhando — plano não fecha"
make lint || die "Lint falhando — plano não fecha"
```

## 5. Gate 5 — Integration Checkpoint (CRÍTICO)

> **⚠️ Exemplos de gap abaixo (`POST /api/v1/proposals/{id}/accept`, `service_request_id`, etc.) são ilustrativos. A máquina de estados do checker funciona com qualquer endpoint.**

**Se a fase tem `integration_check` declarado no ROADMAP:**

```bash
INTEGRATION_CHECK=$(extract_integration_check_from_roadmap "$PHASE")

if [ -n "$INTEGRATION_CHECK" ]; then
  echo "▶ Gate 5 ativo: executando gsd-integration-checker..."

  # Invocar checker
  CHECKER_OUTPUT=$(invoke_agent gsd-integration-checker \
    --phase "$PHASE" \
    --contracts "$INTEGRATION_CHECK")

  # Parsear resultado
  GAPS=$(echo "$CHECKER_OUTPUT" | jq '.gaps')

  if [ "$GAPS" != "[]" ] && [ -n "$GAPS" ]; then
    cat <<EOM
❌ Gate 5 (Integration Check) falhou — gaps encontrados:

$(echo "$CHECKER_OUTPUT" | jq -r '.gaps[] | "  INTEG-\(.id): \(.description)\n    consumer: \(.consumer)\n    expected: \(.expected)\n    found: \(.found)\n"')

A fase $PHASE NÃO pode ser marcada COMPLETE com gaps de integração.

Ações:
  1. Corrigir consumer ou provider conforme indicado
  2. Adicionar tasks de hotfix ao PLAN.md (T-fix-INTEG-*)
  3. Re-rodar /gsd-execute-phase $PHASE --hotfix

Este gate previne bugs que anteriormente chegavam ao audit semanas depois.
EOM
    exit 1
  else
    echo "✓ Gate 5 passou: todos os $(count_contracts "$INTEGRATION_CHECK") contratos verificados"
  fi
fi
```

### Como o integration-checker verifica cada contrato

Para cada linha em `integration_check:`:

```yaml
- endpoint: POST /api/v1/proposals/{id}/accept
  consumer: apps/mobile/src/app/chat/chat.page.ts
  verify:
    body_has: [payment_method, notes]
    response_has: [service_request_id, status]
```

Checker faz:

1. **Encontra o consumer no código:**
   ```bash
   grep -n "accept.*proposal\|acceptProposal" apps/mobile/src/app/chat/chat.page.ts
   # Ex: L.156: await this.api.post(`/proposals/${id}/accept`, { ... });
   ```

2. **Extrai o body sendo enviado:**
   ```bash
   # Analisa o objeto passado no post
   # Lista keys: vê se contém 'payment_method', 'notes'
   ```

3. **Encontra o provider no backend:**
   ```bash
   grep -rn "@router.post.*proposals.*accept\|/proposals/.*/accept" backend/app/api/
   ```

4. **Extrai o schema de Request (Pydantic):**
   ```python
   # Parse ast.parse() em backend/app/api/proposals.py
   # Encontra classe AcceptProposalBody(BaseModel) e lista fields
   ```

5. **Compara:**
   - Consumer envia: `{id}` ou `{}` (vazio)
   - Provider exige: `{payment_method: str, notes: str | None}`
   - Match? → OK
   - Miss? → gap reportado

### Tipos de gap detectáveis

- **G1 — Body missing fields:** consumer envia menos do que provider exige
- **G2 — Body extra fields:** consumer envia campos que provider não conhece (warning, não block em regra)
- **G3 — URL mismatch:** consumer chama path diferente (prefixo /api/v1/ ausente, typo)
- **G4 — Method mismatch:** consumer POST vs provider PUT
- **G5 — Auth mismatch:** consumer sem header `Authorization`, provider exige
- **G6 — WebSocket URL mismatch:** frontend ws:// sem prefixo /api/v1/, nginx proxy não configurado
- **G7 — Response field missing:** consumer lê `data.id` mas provider retorna `{service_request_id}` — renomeou
- **G8 — Status code mismatch:** consumer espera 201, provider retorna 200

### Gap resolução

Cada gap gera task de hotfix automática no PLAN.md:

```markdown
### T-fix-INTEG-01 — Corrigir body de accept_proposal no mobile
- **Files:** apps/mobile/src/app/chat/chat.page.ts:156
- **Fix:** adicionar body com `{payment_method, notes}` conforme schema backend
- **Skills aplicadas:** ionic-patterns, api-design-contracts
- **Success:** integration-checker passa
```

## 6. Atualizar artefatos ao fim da execução

```bash
# STATE.md — marcar tasks completed, apontar próximo plan ou fim de fase
# EXECUTION-LOG.md — append entry com resumo da execução
# DECISIONS.md — append decisões não-óbvias tomadas durante execução
# SUGGESTIONS.md (fase) — append sugestões descobertas
# TECH-DEBT.md — append dívidas aceitas conscientemente
```

## 7. Se fase ainda não fechou (plans restantes)

Continuar execução dos próximos plans automaticamente se `config.json: auto_advance: true`. Caso contrário, parar e aguardar humano.

## 8. Se fase fechou (último plan da fase)

**NÃO marcar fase COMPLETE ainda.** Executor apenas reporta que todos os plans passaram. Gate 6 (Reconciliation) e verify-phase ainda precisam rodar.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► EXECUTE-PHASE — Phase {N} — plans concluídos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plans executados: {N}
Tasks: {total} em {W} waves
Commits: {N} (atômicos)

Gates verificados:
  ✓ Gate 7 (Tests + Lint) por plano
  ✓ Gate 5 (Integration Check) — {M} contratos verificados, zero gaps

A fase ainda NÃO está COMPLETE. Próximos passos obrigatórios:
  /gsd-secure-phase {N}       # revisar threat model implementado
  /gsd-reconcile-state {N}    # Gate 6: prometido vs. código real
  /gsd-verify-phase {N}       # success criteria do ROADMAP
```

</process>

<failure_modes>
- **Test falha no meio de um plan** — para imediatamente, não continua próximo plano. Commit de WIP com prefixo `wip(phase-N)` permitido se humano aprovar.
- **Integration checker falsa-positivo** (ex: grep pegou comentário) — humano pode documentar o falsa-positivo em DECISIONS.md e re-rodar com `--skip-integ-verify INTEG-01 --reason "falso positivo — código real em L.200"`
- **Skills não aplicadas apesar de citadas** (ex: "owasp-security citada, rate limit ausente") — integration-checker v4 detectará isso; v3 não detecta, fica para secure-phase.
</failure_modes>
