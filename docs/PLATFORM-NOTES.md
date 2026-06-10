# PLATFORM-NOTES.md

> Notas operacionais por plataforma. Framework GSD funciona em Windows, macOS e Linux. Algumas operações têm sintaxe específica por plataforma — este documento consolida.

---

## Compatibilidade verificada

| Plataforma | Shell padrão | Status | Notas |
|---|---|---|---|
| **Linux** (Ubuntu 22+, Fedora 38+) | bash | ✅ Suporte completo | Plataforma de desenvolvimento original do framework |
| **macOS** (12+) | zsh / bash | ✅ Suporte completo | Compatível, mesmas regras de Unix |
| **Windows 10/11** | PowerShell 5.1+ / pwsh 7+ | ✅ Suporte completo | Algumas operações usam sintaxe PS — documentadas abaixo |
| **WSL2** | bash | ✅ Suporte completo | Equivalente a Linux nativo |
| **Git for Windows** (bash.exe) | bash | ✅ Suporte completo | Recomendado em Windows nativo |

## Pré-requisitos comuns

Todas as plataformas:

- **Node.js 18+** (para `gsd-tools.cjs` e hooks JavaScript)
- **Python 3.11+** (para skills com scripts: `ui-ux-pro-max`, `bin/collect-metrics.sh`)
- **Git** (qualquer versão recente)
- **Claude Code 2.0+** (idealmente latest)

## Pré-requisitos específicos

### Windows nativo

- **Git for Windows** (recomendado — vem com bash.exe que executa hooks `.sh` do framework)
- **PowerShell 7+** (`pwsh`) recomendado — sintaxe mais moderna que PowerShell 5.1
- **Python via Windows Store** ou **python.org installer** com "Add to PATH" marcado

### macOS

- **Xcode Command Line Tools** (`xcode-select --install`) para compiladores nativos
- **Homebrew** recomendado para instalar Node/Python: `brew install node python git`

### Linux

- Apenas package manager nativo: `apt`, `dnf`, `pacman` etc.

---

## Operações com sintaxe diferente por plataforma

### Multi-line strings em git commit

**Linux/macOS (bash, zsh):**
```bash
git commit -m "$(cat <<'EOF'
título

corpo do commit
EOF
)"
```

**Windows (PowerShell):**
```powershell
git commit -m "primeira linha" -m "" -m "linhas seguintes"
# OU
@"
título

corpo do commit
"@ | Set-Content /tmp/msg.txt
git commit -F /tmp/msg.txt
Remove-Item /tmp/msg.txt
```

### Executar binário de venv Python

**Linux/macOS:**
```bash
./.venv/bin/pytest
./.venv/bin/ruff check .
./.venv/bin/mypy src/
```

**Windows:**
```powershell
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\mypy.exe src\
```

### Ativar virtualenv

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
# Se der erro de execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows cmd.exe:**
```cmd
.venv\Scripts\activate.bat
```

### Path separators

Framework usa `/` em paths (cross-platform compatible). Não use `\` em arquivos de configuração.

Quando precisar concatenar paths em scripts, **prefira**:
- Node: `path.join(...)`
- Python: `os.path.join(...)` ou `pathlib.Path`
- Bash: `"$DIR/$FILE"`

### Hooks `.sh` no Windows

Os hooks do framework (`.claude/hooks/*.sh`) são scripts bash. No Windows:

- **Git for Windows** instala bash.exe automaticamente — hooks rodam.
- **WSL2** funciona transparentemente.
- **PowerShell puro sem Git Bash**: hooks `.sh` falham silenciosamente. Instale Git for Windows.

---

## Convenções padronizadas pelo framework

### Encoding

- Todos os arquivos do framework: **UTF-8 sem BOM**
- Line endings: **LF** (não CRLF), inclusive em Windows
- Configurado via `.gitattributes`: `* text=auto eol=lf`

### Locale

- Output do framework: **pt-BR** (mensagens, comentários, prompts)
- Código gerado: respeita locale do projeto (`config.json` em `.planning/`)
- Datas: ISO 8601 (`YYYY-MM-DD`)

### Permissões de arquivo

Hooks `.sh` e scripts `bin/*.sh` precisam de bit executável:

```bash
chmod +x .claude/hooks/*.sh bin/*.sh
```

Em Windows, isso não se aplica (NTFS não tem o bit).

---

## Comandos de diagnóstico por plataforma

### Validar ambiente

```bash
# Cross-platform — funciona em todos
node --version           # ≥18
python3 --version        # ≥3.11 (Linux/macOS)
python --version         # Windows
git --version
```

### Listar hooks ativos

```bash
ls .claude/hooks/ | grep -v README   # Linux/macOS
Get-ChildItem .claude/hooks/ -Exclude README*   # Windows PowerShell
```

### Rodar testes do framework

Cross-platform:
```bash
bash tests/framework/run-all.sh
```

(Windows requer Git Bash.)

---

## FAQ

### "Meu Claude Code não acha o command `/gsd:bootstrap`"

- Verifique que `.claude/commands/gsd/bootstrap.md` existe
- Claude Code 2.0+ usa `:` como separador de namespace; versões mais antigas usavam `-`
- Framework usa formato canônico atual: `/gsd:command`

### "Hook não dispara"

- Verifique permissão executável (Linux/macOS): `ls -la .claude/hooks/`
- Verifique JSON do `settings.json`: `node -e "JSON.parse(require('fs').readFileSync('.claude/settings.json'))"`
- Hooks `.sh` precisam de bash disponível (Linux/macOS nativo, Git Bash em Windows)

### "Permissão diálogo aparece o tempo todo"

- v0.9+ usa `defaultMode: bypassPermissions` no `settings.json` — não deve aparecer
- Se aparecer mesmo assim, abra `.claude/settings.json` e verifique o campo
- Reinicie Claude Code após mudança

### "Python script da skill não roda"

- Verifique Python 3.11+ disponível: `python3 --version` (Linux/macOS) ou `python --version` (Windows)
- Skills com scripts usam apenas stdlib — não há dependências pip a instalar
- Se erro de permissão em Linux: `chmod +x .claude/skills/*/scripts/*.py`

---

## Suporte estendido

Para issues específicas de plataforma, abra entry em `.planning/SUGGESTIONS.md` com tag `[platform-issue]` e detalhes do ambiente.

O framework é mantido com prioridade de paridade entre Linux, macOS e Windows. Bug que aparece em uma plataforma e não em outras é tratado como regressão.
