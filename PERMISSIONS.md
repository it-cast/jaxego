# PERMISSIONS.md — Como o framework lida com permissões

> Documento curto. Para entender ou ajustar o comportamento de permissões.

## Estado atual (default do framework v0.4.1)

**Bypass total ativado.** O Claude Code não pergunta antes de executar Bash, Read, Write, Edit, etc. Configurado em `.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

## O que isso significa na prática

Claude executa **qualquer comando** sem perguntar. Inclui:

- Operações destrutivas (`rm -rf`, `git push --force`)
- Instalação de pacotes (`npm install`, `pip install`)
- Requisições HTTP (`curl`, `wget`)
- Modificação de arquivos fora do projeto
- Comandos do shell em geral

**Trade-off explícito:** velocidade vs. segurança. Você ganhou velocidade. A rede de segurança agora é **disciplina de git**.

## Como você se protege com bypass total

1. **`git init` e commits frequentes** — antes de qualquer milestone, commit limpo. Se Claude bagunçar, `git reset --hard` recupera.
2. **Rodar em VPS/container ou pasta isolada** — não em `/home/$USER` direto. Limita raio de explosão.
3. **Backup automático** do `.planning/` — esse diretório é o cérebro do projeto. Se sumir, perde contexto.
4. **Não use bypass em produção** — em servidor com banco real, rodar Claude Code é arriscado mesmo sem bypass. Com bypass, é temerário.

## Os 4 modos disponíveis no Claude Code

Você pode trocar `defaultMode` em `.claude/settings.json` para qualquer um destes:

| Modo | Comportamento | Quando usar |
|------|---------------|-------------|
| `default` | Pergunta para cada operação destrutiva ou nova | Projeto crítico, dados sensíveis |
| `acceptEdits` | Auto-aprova Read/Edit/Write, pergunta só pra Bash | Equilíbrio razoável |
| `bypassPermissions` | Não pergunta nada (modo atual do framework) | Velocidade total, projeto com git |
| `plan` | Modo planejamento — Claude propõe, você aprova plano antes de executar | Mudanças grandes |

## Como reverter para modo seguro

Edite `.claude/settings.json` e troque:

```json
{
  "permissions": {
    "defaultMode": "default"
  }
}
```

Salve. Próxima sessão do `claude` já vem em modo seguro.

## Como ativar bypass apenas em sessão específica

Se preferir manter `default` no `settings.json` e ativar bypass por sessão quando quiser:

```bash
claude --dangerously-skip-permissions
```

Roda essa sessão em bypass, próxima volta ao default.

## Allowlist seletiva (alternativa ao bypass total)

Se quiser velocidade no dia a dia mas segurança em comandos estranhos, troque `defaultMode` para `default` e adicione bloco `allow`:

```json
{
  "permissions": {
    "defaultMode": "default",
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "Bash(npm *)", "Bash(npx *)",
      "Bash(python3 *)", "Bash(pip *)", "Bash(uv *)", "Bash(pytest *)",
      "Bash(node *)",
      "Bash(git *)",
      "Bash(ng *)", "Bash(ionic *)",
      "Bash(docker *)", "Bash(docker compose *)",
      "Bash(alembic *)",
      "Bash(ruff *)",
      "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)", "Bash(ls *)",
      "Bash(cat *)", "Bash(echo *)", "Bash(cd *)", "Bash(pwd *)",
      "Bash(bash *)", "Bash(curl *)", "Bash(wget *)",
      "Bash(make *)", "Bash(find *)",
      "Task", "TodoWrite", "WebFetch"
    ]
  }
}
```

Cobre 95% das operações sem pedir aprovação. Operações fora da lista (ex: `rm -rf`, `chmod 777`, comandos não previstos) ainda perguntam.

## Hooks do GSD continuam ativos em qualquer modo

Os 9 hooks do GSD (statusline, context-monitor, workflow-guard, etc.) **funcionam independente do modo de permissão**. Eles validam workflow, monitoram contexto e protegem boundary de fase mesmo em bypass total.

Se quiser desabilitar hooks também: remover bloco `hooks` do `settings.json`.

## Resumo em 3 linhas

- **Default do framework:** bypass total. Velocidade máxima.
- **Para reverter:** trocar `defaultMode` para `default` em `.claude/settings.json`.
- **Rede de segurança:** git frequente. Sem git, bypass é perigoso.
