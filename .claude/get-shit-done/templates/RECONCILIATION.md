# RECONCILIATION — Phase {N} {nome}

> Gerado por `/gsd-reconcile-state {N}` em {date}.
> Propósito: verificar que os artefatos de planejamento refletem o código real.

> **⚠️ Os exemplos abaixo ({gateway-pagamento}, `accept_proposal`, JWT admin em localStorage, etc.) são ilustrativos — vieram de um projeto real usado como referência. Adapte ao seu domínio. O VALOR do template está na ESTRUTURA: como listar confirmações, como descrever divergências, como propor patches.**

---

## Status geral

**{✅ CLEAN | ⚠️ GAPS | ❌ DIVERGENT}**

## Sumário

- Afirmações verificadas: {total}
- Confirmadas no código: {count} ({percent}%)
- Divergências: {count}
- Arquivos-fantasma: {count}
- Features fantasma: {count}
- Dívidas ressuscitadas: {count}

---

## Afirmações verificadas

### ✅ Confirmadas

Formato: `[x] {fonte} → {afirmação} → {verificação positiva}`

- [x] `PLAN 05-03` T-03: endpoint `POST /proposals/{id}/accept` implementado
  - File: `backend/app/api/proposals.py:142`
  - Signature OK: `async def accept_proposal(id: UUID, body: AcceptProposalBody, user: CurrentUser)`
  - Skill aplicada confirmada: rate limit 20/min via `@limiter.limit("20/minute")`

- [x] `PLAN 05-04` T-04: WebSocket URL inclui prefixo `/api/v1/`
  - File: `apps/mobile/src/core/services/websocket.service.ts:28`
  - Pattern: `const url = \`${env.wsBase}/api/v1/ws/conversations/${id}\`;`

(listar todas)

### ⚠️ Divergências

Formato: `[!] {fonte} → {afirmação} → {realidade} → {fix proposto}`

- [!] `STATE.md` L-42 declara "{gateway-pagamento}: 4/26 features implementadas"
  - **Código real:** `backend/app/services/payment/{gateway-pagamento}_service.py` tem **26 métodos** (`grep -c "async def \|def " = 26`)
  - **Fix proposto:** atualizar STATE.md para "26/26 implementada"
  - **Patch disponível:** ver seção "Patches propostos" abaixo

- [!] `TECH-DEBT.md` TD-012 "JWT admin em localStorage" marcada "RESOLVIDO (Phase 07)"
  - **Código real:** `admin/src/app/auth/auth.service.ts:45` ainda usa `localStorage.setItem('token', token)`
  - **Fix proposto:** reabrir TD-012, mover "Plan a resolver" para próxima fase
  - **Adicionar a SUGGESTIONS:** migrar localStorage → httpOnly cookie (ref skill `owasp-security`)

### ❌ Arquivos-fantasma

- `PLAN 03-02` T-01 declara criação de `backend/app/services/chat/websocket_manager.py`
  - **Real:** arquivo não existe
  - **Investigação:** grep por `WebsocketManager` encontra classe em `backend/app/core/websocket.py:10`
  - **Conclusão:** absorvido em core. Atualizar PLAN.md para refletir localização final.

### 🎯 Features fantasma (código sem artefato correspondente)

Código com funcionalidade não documentada em nenhum PLAN.md:

- `backend/app/services/chat/archive.py` — função `archive_old_conversations()` (não em nenhum plano)
  - **Conclusão:** código emergente. Adicionar a `SUGGESTIONS.md` para discussão:
    - Manter? → criar task retroativa para documentar
    - Remover? → task de deleção com justificativa

---

## Patches propostos

Aplicar com `/gsd-reconcile-state {N} --apply` (ou revisar manualmente).

### Patch 1 — `.planning/STATE.md`

```diff
  ## Current Position
  
- - **Feature {gateway-pagamento}:** 4/26 implementada (blocker para pagamento)
+ - **Feature {gateway-pagamento}:** 26/26 implementada (verificado em {date})
```

### Patch 2 — `.planning/TECH-DEBT.md`

```diff
- | TD-012 | JWT admin em localStorage | XSS risk | dev | Phase 07 | RESOLVIDO (Phase 07) |
+ | TD-012 | JWT admin em localStorage | XSS risk | dev | Phase {N+1} | ABERTO — localStorage ainda em auth.service.ts:45. Ref: RECONCILIATION Phase {N} |
```

### Patch 3 — `.planning/SUGGESTIONS.md` (adições)

```markdown
### {date} — Migrar localStorage → httpOnly cookie no admin

- **Origem:** `/gsd-reconcile-state {N}`
- **Severidade:** must (XSS risk conhecido)
- **Categoria:** tech-debt
- **Contexto:** TD-012 marcada como resolvida em Phase 07, grep mostra que ainda existe em `admin/src/app/auth/auth.service.ts:45`. Skill owasp-security proíbe localStorage para JWT.
- **Ação sugerida:** fase dedicada de migração com backend endpoint `/auth/session-cookie` + frontend mudança em auth.service.ts. Estimativa: 1 dia.
- **Status:** 🟡 aberto

### {date} — Função archive_old_conversations() não documentada

- **Origem:** `/gsd-reconcile-state {N}`
- **Severidade:** should
- **Categoria:** process
- **Contexto:** Função existe em `backend/app/services/chat/archive.py`, nenhum PLAN.md menciona. Origem desconhecida.
- **Ação sugerida:** decidir com humano: documentar retroativamente em PLAN.md de Phase N, ou remover.
- **Status:** 🟡 aberto
```

### Patch 4 — `.planning/phases/{padded}-{slug}/PLAN.md`

```diff
  ### T-01 — Criar websocket_manager.py
  - **Files:**
- - `backend/app/services/chat/websocket_manager.py`
+ - `backend/app/core/websocket.py` (renomeado durante execução, classe WebsocketManager)
```

---

## Ação requerida

Escolha uma:

1. **Aplicar todos os patches** (recomendado se revisão dos patches acima está OK):
   ```
   /gsd-reconcile-state {N} --apply
   ```

2. **Revisar e aplicar seletivamente:**
   ```
   /gsd-reconcile-state {N} --interactive
   ```

3. **Rejeitar reconciliação** (manter artefatos como estão — documentar razão em DECISIONS.md):
   ```
   /gsd-reconcile-state {N} --reject --reason "<texto>"
   ```

---

## Resultado

Preenchido após aplicação:

- [ ] Patches aplicados em: {date}
- [ ] Entry em DECISIONS.md: {link}
- [ ] Commit: {hash}
- [ ] Gate 6 (Reconciliation) satisfeito → pode fechar Phase {N}
