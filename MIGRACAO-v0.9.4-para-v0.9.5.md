# Migração v0.9.4 → v0.9.5

> Como aplicar a v0.9.5 a um projeto que já usa o gsd-framework v0.9.x. Tudo é **aditivo** — nada do que existe quebra.

## TL;DR

A v0.9.5 não altera nenhum workflow existente de forma incompatível. Você pode copiar os arquivos novos por cima e seguir usando exatamente como antes. As novidades só entram em ação quando você as invoca (`/gsd:go`) ou quando o roadmapper grava as flags novas.

## Arquivos novos (copiar para o projeto)

```
.claude/skills/domain/fastapi-production-patterns/    (SKILL.md + triggers.yaml)
.claude/skills/domain/github-actions-ci/              (SKILL.md + triggers.yaml)
.claude/skills/ux-advanced/data-tables-ux/            (SKILL.md + triggers.yaml)
.claude/skills/ux-advanced/search-filter-ux/          (SKILL.md + triggers.yaml)
.claude/skills/meta/parallel-orchestration/           (SKILL.md + triggers.yaml)
.claude/skills/quality/senior-quality-bar/            (SKILL.md + triggers.yaml)  ← Gate 8
.claude/agents/gsd-wave-dispatcher.md
.claude/commands/gsd/go.md
.claude/get-shit-done/workflows/go.md
bin/collect-framework-telemetry.sh                    ← mede o framework, não o projeto
tests/framework/test_v095_additions.sh
```

## Correção crítica de portabilidade (aplicar em projeto que veio de versão anterior)

A v0.9.5 corrigiu 733 paths Windows hardcoded (`C:/Projetos/global/...`). Se seu projeto foi inicializado a partir de uma versão anterior, rode a mesma correção:

```bash
for f in $(grep -rl "C:/Projetos/global/" .claude/ 2>/dev/null); do
  sed -i 's#C:/Projetos/global/#./#g' "$f"
done
# verificar: deve dar 0
grep -rn "C:/Projetos" .claude/ | wc -l
```

## Arquivos alterados (re-aplicar edições, ou copiar inteiros)

| Arquivo | Mudança |
|---|---|
| `CLAUDE.md` | versão, contadores, matriz de skills (+data-tables, +search-filter, +fastapi, +ci), `/gsd:go` na lista de comandos, arquitetura em camadas |
| `.claude/agents/gsd-roadmapper.md` | seção "Orchestration metadata por phase" (flags, pre-phase, post-execute, parallel-hint) |
| `.claude/agents/gsd-plan-checker.md` | clause type `config:` + flags has_api/has_admin/has_ai |
| `.claude/get-shit-done/workflows/execute-phase.md` | branch task_level → gsd-wave-dispatcher; corrige gsd-task-executor → gsd-executor |
| `.claude/get-shit-done/workflows/autopilot.md` | lê parallel-hint e ativa task_level por phase |
| `.claude/get-shit-done/templates/config.json` | bloco parallelization com wave_dispatcher |
| `.claude/skills/SKILLS_INDEX.md` | 72 skills + nota de autoridade |
| `tests/framework/run-all.sh` | registra test_v095_additions.sh |

## Para ativar o paralelismo de execução (opcional)

No `.planning/config.json` do projeto:

```json
"parallelization": { "enabled": true, "task_level": true, "max_concurrent_agents": 3, "wave_dispatcher": true }
```

E garantir que o ROADMAP tenha `parallel-hint:` por phase (rode `/gsd:go` ou re-rode o roadmapper para phases antigas que não têm a linha). Sem a flag, tudo continua serial — comportamento idêntico à v0.9.4.

## Verificação pós-migração

```bash
bash tests/framework/run-all.sh        # esperado: 7/7 suites passed
find .claude/skills -name SKILL.md | wc -l   # esperado: 72
```

## O que NÃO mudou

- Os 7 gates anteriores: idênticos. **Novo: Gate 8 (Senior Quality Bar)** — bloqueante em verify-phase, enforced por `gsd-tools verify quality-bar` e pelo hook de transição
- O fluxo manual (discuss → ui → research → plan → execute → verify): idêntico
- `/gsd:autopilot`: mesma semântica, só ganhou o lookahead de parallel-hint
- Deploy (v0.9.4): intocado
