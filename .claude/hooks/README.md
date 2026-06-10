# Claude Code Hooks — GSD Edition

Hooks operacionais do framework GSD que rodam em momentos específicos do ciclo de vida do Claude Code. Adicionados ao framework em v0.3.0.

## Hooks incluídos

| Hook | Tipo | Função |
|------|------|--------|
| `gsd-statusline.js` | Statusline | Mostra: modelo \| fase/tarefa atual \| diretório \| uso de contexto |
| `gsd-context-monitor.js` | PostToolUse/AfterTool | Injeta warnings quando contexto fica baixo (35% warning / 25% critical), forçando o agente a salvar estado |
| `gsd-prompt-guard.js` | UserPromptSubmit | Valida prompts contra padrões conhecidos de risco |
| `gsd-read-guard.js` | PreToolUse (Read) | Previne leitura de arquivos fora do escopo permitido |
| `gsd-workflow-guard.js` | Vários | Garante que workflows GSD sigam ordem correta (bootstrap antes de plan, plan antes de execute) |
| `gsd-check-update.js` | SessionStart | Verifica se há atualização disponível do GSD |
| `gsd-phase-boundary.sh` | PreToolUse | Bloqueia edição cruzada de fase (ex: editar arquivos da fase 3 durante fase 5) |
| `gsd-session-state.sh` | SessionStart/End | Persiste estado da sessão em `.planning/STATE.md` |
| `gsd-validate-commit.sh` | PreToolUse (Bash com git commit) | Valida mensagem de commit segue conventional commits |

## Como instalar

No arquivo `.claude/settings.json` do projeto, adicione:

```json
{
  "hooks": {
    "statusline": {
      "command": "node",
      "args": [".claude/hooks/gsd-statusline.js"]
    },
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "command": "node", "args": [".claude/hooks/gsd-context-monitor.js"] }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "command": "node", "args": [".claude/hooks/gsd-prompt-guard.js"] }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          { "command": "node", "args": [".claude/hooks/gsd-read-guard.js"] }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "command": "bash", "args": [".claude/hooks/gsd-validate-commit.sh"] }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "command": "bash", "args": [".claude/hooks/gsd-session-state.sh"] },
          { "command": "node", "args": [".claude/hooks/gsd-check-update.js"] }
        ]
      }
    ]
  }
}
```

**Permissões:** dar `chmod +x` nos `.sh`:

```bash
chmod +x .claude/hooks/*.sh
```

Os `.js` rodam via `node`, não precisam executable bit.

## Requisitos

- **Node.js 18+** (para os `.js`)
- **Bash** (para os `.sh`, funciona também em Git Bash no Windows)
- `jq` é opcional mas recomendado para parsing JSON em scripts bash

## Ordem de carregamento

1. `SessionStart` hooks carregam primeiro (session state + check update)
2. Statusline roda continuamente em background
3. `UserPromptSubmit` filtra cada prompt antes de chegar ao modelo
4. `PreToolUse` valida antes de cada ferramenta
5. `PostToolUse` injeta contexto depois de ferramenta

## Desabilitar hooks específicos

Remover do `settings.json`. Não apagar os arquivos — algum outro projeto pode usar.

Para desabilitar globalmente (todos os projetos): comentar o bloco inteiro de `hooks` no `~/.claude/settings.json`.

## Configuração por hook

### `gsd-context-monitor.js`

Thresholds configuráveis via env:
- `GSD_CONTEXT_WARNING_THRESHOLD=35` (padrão 35%)
- `GSD_CONTEXT_CRITICAL_THRESHOLD=25` (padrão 25%)

### `gsd-statusline.js`

Lê `.planning/STATE.md` do projeto automaticamente. Formato do statusline:

```
Opus 4.7 | M3-checkout · Phase 07 · Sprint 02 · task 5/9 | /home/user/acme | 72% used
```

### `gsd-prompt-guard.js`

Bloqueia padrões como:
- "execute sem revisar"
- "delete tudo"
- "force push"
- Comandos destrutivos em produção

Permite override com `--confirm-destructive`.

## Troubleshooting

**Hook "error" aparecendo no Claude Code:**
- Verifica logs em `/tmp/claude-hook-{session_id}.log`
- Maioria das vezes é timeout de stdin (10s) ou Node/Bash ausente no PATH

**Statusline vazio:**
- Projeto não tem `.planning/STATE.md` — rodar `/gsd-bootstrap` primeiro

**`gsd-validate-commit.sh` rejeitando mensagens legítimas:**
- Ajustar padrão no topo do arquivo (variável `VALID_PREFIXES`)
- Convenção padrão: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`

## Fonte

Hooks vêm do GSD base (v1.36.0). Integrados ao framework em v0.3.0.
