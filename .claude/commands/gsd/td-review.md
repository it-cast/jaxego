---
name: gsd:td-review
description: |
  Revisa TECH-DEBT.md, detecta TDs aging (abertas há múltiplas phases),
  e oferece 3 ações: promover urgency_class / resolver agora / aceitar como ADR.
  
  Origem: retros de campo (Rota Certa phases 2-4) mostraram que bugs pré-existentes
  ficam mencionados como "out-of-scope" em phases consecutivas sem resolução.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# /gsd:td-review

Análise de envelhecimento de tech debt + ação concreta.

## O que faz

1. **Lê** `.planning/TECH-DEBT.md` + retros em `.planning/retros/` + `.planning/METRICS.md`
2. **Detecta** TDs aging (abertas há mais phases do que o threshold da `urgency_class`):
   - `post_launch_quarter`: aging após 4 phases
   - `post_launch_30d`: aging após 3 phases
   - `pre_launch_high`: aging após 2 phases
   - `pre_launch_blocker`: aging após 1 phase (sempre é crítico)
3. **Para cada TD aging, propõe 3 ações:**
   - **Promover** urgency_class para nível superior + atualizar TECH-DEBT.md
   - **Resolver agora** — abre research/plan/execute para resolver dentro da phase atual
   - **Aceitar como ADR** — virar decisão consciente em `docs/adrs/`, sair de TECH-DEBT.md
4. **Atualiza** TECH-DEBT.md com decisões tomadas
5. **Atualiza** `.planning/METRICS.md` com log da decisão

## Por que existe

Histórico de campo (Rota Certa phases 2-4):
- Bug TypeScript TS2352/TS2322 introduzido em phase 2 (commit 8154093)
- Mencionado em phase 3 como "pre-existing out-of-scope"
- Mencionado em phase 4 como "pre-existing out-of-scope"
- Nunca foi resolvido

Esse padrão é exatamente o que TD aging policy quer prevenir. Sem este command, TDs acumulam silenciosamente até virar ruído permanente.

## Uso

```
/gsd:td-review              # análise + decisão interativa por TD aging
/gsd:td-review --report     # só relatório, sem ação
/gsd:td-review --auto-promote   # promove automaticamente urgency_class (sem perguntar)
```

## Invocação

Você é o operador. Para esta tarefa:

1. **Leia** `.planning/TECH-DEBT.md` parseando a tabela de TDs
2. **Para cada TD com status=aberto ou em-progresso:**
   - Procure menções dela em `.planning/retros/phase-*.md` (regex `TD-NNN` ou descrição)
   - Conte em quantas phases distintas ela apareceu
   - Compare com threshold da urgency_class
3. **Mostre o relatório**:
   ```
   📋 TD Review — análise de envelhecimento
   
   3 TDs aging:
   
   1. TD-005: erros TS pré-existentes em pricing-table-form.component.ts
      Urgency: post_launch_quarter (threshold: 4 phases)
      Aberta em: phase 2, 3, 4 (3 phases — DENTRO do threshold)
      → status: monitorando
   
   2. TD-012: alembic/env.py ignora TEST_DATABASE_URL
      Urgency: post_launch_30d (threshold: 3 phases)
      Aberta em: phase 03-01, 04, 05 (3 phases — NO threshold)
      → AÇÃO: promover para pre_launch_high OU resolver
   
   3. TD-019: magic library Windows access violation
      Urgency: post_launch_quarter
      Aberta há: 1 phase
      → ok
   ```

4. **Para TDs no threshold**, pergunte ao operador (AskUserQuestion):
   - Promover urgency_class? (acelera prazo)
   - Resolver dentro desta phase? (abre execute-phase-fix)
   - Aceitar como ADR? (vira decisão consciente, sai de TECH-DEBT)
   - Skip por enquanto? (logado mas não age)

5. **Aplique** a decisão escolhida:
   - Promoção: edite a linha de TECH-DEBT.md mudando `urgency_class`
   - Resolver: crie phase de fix em ROADMAP.md (ou execute inline se trivial)
   - ADR: mova entry de TECH-DEBT para `docs/adrs/ADR-XXX-{slug}.md` + atualize status para `aceito`
   - Skip: registre em METRICS.md com timestamp

6. **Resumo final**: quantas TDs revisadas, quantas promovidas, quantas resolvidas, quantas vira ADR.

## Não-objetivos

- **Não resolve TDs automaticamente em código.** Só identifica e propõe ação.
- **Não cria phases novas sem perguntar.** Operador decide.
- **Não toca em TDs com status `resolvido` ou `aceito`.** Só `aberto` e `em-progresso`.
