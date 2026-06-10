# Migração v0.9.5 → v0.9.6

> Versão de **enforcement e correção**. Nenhuma capacidade nova, nenhuma mudança
> de workflow para o operador — o que muda é que mecanismos que dependiam de
> disciplina do agente agora são verificados por código. Migração de baixo risco.

## TL;DR

```bash
# 1. Substitua .claude/, bin/ e tests/ pelos da v0.9.6
# 2. Rode as 10 suites (3 novas):
bash tests/framework/run-all.sh        # esperado: 11/11
# 3. Pronto. Nenhuma mudança em .planning/ de projetos existentes.
```

## O que muda no comportamento

### Gate 8 agora bloqueia mecanicamente
Antes: o workflow verify-phase instruía avaliar a quality bar — e dependia do
agente obedecer. Agora: `gsd-tools verify quality-bar <N>` valida o
QUALITY-BAR.md de verdade, e o hook `gsd-phase-transition-guard.sh` roda esse
check antes de qualquer transição de phase.

**Impacto em projeto em andamento:** se a phase atual tem QUALITY-BAR.md com
FAIL-BLOCK aberto, FAIL-DEBT sem linha em TECH-DEBT.md citando a phase, ou nem
tem QUALITY-BAR.md, a PRÓXIMA transição de phase vai bloquear. Isso é o
comportamento correto — mas se você precisa avançar antes de regularizar:
`export GSD_SKIP_TRANSITION_GUARD=true` + razão em DECISIONS.md.

Sintaxe de resolução: FAIL-BLOCK corrigido marca `[RESOLVIDO]` na própria
linha, com a evidência (ex.: `FAIL-BLOCK [RESOLVIDO] — .env removido, credencial rotacionada`).

### Wave-dispatcher agora calcula partição por código
O agente passa a chamar `gsd-tools partition` e obedecer à saída. Se você tinha
`parallelization.enabled: true`, nada a fazer — o agente novo já usa o comando.

### Skill-application-check cobre 73/73 skills
O hook vai começar a apontar skills citadas-mas-não-aplicadas que antes passavam
em silêncio (eram 12 com fingerprint; agora todas). É advisory — apontamentos
novos em phases antigas são informação, não bloqueio.

## Correções que você pode querer replicar em docs próprios

Se você copiou trechos dos guias v0.9.5 para docs do seu projeto:
- `gsd:tools.cjs` → `gsd-tools.cjs` (typo de sanitização)
- `/gsd:docs-index` → `/gsd:docs-update`
- `/gsd:tech-debt` → `/gsd:td-review`
- `/gsd:reconcile` → `/gsd:reconcile-state`
- `/gsd:verify <N>` → `/gsd:verify-phase <N>`
- `/gsd:suggestions` agora EXISTE (antes era citado sem existir)
- "7 gates" → "8 gates"

## Comandos novos do gsd-tools

```bash
node .claude/get-shit-done/bin/gsd-tools.cjs --help                    # agora funciona
node .claude/get-shit-done/bin/gsd-tools.cjs verify quality-bar <N>   # Gate 8 por script
node .claude/get-shit-done/bin/gsd-tools.cjs partition <tasks.json>   # partição de wave
```

## O que NÃO muda

- Nenhum arquivo de `.planning/` de projetos existentes
- Workflow do operador (`/gsd:go`, autopilot, comandos do dia a dia)
- Os 7 gates anteriores
- Scripts de deploy/backup
- config.json (nenhuma chave nova obrigatória)
