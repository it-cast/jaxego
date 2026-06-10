<purpose>

> **⚠️ Os exemplos concretos neste workflow ({gateway-pagamento} service, `accept_proposal`, JWT em localStorage, etc.) vêm de um projeto real usado como referência durante o desenho do framework. O PADRÃO de verificação é universal; adapte os comandos grep/find ao seu domínio e estrutura de código.**

Reconciliar artefatos de planejamento (`STATE.md`, `SUMMARY.md`, `TECH-DEBT.md`) contra o código real.

Resolve um problema observado: artefatos de planejamento refletem o que o agente planejou entregar,
não o que foi efetivamente entregue. Ex: feature marcada como "4/26 implementada" que, ao inspecionar
o código, está 100% completa — e ninguém percebeu por semanas.

Este workflow lê cada afirmação de entrega/blocker/dívida e VERIFICA no código real.
Gera `RECONCILIATION.md` para a fase consultada e atualiza artefatos globais.
</purpose>

<required_reading>
@$CLAUDE_PROJECT_DIR/CLAUDE.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/gates-v3.md
</required_reading>

<when_to_run>
- **Obrigatório** antes de fechar qualquer fase (gate de reconciliação — Regra 8 do CLAUDE.md)
- Recomendado após reiniciar trabalho em projeto parado há > 1 semana
- Sob demanda: `/gsd-reconcile-state <N>` para fase específica ou `/gsd-reconcile-state --all`
</when_to_run>

<process>

## 1. Parsear argumentos

```
/gsd-reconcile-state <N>      — reconcilia uma fase específica
/gsd-reconcile-state --all    — reconcilia todas as fases concluídas ou em andamento
/gsd-reconcile-state --global — reconcilia apenas STATE.md, TECH-DEBT.md, SUGGESTIONS.md (sem fase)
```

Se argumento ausente, detectar fase atual em `.planning/STATE.md`.

## 2. Coletar afirmações a reconciliar

Para cada fase em escopo, extrair do `PLAN.md` e `SUMMARY.md`:

### 2.1. Deliveráveis declarados

Cada task do PLAN.md marcada como `completed` deve ter:
- **Arquivo(s) criado(s) ou modificado(s)** — extrair do campo `files` da task
- **Função(ões) / endpoint(s) / componente(s)** — extrair do campo `artifacts`
- **Success criteria** — extrair do campo `success_criteria`

### 2.2. Blockers ativos no STATE.md

Cada linha em `STATE.md` sob "Blockers ativos" menciona:
- Um arquivo (ex: `admin/src/app/auth/auth.service.ts`)
- Um problema descrito (ex: "JWT em localStorage em vez de httpOnly cookie")

### 2.3. Dívidas em TECH-DEBT.md

Cada row tem `Descrição` e `Plan a resolver`. Verificar se dívidas marcadas como "resolvidas" realmente foram.

### 2.4. Features/progresso em PROJECT.md ou ROADMAP

Frases como "Feature X: 4/26 implementada" precisam de verificação.

## 3. Verificar cada afirmação no código

Para cada item coletado, rodar verificação automática:

### 3.1. Arquivo existe

```bash
if [ -f "$FILE" ]; then
  # arquivo existe → continuar verificação de conteúdo
else
  # MARCAR COMO DIVERGÊNCIA: arquivo esperado não existe
fi
```

### 3.2. Símbolo existe no arquivo

Para afirmações do tipo "função `acceptProposal` implementada":

```bash
# Python
grep -n "def acceptProposal\|async def acceptProposal" "$FILE"

# TypeScript/JavaScript
grep -n "function acceptProposal\|acceptProposal(" "$FILE"
grep -n "acceptProposal:" "$FILE"

# Endpoint FastAPI
grep -n "@router.*\(post\|get\|put\|delete\).*accept-proposal" "$FILE"
```

### 3.3. Anti-patterns explicitamente proibidos

Para cada blocker/dívida descrita, rodar grep por padrão problemático:

```bash
# Exemplo: "JWT em localStorage"
grep -rn "localStorage.*token\|localStorage.setItem.*jwt" admin/src/ apps/admin/src/ 2>/dev/null

# Exemplo: "rate limit ausente no endpoint de login"
grep -n "def login\|async def login" backend/app/api/auth.py 2>/dev/null
grep -n "@limiter\|rate_limit\|slowapi" backend/app/api/auth.py 2>/dev/null

# Exemplo: "client_max_body_size não configurado no Nginx"
grep -rn "client_max_body_size" infra/nginx/ 2>/dev/null

# Exemplo: "DH 2048-bit no SSL"
ls infra/nginx/ssl/dhparam*.pem 2>/dev/null
[ -f infra/nginx/ssl/dhparam.pem ] && openssl dhparam -in infra/nginx/ssl/dhparam.pem -text 2>/dev/null | head -1
```

### 3.4. Counts progressivos (ex: "4/26 features")

Para afirmações do tipo "X/Y features implementadas", contar programaticamente:

```bash
# Exemplo: features do {gateway-pagamento} — cada feature é uma função no service
FEATURES_IMPLEMENTED=$(grep -c "def .*(" backend/app/services/payment/{gateway-pagamento}_service.py)
FEATURES_EXPECTED=26  # do PLAN.md ou do brief

if [ "$FEATURES_IMPLEMENTED" -ne "$FEATURES_EXPECTED" ]; then
  # MARCAR divergência: artefato diz X, código tem Y
fi
```

**Padrão para contagens:**
- Declaração no PLAN: "{gateway-pagamento} service terá 26 métodos cobrindo escrow full lifecycle"
- Verificação: `grep -c "async def \|def " file.py` (ou análise AST com `ast.parse` em Python)

## 4. Produzir `RECONCILIATION.md`

Formato de saída por fase verificada:

```markdown
# Reconciliation — Phase {N} {nome}

**Data:** {date}
**Verificado por:** /gsd-reconcile-state
**Status geral:** {✅ CLEAN | ⚠️ GAPS | ❌ DIVERGENT}

## Sumário

- Afirmações verificadas: {total}
- Confirmadas no código: {count} ({percent}%)
- Divergências: {count}
- Arquivos-fantasma (declarados mas ausentes): {count}
- Features fantasma (declaradas como pending que já estão prontas): {count}
- Dívidas ressuscitadas (marcadas resolvidas mas ainda no código): {count}

## Afirmação por afirmação

### ✅ Confirmadas

- [x] `PLAN 05-03`: endpoint `POST /proposals/{id}/accept` implementado
  - File: `backend/app/api/proposals.py:142`
  - Signature OK: `async def accept_proposal(id: UUID, body: AcceptProposalBody, ...)`

- [x] `PLAN 05-04`: WebSocket URL inclui prefixo `/api/v1/`
  - File: `apps/mobile/src/core/services/websocket.service.ts:28`
  - Pattern confirmado: `const url = \`\${env.wsBase}/api/v1/ws/conversations/\${id}\`;`

### ⚠️ Divergências encontradas

- [!] `STATE.md` declara "{gateway-pagamento}: 4/26 features implementadas"
  - **Código real:** `backend/app/services/payment/{gateway-pagamento}_service.py` tem **26 métodos**
  - **Conclusão:** afirmação desatualizada. Fix sugerido abaixo.

- [!] `TECH-DEBT.md` TD-012 "JWT admin em localStorage" marcada como "resolvida em Phase 07"
  - **Código real:** `admin/src/app/auth/auth.service.ts:45` ainda usa `localStorage.setItem('token', ...)`
  - **Conclusão:** dívida NÃO resolvida. Fix sugerido abaixo.

### ❌ Arquivos-fantasma

- `PLAN 03-02` declara criação de `backend/app/services/chat/websocket_manager.py`
  - **Código real:** arquivo não existe
  - **Verificar:** foi renomeado? Foi absorvido em outro arquivo? Ou task está aberta?

## Atualizações propostas

Gerar patches prontos para aplicar após revisão humana:

### Patch 1 — `STATE.md`
```diff
- Feature {gateway-pagamento}: 4/26 implementada (blocker para pagamento)
+ Feature {gateway-pagamento}: 26/26 implementada (ver backend/app/services/payment/{gateway-pagamento}_service.py)
```

### Patch 2 — `TECH-DEBT.md`
```diff
- | TD-012 | JWT admin em localStorage | XSS risk | dev | Phase 07 | RESOLVIDO (Phase 07) |
+ | TD-012 | JWT admin em localStorage | XSS risk | dev | Phase N+1 | ABERTO — localStorage ainda em auth.service.ts:45 |
```

### Patch 3 — `SUGGESTIONS.md` (adições)
```markdown
- [RECONCILE {date}] Implementar migração de localStorage → httpOnly cookie no admin
  - Referência: `admin/src/app/auth/auth.service.ts:45`
  - Skill: `owasp-security`
  - Estimativa: 1 dia
```

## Ação requerida do humano

Opção 1: Aplicar todos os patches propostos (`/gsd-reconcile-state --apply`)
Opção 2: Revisar um a um (editor interativo)
Opção 3: Rejeitar reconciliação e manter artefatos como estão (documentar por quê em DECISIONS.md)
```

## 5. Aplicar patches (se humano aprovar)

```bash
if [ "$APPLY" = "true" ]; then
  # Aplicar cada patch nos arquivos correspondentes
  # Atualizar STATE.md com timestamp da reconciliação
  # Adicionar entrada em DECISIONS.md:
  cat >> .planning/DECISIONS.md <<EOF

## ${DATE} — Reconciliation aplicada (Phase ${N})

- **Tipo:** Reconciliação automática
- **Divergências resolvidas:** ${COUNT}
- **Origem:** \`/gsd-reconcile-state ${N}\`
- **Arquivo detalhado:** \`.planning/phases/${PADDED}-${SLUG}/RECONCILIATION.md\`

Mudanças:
$(cat .planning/phases/${PADDED}-${SLUG}/RECONCILIATION.md | grep -E '^- \[!\]' | sed 's/^- /- Ajuste: /')

EOF

  # Commit atômico
  git add .planning/
  git commit -m "chore(reconcile-${N}): update artifacts to match real code

$(RECONCILIATION summary)
"
fi
```

## 6. Relatório final

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► RECONCILIATION — Phase {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: {✅ | ⚠️ | ❌}

{N} afirmações verificadas:
  ✓ {count} confirmadas no código
  ! {count} divergências
  ✗ {count} arquivos-fantasma

Relatório completo: .planning/phases/{padded}-{slug}/RECONCILIATION.md

{se --apply foi usado:}
Patches aplicados:
  ✓ STATE.md atualizado
  ✓ TECH-DEBT.md atualizado
  ✓ SUGGESTIONS.md com {N} novas entradas
  ✓ DECISIONS.md com log de reconciliação
  ✓ Commit: chore(reconcile-{N}): ...

{se sem --apply:}
Próximo passo: revisar RECONCILIATION.md e aplicar com:
  /gsd-reconcile-state {N} --apply
```

</process>

<heuristics>

## Como detectar tipos comuns de divergência

### Tipo A — Feature declarada incompleta, na verdade completa

Sintoma: `STATE.md` ou `SUMMARY.md` diz "X/Y", mas código tem Y.
Causa: atualização esquecida após merge rápido.
Detecção: contagem direta (grep -c, ou AST).

### Tipo B — Dívida técnica marcada resolvida, ainda presente

Sintoma: `TECH-DEBT.md` tem "RESOLVIDO (Phase N)", mas grep ainda encontra o padrão.
Causa: refactor parcial, commit descritivo mentiu.
Detecção: rodar grep pelos padrões listados na coluna "Descrição".

### Tipo C — Arquivo-fantasma

Sintoma: PLAN.md diz "criado arquivo `foo.py`", arquivo não existe.
Causa: renomeio sem atualizar plan, ou task abandonada com marcação errada.
Detecção: `[ -f "$FILE" ]`.

### Tipo D — Endpoint declarado, não implementado

Sintoma: PLAN.md diz endpoint `POST /x/y/z` pronto, router não tem.
Causa: task fechada prematuramente.
Detecção: `grep -rn "@router.*['\"].*${ENDPOINT}" backend/`.

### Tipo E — Feature fantasma (existe mas não documentada)

Sintoma: código tem feature, nenhum artefato menciona.
Causa: commit fora do fluxo GSD, ou feature emergente não planejada.
Detecção: diff entre símbolos reais no código e símbolos listados nos PLAN.md recentes.

Este tipo NÃO é resolvido automaticamente — gera SUGGESTIONS.md com "nova feature observada, considerar documentar ou remover".

</heuristics>

<failure_modes>
- **Sem SUMMARY.md por fase** → workflow usa só PLAN.md como fonte. Acurácia cai.
- **Fase com muitos arquivos** → verificação pode ser lenta. Aceitável. Não otimizar cedo.
- **Grep false positives** (padrão aparece em comentário/teste/docstring) → documentar: ao aplicar patch, humano confirma um a um. Sem `--apply` automático em divergências ambíguas.
- **Git uncommitted changes** → avisar antes de aplicar patches. Não misturar working tree sujo com mudança automática.
</failure_modes>
