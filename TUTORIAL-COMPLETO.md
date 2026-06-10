# Tutorial completo — GSD Framework v0.4.0

**Guia operacional passo a passo.** Inclui prompts literais para copiar/colar, exemplos de output esperado, armadilhas específicas e como forçar comportamentos corretos do Claude.

**Cenário exemplo usado ao longo do tutorial:** você está construindo **"MercadoPRO"**, um marketplace B2B onde comerciantes locais vendem para atacadistas. Stack: FastAPI + Angular/Ionic + MySQL. Locale pt-BR. O exemplo é genérico — adapte ao seu projeto real.

**Tempo total:** 3-5 horas na primeira vez. Depois, ~30 min para setup de projeto novo.

**Atenção:** este tutorial assume que você está usando **Claude Code** (terminal ou IDE com plugin). Se estiver usando Claude.ai web, os slash commands não existem — consulte a seção "Modo Web" no final.

---

# SUMÁRIO

- FASE 0 — Validação de pré-requisitos
- FASE 1 — Descompactar e validar
- FASE 2 — Preencher documentação do projeto
- FASE 3 — Identidade visual (crítico se tem UI)
- FASE 4 — Arquivos extras (PDFs, XLSX, wireframes)
- FASE 5 — Configurar hooks e settings
- FASE 6 — Primeiro contato com Claude: bootstrap
- FASE 7 — Quebrar milestone em sprints
- FASE 8 — Executar primeiro sprint
- FASE 9 — Fechar sprint e métricas
- FASE 10 — Ciclo contínuo
- FASE 11 — Telemetria e iteração
- APÊNDICE A — Prompts de emergência
- APÊNDICE B — Modo Web
- APÊNDICE C — Troubleshooting

---

# FASE 0 — Validação de pré-requisitos (5 min)

Não pule isso. 80% dos problemas que você vai ter depois nascem de pré-requisito faltando.

## 0.1 Versões de Node, Python, Git

```bash
node --version
python3 --version
git --version
```

**Esperado:** Node ≥ 18, Python ≥ 3.10, Git qualquer. Se Node < 18, hooks quebram e `gsd-tools.cjs` falha. Se Python < 3.10, scripts do `ui-ux-pro-max` e `convert-docs.sh` não rodam.

Para atualizar Node:
```bash
nvm install 20 && nvm use 20
```

## 0.2 Claude Code instalado

```bash
which claude
```

Se não retornou caminho, instale antes de continuar: https://docs.claude.com/en/docs/claude-code

## 0.3 Pandoc e openpyxl (opcionais)

Só precisa se vai ter arquivos `.docx`, `.pptx`, `.xlsx`:

```bash
# pandoc
sudo apt install pandoc  # Linux
brew install pandoc      # macOS

# openpyxl
pip install openpyxl
```

## 0.4 Editor aberto

Você vai preencher uns 6-8 arquivos nas próximas horas. Abra seu editor favorito apontando para onde vai descompactar.

---

# FASE 1 — Descompactar e validar (10 min)

## 1.1 Descompactar

```bash
cd ~/projetos                 # onde você guarda projetos
unzip gsd-framework.zip
mv gsd-framework mercadopro   # renomeia com slug do SEU projeto (kebab-case)
cd mercadopro
```

## 1.2 Entender a estrutura

```bash
ls -la
```

**Você vê:**

```
.claude/                     skills, agents, commands, hooks, workflows
.planning/                   estado do projeto (bootstrap vai popular)
docs/                        templates de documentação
specs/                       templates de specs YAML
bin/                         scripts utilitários
tests/                       testes do framework em si
tooling/                     configs CI, linters
CLAUDE.md                    instruções para o Claude neste projeto
FRAMEWORK-STATUS.md          changelog do framework
INSTALLATION.md              guia resumido
TUTORIAL-COMPLETO.md         este arquivo
README.md
```

## 1.3 Git init — baseline

```bash
git init
git add .
git commit -m "chore: inicializa projeto a partir do gsd-framework v0.9.4"
```

Isso dá ponto de retorno caso algo quebre nas próximas horas.

## 1.4 Validar integridade

```bash
bash tests/framework/run-all.sh
```

**Output esperado:**

```
→ test_structure.sh
  ✓  passed
→ test_plan_checker.sh
  ✓  passed
→ test_reconcile.sh
  ✓  passed
→ test_gate_bypasses.sh
  ✓  passed
→ test_sprint_checker.sh
  ✓  passed

===============================
11/11 suites passed
```

**Se quebrou:** não prossiga, descompacte de novo em diretório limpo.

## 1.5 Permissões de execução

```bash
chmod +x bin/*.sh
chmod +x .claude/hooks/*.sh
chmod +x .claude/get-shit-done/bin/*.cjs 2>/dev/null || true
```

## 1.6 Teste do gsd-tools

```bash
node .claude/get-shit-done/bin/gsd-tools.cjs --help
```

Esperado: lista de comandos aparece (`state load`, `resolve-model`, etc.). Se deu erro, provavelmente Node < 18.

---

# FASE 2 — Preencher documentação do projeto (60-90 min)

Parte longa mas **fundamento do projeto todo**. O que você preenche aqui é o contexto que o Claude usa em TODOS os prompts seguintes. Vagueza aqui = imprecisão depois.

## 2.1 `docs/project-brief.md` — o documento mais importante

Abra o arquivo. 12 seções com placeholders. Exemplo preenchido para MercadoPRO:

```markdown
# Project Brief — MercadoPRO

## 1. Proposta de valor
Marketplace B2B que conecta comerciantes locais (pequenos varejistas) 
a atacadistas regionais, eliminando intermediários. Pedidos mínimos 
de R$ 500, pagamento em até 30 dias, entrega agendada.

## 2. Usuário-alvo primário
**Comerciante varejista** (dono ou gerente de mercadinho/padaria/bar):
- 30-55 anos
- Não é tech-savvy (usa WhatsApp e Pix confortavelmente, nada mais)
- Faz pedido para reposição semanal

**Usuário secundário:** atacadista (admin do próprio perfil).
**NÃO é usuário:** consumidor final.

## 3. Problema que resolve
Comerciante perde 2-4h/semana ligando para atacadistas comparando 
preços. Atacadista perde pedidos porque comerciante liga primeiro 
para concorrente que atendeu mais rápido.

## 4. Modelo de negócio
Comissão de 3% sobre cada pedido concluído, paga pelo atacadista.

## 5. KPI primário
GMV/mês. Meta 6m: R$ 500k. Meta 12m: R$ 3M.

## 6. KPIs secundários
- Comerciantes ativos/mês
- Atacadistas ativos/mês
- NPS comerciante
- Taxa de repetição

## 7. Escopo MVP
- Cadastro comerciante e atacadista
- Catálogo de produtos
- Pedido com Pix/boleto
- Push notification status
- Admin interno para aprovar cadastros

## 8. FORA DE ESCOPO (absoluto)
- App para consumidor final
- Frete via marketplace
- Cartão de crédito
- Chat in-app
- Reviews e ratings

## 9. Stack (detalhes em specs/stack.yaml)
- FastAPI + Python 3.11 + MySQL 8
- Angular 19 + Ionic 8 + Capacitor (mobile)
- Angular 19 web (admin atacadista e admin interno)

## 10. Restrições
- Solo dev, 20h/semana
- MVP em produção em 4 meses
- LGPD e fiscal obrigatórios

## 11. Decisões tomadas (ADRs)
- ADR-001: MySQL em vez de Postgres (time conhece melhor)
- ADR-002: Ionic em vez de React Native (single team)
- ADR-003: Pagarme como PSP

## 12. Riscos conhecidos
- Liquidez marketplace (chicken-and-egg)
- Atacadista pode não aceitar pagamento 30 dias
- Compliance LGPD/fiscal mal implementado trava projeto
```

**Regras ao preencher:**

- Se não sabe uma resposta, escreve `a definir` em vez de inventar
- **Seção 8 (fora de escopo) é MAIS importante que a 7 (escopo)** — é ela que evita scope creep
- Seção 2 define slicing strategy: usuário externo → `vertical_value`, operador interno → `admin_first`

Commit:

```bash
git add docs/project-brief.md
git commit -m "docs: preenche project-brief"
```

## 2.2 `specs/project.yaml`

```yaml
name: "MercadoPRO"
slug: "mercadopro"
description: "Marketplace B2B conectando varejistas a atacadistas"
locale: "pt-BR"
platforms:
  - web
  - mobile
  - api
owner: "Seu Nome"
email: "voce@dominio.com"
created: "2026-04-23"
```

## 2.3 `specs/stack.yaml` — seja específico

```yaml
backend:
  language: "python"
  version: "3.11"
  framework: "fastapi"
  framework_version: "0.109"
  orm: "sqlalchemy"
  async: true
  queue: "celery"
  broker: "redis"

frontend_web:
  framework: "angular"
  version: "19"
  ui_kit: "angular-material"
  build: "vite"

frontend_mobile:
  framework: "angular"
  version: "19"
  ui_kit: "ionic"
  ui_version: "8"
  wrapper: "capacitor"
  wrapper_version: "6"
  targets: ["android", "ios"]

database:
  primary: "mysql"
  version: "8.0"
  migrations: "alembic"
  cache: "redis"

infra:
  hosting: "vps-hetzner"
  container: "docker"
  orchestration: "docker-compose"

observability:
  logs: "journalctl + loki"
  metrics: "prometheus + grafana"
  errors: "sentry"

ci:
  provider: "github-actions"

auth:
  strategy: "jwt"

payment:
  psp_primary: "pagarme"
  methods: ["pix", "boleto"]

storage:
  object: "backblaze-b2"
```

## 2.4 `specs/database.yaml` (se tem DB)

Esboço de tabelas principais. Vai evoluir nos sprints:

```yaml
tables:
  users:
    description: "Auth base"
    columns:
      - id: "uuid, PK"
      - email: "string 255, unique"
      - password_hash: "string 255"
      - type: "enum(comerciante, atacadista, admin)"
      - status: "enum(pending, active, suspended)"
    indexes: ["email", "type+status"]

  comerciantes:
    description: "Perfil comerciante varejista"
    columns:
      - id: "uuid, PK, FK users(id)"
      - razao_social: "string 200"
      - cnpj: "string 14, unique"
      - cep: "string 8"
    indexes: ["cnpj", "cep"]

  atacadistas:
    description: "Perfil atacadista"
    columns:
      - id: "uuid, PK, FK users(id)"
      - razao_social: "string 200"
      - cnpj: "string 14, unique"
      - pedido_minimo_cents: "int"
    indexes: ["cnpj"]

  produtos:
    description: "Catálogo por atacadista"
    columns:
      - id: "uuid, PK"
      - atacadista_id: "uuid, FK"
      - nome: "string 200"
      - preco_cents: "int"
      - estoque: "int"
      - ativo: "boolean"
    indexes: ["atacadista_id+ativo"]

  pedidos:
    description: "Pedido comerciante → atacadista"
    columns:
      - id: "uuid, PK"
      - codigo: "string 10, unique"
      - comerciante_id: "uuid, FK"
      - atacadista_id: "uuid, FK"
      - status: "enum(rascunho, confirmado, pago, em_transito, entregue, cancelado)"
      - total_cents: "int"
    indexes: ["comerciante_id+status", "atacadista_id+status"]
```

## 2.5 `specs/rules.yaml`

```yaml
rules:
  - id: R-001
    description: "Comerciante só cria pedido se cadastro aprovado"
    criticality: high
  - id: R-002
    description: "Pedido precisa atingir pedido_minimo do atacadista"
    criticality: high
  - id: R-003
    description: "Preço do produto é capturado no momento do pedido"
    criticality: high
  - id: R-004
    description: "Comissão 3% subtraída do repasse ao atacadista"
    criticality: high
  - id: R-005
    description: "LGPD: exclusão solicitada anonimiza dados em 30 dias"
    criticality: high
    legal: "LGPD art. 18"
```

Commit:

```bash
git add specs/
git commit -m "docs: preenche specs do projeto"
```

---

# FASE 3 — Identidade visual (30-60 min, crítico se tem UI)

Fase mais negligenciada e a que mais quebra sprints depois. **Não pule.**

## 3.1 `docs/identidade-visual/tokens.json` — OBRIGATÓRIO

Sem esse arquivo com mínimo de `color` + `space`, sprints com UI bloqueiam no gate 2.

**Template completo pronto para copiar e ajustar:**

```json
{
  "color": {
    "brand": {
      "50":  { "value": "#eff6ff" },
      "100": { "value": "#dbeafe" },
      "500": { "value": "#3b82f6" },
      "600": { "value": "#2563eb" },
      "700": { "value": "#1d4ed8" },
      "900": { "value": "#1e3a8a" }
    },
    "accent": {
      "500": { "value": "#f59e0b" },
      "600": { "value": "#d97706" }
    },
    "text": {
      "primary":   { "value": "#111827" },
      "secondary": { "value": "#6b7280" },
      "disabled":  { "value": "#9ca3af" },
      "inverse":   { "value": "#ffffff" }
    },
    "surface": {
      "default":  { "value": "#ffffff" },
      "elevated": { "value": "#f9fafb" },
      "raised":   { "value": "#f3f4f6" }
    },
    "border": {
      "subtle":  { "value": "#f3f4f6" },
      "default": { "value": "#e5e7eb" },
      "strong":  { "value": "#d1d5db" }
    },
    "semantic": {
      "success": { "value": "#10b981" },
      "warning": { "value": "#f59e0b" },
      "danger":  { "value": "#ef4444" },
      "info":    { "value": "#3b82f6" }
    }
  },
  "space": {
    "0":   { "value": "0" },
    "xs":  { "value": "4px" },
    "sm":  { "value": "8px" },
    "md":  { "value": "16px" },
    "lg":  { "value": "24px" },
    "xl":  { "value": "32px" },
    "2xl": { "value": "48px" },
    "3xl": { "value": "64px" }
  },
  "radius": {
    "none": { "value": "0" },
    "sm":   { "value": "4px" },
    "md":   { "value": "8px" },
    "lg":   { "value": "12px" },
    "full": { "value": "9999px" }
  },
  "typography": {
    "family": {
      "sans":  { "value": "Inter, system-ui, sans-serif" },
      "mono":  { "value": "JetBrains Mono, monospace" }
    },
    "size": {
      "xs":   { "value": "12px" },
      "sm":   { "value": "14px" },
      "base": { "value": "16px" },
      "lg":   { "value": "18px" },
      "xl":   { "value": "24px" },
      "2xl":  { "value": "32px" },
      "3xl":  { "value": "48px" }
    },
    "weight": {
      "regular":  { "value": "400" },
      "medium":   { "value": "500" },
      "semibold": { "value": "600" },
      "bold":     { "value": "700" }
    }
  },
  "motion": {
    "duration": {
      "fast":   { "value": "150ms" },
      "normal": { "value": "250ms" },
      "slow":   { "value": "400ms" }
    },
    "easing": {
      "ease_out": { "value": "cubic-bezier(0.16, 1, 0.3, 1)" },
      "ease_in":  { "value": "cubic-bezier(0.7, 0, 0.84, 0)" },
      "spring":   { "value": "cubic-bezier(0.34, 1.56, 0.64, 1)" }
    }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px rgba(0,0,0,0.05)" },
    "md": { "value": "0 4px 6px rgba(0,0,0,0.1)" },
    "lg": { "value": "0 10px 15px rgba(0,0,0,0.1)" }
  }
}
```

**Sem designer no time:**
- Paletas: https://coolors.co
- Escalas prontas: https://tailwindcss.com/docs/customizing-colors
- Fontes: https://fontpair.co

**Regra de ouro:** token provisório é 10x melhor que token ausente. Enforcement bloqueia ausência, não escolha ruim.

## 3.2 `docs/identidade-visual/brand.md`

Exemplo preenchido:

```markdown
# Brand — MercadoPRO

## Voz
**É:** direta, prática, confiável, respeitosa
**NÃO é:** formal demais, gírias, jovem demais

## Tom por contexto

| Contexto         | Tom                      | Exemplo                             |
|------------------|--------------------------|-------------------------------------|
| Onboarding       | Acolhedor, claro         | "Vamos configurar seu cadastro"     |
| Ação primária    | Direto                   | "Fazer pedido"                      |
| Erro recuperável | Neutro, orientador       | "CNPJ inválido. Confirme os dígitos" |
| Erro grave       | Honesto, com caminho     | "Não conseguimos processar. Tente em instantes." |
| Confirmação      | Tranquilizador           | "Pedido recebido. Prazo: 2 dias."   |
| Empty state      | Orientador, convidativo  | "Ainda sem pedidos. Ver catálogo →" |

## Vocabulário canônico

**Usar:**
- "pedido" (não "ordem")
- "atacadista" (não "fornecedor")
- "comerciante" (não "cliente")
- "você" (nunca "tu" nem "o senhor")
- "R$" (não "BRL")

**Evitar:**
- "nosso sistema" → usar "MercadoPRO" ou ação direta
- "infelizmente" → tom derrotista
- "por favor aguarde" → usar "carregando"
- "erro 500" → sempre traduzir erro técnico

## Gramática
- Tratamento: "você" (3ª pessoa)
- CTAs máximo 3 palavras: "Fazer pedido", "Ver catálogo"
- Números em R$: "R$ 1.234,56" (não "1234.56")
- Datas: "hoje", "ontem", "há 2 dias" (não ISO cru)

## Acessibilidade de copy
- Nível 8ª série (comerciante não é tech)
- Sem jargão
```

## 3.3 `design-system.md` — opcional

Vazio no dia 1, cresce por sprint.

Commit:

```bash
git add docs/identidade-visual/
git commit -m "docs: identidade visual inicial"
```

---

# FASE 4 — Arquivos extras (20-30 min)

Se tem pesquisa, pitch, wireframes, XLSX — joga tudo agora.

## 4.1 Criar pastas

```bash
mkdir -p docs/business docs/research
mkdir -p docs/identidade-visual/wireframes docs/identidade-visual/mockups
```

## 4.2 Copiar arquivos

```bash
cp ~/Documents/pitch.pdf docs/business/
cp ~/Documents/swot-2026.xlsx docs/business/
cp ~/Documents/pesquisa-comerciantes.pdf docs/research/
cp ~/Downloads/home-v0.html docs/identidade-visual/wireframes/home-mobile.html
```

## 4.3 Converter XLSX/DOCX/PPTX

```bash
bash bin/convert-docs.sh
```

**Output:**

```
Escaneando docs/...

✓  gerado: docs/business/swot-2026.xlsx.md

===============================
Convertidos:  1
Já atuais:    0
Falhados:     0
```

## 4.4 INDEX.md em cada pasta

Template pronto em `.claude/get-shit-done/templates/INDEX-subpasta.md`:

```bash
cp .claude/get-shit-done/templates/INDEX-subpasta.md docs/business/INDEX.md
```

Edite e preencha. Exemplo `docs/business/INDEX.md`:

```markdown
# docs/business/ — INDEX

> Pitch, SWOT, análise de mercado.

## Arquivos

### Alta relevância (ler ao planejar milestones estratégicos)
- `pitch-investidores.pdf` (24p) — Deck mar/2026. 
  Páginas 3-7: problema e mercado. Página 18: projeção financeira.
  **Atenção:** escopo MVP no deck era maior; seguir project-brief atual.

- `swot-2026.xlsx.md` — SWOT interna abr/2026. 
  Fraquezas listadas devem virar riscos no ROADMAP.

### Referência
- `swot-2026.xlsx` — original preservado; use o .md

## Última revisão: 2026-04-23
```

## 4.5 Atualizar `docs/INDEX.md`

```markdown
# docs/ — INDEX

## Canônicos
- `project-brief.md` — fonte de verdade
- `INDEX.md` — este arquivo

## Subpastas
- `adrs/` — decisões arquiteturais
- `identidade-visual/` — tokens, brand, wireframes
- `business/` — pitch, SWOT
- `research/` — pesquisa, concorrentes

## Última revisão: 2026-04-23
```

Commit:

```bash
git add docs/
git commit -m "docs: adiciona business, research, wireframes com INDEX.md"
```

---

# FASE 5 — Configurar hooks e settings (10 min)

## 5.1 Verificar `.claude/settings.json`

```bash
cat .claude/settings.json | head -50
```

Deve ter bloco `"permissions"` e `"hooks"`.

## 5.2 Template de settings.json completo

Se precisar recriar:

```json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "Bash(npm *)", "Bash(npx *)",
      "Bash(python3 *)", "Bash(python *)", "Bash(pip *)", "Bash(uv *)",
      "Bash(pytest *)",
      "Bash(node *)",
      "Bash(git *)",
      "Bash(ng *)", "Bash(ionic *)",
      "Bash(docker *)", "Bash(docker compose *)",
      "Bash(alembic *)",
      "Bash(ruff *)",
      "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)", "Bash(ls *)",
      "Bash(cat *)", "Bash(echo *)",
      "Bash(cd *)", "Bash(pwd *)",
      "Bash(bash *)",
      "Task", "TodoWrite", "WebFetch"
    ]
  },
  "hooks": {
    "statusline": {
      "command": "node",
      "args": [".claude/hooks/gsd:statusline.js"]
    },
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "command": "node", "args": [".claude/hooks/gsd:context-monitor.js"] }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "command": "node", "args": [".claude/hooks/gsd:prompt-guard.js"] }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "command": "bash", "args": [".claude/hooks/gsd:validate-commit.sh"] }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "command": "bash", "args": [".claude/hooks/gsd:session-state.sh"] }
        ]
      }
    ]
  }
}
```

## 5.3 Teste de hook

```bash
echo '{}' | node .claude/hooks/gsd:statusline.js
```

Deve retornar JSON. Se erro, verifique Node 18+.

Commit:

```bash
git add .claude/settings.json
git commit -m "chore: configura hooks"
```

---

# FASE 6 — Primeiro contato com Claude: bootstrap (15-20 min)

## 6.1 Abrir Claude Code no diretório

```bash
cd ~/projetos/mercadopro
claude
```

Ou IDE com plugin Claude Code, abrir pasta do projeto.

## 6.2 Primeiro prompt — validação de contexto

**Copie e cole exatamente:**

```
Estou iniciando um projeto novo usando o gsd-framework v0.9.4. 

Antes de qualquer coisa, faça em ordem:
1. Leia CLAUDE.md integralmente
2. Leia FRAMEWORK-STATUS.md — entenda em que versão estamos e quais limitações conhecidas existem (listadas como "O que esta versão NÃO resolve")
3. Liste o que você vê em docs/ e specs/ com uma frase por arquivo
4. Me confirme explicitamente: "li CLAUDE.md, li FRAMEWORK-STATUS, entendi que estamos em v0.4.0 com as seguintes limitações conhecidas: [liste 3 principais]"

Só prossiga para o próximo passo após eu confirmar que essa leitura está correta.
```

**Por que esse prompt:** estabelece o padrão de interação. Se você aceita "eu li o arquivo" sem prova, vai aceitar depois. Esse é o momento de firmar o tom.

**O que esperar:** Claude lê, lista, confirma. Exemplo de resposta boa:

```
Li CLAUDE.md. Confirma que este é o arquivo de instruções do projeto com ~40 
linhas definindo o slug, locale, estratégia de orquestração...

Li FRAMEWORK-STATUS.md. Estamos em v0.4.0. As 3 principais limitações 
conhecidas documentadas são:
1. Workflows do upload não conhecem meu enforcement (sprint_ui_matrix, 
   visual_tokens_mode) — usar workflows como 'autonomous' ou 'ship' 
   bypassa disciplina
2. Testes das 36 agentes/76 workflows são apenas de existência, não semântica
3. Zero field data ainda — framework teoricamente completo mas não validado

Arquivos em docs/:
- project-brief.md — brief do projeto [preenchido/vazio]
- identidade-visual/tokens.json — tokens de design [presente/ausente]
...

Arquivos em specs/:
- project.yaml — metadata do projeto
...

Confirmo entendimento. Prossigo?
```

**Se Claude pular algum passo ou fizer resumo genérico:**

```
Você não fez o passo 4. Me confirme explicitamente as 3 limitações 
conhecidas do framework v0.4.0 lendo a seção "O que esta versão NÃO 
resolve" do FRAMEWORK-STATUS.md. Cole o texto literal, não paráfrase.
```

## 6.3 Rodar bootstrap

```
/gsd:bootstrap
```

## 6.4 O que vai acontecer — passo a passo

### Passo A — Claude lê seus docs

Ele vai:
- Ler `docs/project-brief.md`
- Ler `specs/*.yaml`
- Ler `docs/identidade-visual/tokens.json`, `brand.md`
- Listar subpastas

**Output típico:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP — síntese do projeto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projeto: MercadoPRO
Slug: mercadopro
Locale: pt-BR
Plataformas: web, mobile, api

Proposta: Marketplace B2B conectando varejistas a atacadistas...

Usuário primário: Comerciante varejista (30-55, não tech-savvy)
Usuário secundário: Atacadista
NÃO é usuário: Consumidor final

Stack: FastAPI + Angular 19 + Ionic 8 + MySQL 8 + Docker

KPI primário: GMV/mês (meta 6m R$ 500k; 12m R$ 3M)

Escopo MVP:
- Cadastro comerciante e atacadista
- Catálogo de produtos
- Pedido com Pix/boleto
- Push notification
- Admin interno

FORA de escopo:
- App consumidor final
- Cartão de crédito
- Chat in-app

Identidade visual: tokens.json com color+space+radius+typography+motion+shadow ✓
Brand.md: voz, tom, vocabulário preenchido ✓

Arquivos extras detectados:
- docs/business/pitch-investidores.pdf
- docs/business/swot-2026.xlsx.md
- docs/research/pesquisa-comerciantes.pdf

Divergências com sua intenção? [s/N]
```

### Passo B — confirmar síntese

Se bateu: `N`.

Se errou, correção específica:

```
Sim. Você entendeu que "admin interno" é plataforma separada, mas 
é parte do admin do atacadista com feature flag para role. Registre 
antes de prosseguir.
```

### Passo C — slicing strategy

```
Strategy detectada: vertical_value
(usuário é comerciante externo; cada sprint entrega valor pra ele)

Alternativa: admin_first (monta admin primeiro)

Confirmar [vertical_value]?
```

Para MercadoPRO: confirme.

### Passo D — orchestrator mode

```
[1] Completo — invoca agentes em paralelo
[2] Inline — Claude principal faz tudo (recomendo começar)
```

**Escolha `2`** para começar. Troque depois de 3-5 sprints editando `.planning/config.json`.

### Passo E — `visual_tokens_mode`

```
tokens.json: final (todas categorias mínimas)

Confirmar [final] ou [provisional]?
```

Se preencheu tudo: `final`.

### Passo F — `/gsd:docs-index`

```
5 arquivos sem descrição detectados. Rodar /gsd:docs-index? [s/N]
```

Se preencheu INDEX.md na Fase 4.4: `N`.

Se não: `s`, Claude vai conversar descrevendo cada arquivo.

### Passo G — geração de `.planning/`

Claude gera:
1. `.planning/PROJECT.md`
2. `.planning/ROADMAP.md`
3. `.planning/STATE.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/MILESTONES.md`
6. `.planning/DECISIONS.md`
7. Atualiza `.planning/config.json`

## 6.5 Revisar o roadmap — CRÍTICO

**Abra `.planning/ROADMAP.md` agora.** Documento mais importante gerado.

Pode sair algo assim para o MercadoPRO:

```markdown
# Roadmap — MercadoPRO

## M0 — Setup infra e CI (Semana 1)
Docker, FastAPI, MySQL local, GitHub Actions CI.

## M1 — Foundation (Semanas 2-3)
Auth JWT, models base, endpoints CRUD admin sem UI.

## M2 — Cadastro público (Semanas 4-5)
UI cadastro comerciante + atacadista + admin aprova.

## M3 — Catálogo (Semanas 6-8)
Atacadista gerencia produtos; comerciante vê catálogo.

## M4 — Pedido (Semanas 9-11)
Criar pedido, validar mínimo, confirmar.

## M5a — Pagamento Pix (Semanas 12-13)
Integração Pagar.me Pix.

## M5b — Pagamento Boleto (Semanas 14-15)
Pagar.me boleto.

## M6 — Notificação e Deploy (Semanas 16-18)
FCM push + deploy VPS.
```

**Perguntas:**
1. Ordem faz sentido?
2. Duração realista para sua capacidade?
3. Faltou algum milestone crítico?
4. Algum está grande demais (> 3 semanas)?

**Ajustar se necessário:**

```
Revisei ROADMAP.md. Quero mudanças:
1. Trocar ordem de M2 e M3: catálogo vem antes do cadastro público 
   porque atacadista precisa de catálogo antes do comerciante se cadastrar
2. M6 tem deploy junto com push — quebrar em M6 (FCM) e M7 (Deploy)
3. Adicionar milestone M-LGPD entre M2 e M3: setup de consentimento e 
   termos de uso

Atualize ROADMAP.md refletindo essas mudanças e me mostre o diff.
```

## 6.6 Commit

```bash
git add .planning/ .claude/settings.json
git commit -m "chore: bootstrap — ROADMAP com N milestones"
```

---

# FASE 7 — Quebrar milestone em sprints (15-20 min)

## 7.1 Primeiro milestone

Abra `.planning/ROADMAP.md`, anote slug (ex: `M0-setup-infra`).

## 7.2 Quebrar em sprints

```
/gsd:plan-phase M0-setup-infra
```

## 7.3 O que acontece

Workflow:
1. Lê milestone do ROADMAP
2. Aplica strategy escolhida
3. Consulta `references/sprint-slicing.md`
4. Gera 3-5 `SPRINT-NN-<slug>.md` em `.planning/sprints/`
5. Valida cada: Visual Contract, skills, DoD
6. Lista consolidada

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► SPRINT PLAN — M0-setup-infra
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy: vertical_value
Sprints gerados: 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sprint 01 — docker-fastapi
Narrativa: "Dev consegue rodar docker-compose up e ter FastAPI + 
MySQL rodando localmente com endpoint /health respondendo 200."
DoD: curl http://localhost:8000/health → {"status":"ok","db":"connected"}
Skills: domain/docker-production-ready, domain/mysql-schema-design, 
quality/observability-production
Has UI: false
Validação: ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sprint 02 — auth-jwt
Narrativa: "Usuário consegue fazer signup e login via API, recebendo 
JWT para endpoints protegidos."
DoD: POST /auth/signup cria user; POST /auth/login retorna JWT; 
GET /me com Bearer token retorna user data
Skills: product/api-design-contracts, owasp-security, 
quality/observability-production, quality/error-ux-patterns
Has UI: false
Validação: ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sprint 03 — ci-cd
Narrativa: "Dev faz push em branch, GitHub Actions roda tests + lint + 
build, PR só mergeia com tudo verde."
DoD: .github/workflows/ci.yml funcional; 3 jobs verdes em PR de teste
Skills: domain/docker-production-ready, quality/observability-production
Has UI: false
Validação: ✓

Revisar antes de prosseguir? [s/N]
```

## 7.4 Revisar cada SPRINT.md

**Antes de responder N, abra cada sprint.**

Exemplo `.planning/sprints/SPRINT-01-docker-fastapi.md`:

```markdown
---
sprint_id: "01-docker-fastapi"
milestone: "M0-setup-infra"
has_ui: false
has_forms: false
has_auth_flow: false
has_mobile: false
locale: "pt-BR"
estimated_hours: 8
---

# Sprint 01 — docker-fastapi

## Narrativa
Dev consegue rodar `docker-compose up` e ter FastAPI + MySQL rodando 
localmente com endpoint `/health` respondendo 200.

## Definition of Done
- [ ] `docker-compose.yml` sobe api, mysql, redis
- [ ] `curl http://localhost:8000/health` retorna `{"status":"ok","db":"connected"}`
- [ ] `docker-compose down -v` limpa tudo
- [ ] README.md tem seção "Quick Start" testada
- [ ] `.env.example` documentado com todas as vars

## Tasks (planner detalha em /gsd:plan-phase)
- Dockerfile multi-stage
- docker-compose.yml
- Endpoint /health com db ping
- Conexão SQLAlchemy
- README atualizado

## Skills Consultadas
- domain/docker-production-ready
- domain/mysql-schema-design
- quality/observability-production

## Visual Contract
N/A — sem UI

## Riscos
- Porta 3306 conflito com MySQL local
- MySQL 8 startup lento pode causar flaky no primeiro start
```

**Revise cada sprint:**

- Narrativa clara, em linguagem humana?
- DoD testável manualmente em ≤ 30 min?
- Skills citadas batem com escopo?
- Se `has_ui: true`, tem Visual Contract com tokens de `tokens.json`?

**Se errado, edite ou peça ajuste:**

```
No SPRINT-02-auth-jwt.md:
1. Adicione na DoD: "logs em JSON estruturado, não texto"
2. Remova "MFA" das skills — fora de escopo MVP
3. Reduza estimate de 10h para 6h
```

## 7.5 Commit

```bash
git add .planning/sprints/
git commit -m "chore: sprints planejados para M0-setup-infra"
```

---

# FASE 8 — Executar primeiro sprint (30 min a 3h)

Trabalho real. É aqui que disciplina paga.

## 8.1 Planejar fase

```
/gsd:plan-phase sprint-01-docker-fastapi
```

## 8.2 O que acontece

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PLAN PHASE — sprint-01-docker-fastapi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gate 1 (bootstrap): ✓
Gate 2 (visual_contract): N/A — has_ui=false
Gate 4 (security_baseline): ✓

Invocando gsd-phase-researcher...
  Consultando docker-production-ready...
  Consultando mysql-schema-design...
  Consultando observability-production...

Gerando PLAN.md...

Gate 3 (skills_coverage): 
  ✓ domain/docker-production-ready citada
  ✓ domain/mysql-schema-design citada
  ✓ quality/observability-production citada
  Resultado: CLEAR

Prosseguir com /gsd:execute-phase? [s/N]
```

## 8.3 **ANTES DE EXECUTAR — FORÇAR LEITURA DE SKILLS**

**Passo mais importante do tutorial inteiro.** Plan-checker valida que skill foi CITADA. Não valida que foi LIDA e APLICADA. Você força isso.

**Copie e cole exatamente:**

```
PARE antes de executar. Antes do /gsd:execute-phase, faça em ordem:

1. Abra .claude/skills/domain/docker-production-ready/SKILL.md 
   (arquivo inteiro, não só primeiras linhas). Me liste:
   - As 3 regras mais relevantes para este sprint específico
   - Quais delas você vai aplicar no código
   - Alguma que você vai conscientemente NÃO aplicar e por quê
   - Cole uma linha literal de cada regra que provou que leu

2. Abra .claude/skills/domain/mysql-schema-design/SKILL.md 
   e faça o mesmo.

3. Abra .claude/skills/quality/observability-production/SKILL.md 
   e faça o mesmo.

NÃO COMECE A CODAR até ter feito os 3 passos e eu confirmar.
```

**O que esperar:**

```
Lendo .claude/skills/domain/docker-production-ready/SKILL.md...

3 regras mais relevantes para este sprint:

1. Multi-stage build — separar stage de build do stage de runtime 
   para imagem final menor (< 200MB ideal).
   Linha literal: "Dockerfile must use multi-stage build: FROM python:3.11 
   AS builder / ... / FROM python:3.11-slim AS runtime"
   → VOU APLICAR: Dockerfile com 2 stages nomeadas builder e runtime

2. Non-root user — nunca rodar container como root em produção.
   Linha literal: "USER directive mandatory before CMD; create user 
   with UID >= 1000"
   → VOU APLICAR: useradd -m -u 1000 app; USER app antes de CMD

3. Health check integrado — HEALTHCHECK no Dockerfile E no 
   docker-compose.yml.
   Linha literal: "HEALTHCHECK --interval=30s --timeout=10s CMD 
   curl -f http://localhost:8000/health || exit 1"
   → VOU APLICAR: healthcheck em ambos, com endpoint /health que 
   pinga DB

Uma regra que NÃO vou aplicar conscientemente: "Secrets via Docker 
Secrets ou Vault"
→ Motivo: MVP usa .env file. Documento em PLAN.md como dívida 
técnica a resolver antes de produção (sprint futuro de pre-prod).

---

Lendo .claude/skills/domain/mysql-schema-design/SKILL.md...
[... continua ...]

---

3 skills lidas e analisadas. Aguardo sua confirmação para iniciar 
execução.
```

**Se Claude pular ou resumir genericamente:**

```
Você não colou linha literal das regras. Refaça passo 1, copiando 
texto EXATO da SKILL.md entre aspas. Se não está conseguindo abrir 
o arquivo, me avise o erro — não invente.
```

**Essa fricção é o framework trabalhando.** Nos primeiros 3 sprints, insista sempre. Depois vira hábito automático.

## 8.4 Revisar PLAN.md

Abra `.planning/sprints/sprint-01-docker-fastapi/PLAN.md`.

Estrutura típica:

```markdown
# PLAN — Sprint 01 docker-fastapi

## Tasks (ordem topológica)

### T01 — Dockerfile
- Output: backend/Dockerfile (multi-stage, non-root)
- Skills aplicadas: docker-production-ready (regras 1, 2)
- Testes: docker build sem erro; imagem final < 200MB
- Estimativa: 30 min

### T02 — docker-compose.yml
- Input: T01
- Output: docker-compose.yml (api, mysql, redis)
- Skills aplicadas: docker-production-ready (regra 3 healthcheck)
- Testes: docker-compose up sobe 3 serviços em < 60s
- Estimativa: 45 min

### T03 — Conexão SQLAlchemy
- Input: T02
- Output: backend/app/core/database.py
- Skills aplicadas: mysql-schema-design (pool, async)
- Testes: pytest fixture conecta e roda query
- Estimativa: 1h

### T04 — Endpoint /health
- Input: T03
- Output: backend/app/api/health.py + router
- Skills aplicadas: observability-production (endpoint /health)
- Testes: GET /health retorna 200 com db ping ok
- Estimativa: 30 min

### T05 — README Quick Start
- Input: tudo anterior
- Output: README.md atualizado
- Testes: dev novo consegue rodar seguindo README
- Estimativa: 20 min

## Dependências
- Python 3.11, Docker 24+, MySQL 8

## Riscos mitigados
- Porta 3306 conflito: docker-compose publica em 3307

## Dívida técnica registrada
- Secrets via .env (não Vault) — resolver pré-prod
- Logs texto stdout — estruturar JSON no sprint 02
```

Se OK, prossegue. Se não, ajuste:

```
No PLAN.md, T03 estima 1h mas conexão async SQLAlchemy com MySQL 
tem pegadinhas (driver aiomysql vs asyncmy). Aumenta para 1h30 
e adiciona subtask de escolher driver.
```

## 8.5 Executar

```
/gsd:execute-phase sprint-01-docker-fastapi
```

## 8.6 Durante execução

Claude vai implementar T01 a T05 em ordem. Observe:

**Statusline** mostra progresso:
```
Opus 4.7 | M0-setup-infra · Sprint 01 · T03/5 | 68% used
```

**Context monitor** avisa:
```
[WARNING] Contexto em 30%. Considere finalizar sprint ou salvar estado.
```

Se virar `CRITICAL`, salve:

```
PARE. Salve o estado atual em .planning/STATE.md incluindo:
- Task exata em que paramos (ex: T04 linha 23)
- O que já foi commitado
- Próximo passo necessário
Vou iniciar sessão nova.
```

**Gate 5 (integration check)** roda durante execução, pegando divergências cedo.

**Gate 6 (reconcile)** ao final, compara PLAN vs código:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GATE 6 — RECONCILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Divergências:

1. [ALTA] PLAN.md T03 diz pool_size=20
   → Código em core/database.py usa pool_size=5
   → Ação: alinhar PLAN ou código

2. [BAIXA] PLAN.md T04 diz "logs estruturados JSON"
   → Código usa logging padrão (texto)
   → Ação: dívida técnica ou corrigir

Resolução? [s/N]
```

Responda cada uma:

```
1. Código está certo (pool_size=5 é adequado para MVP). Atualize PLAN.md.
2. Aceitar como dívida técnica. Adicionar em .planning/TECH_DEBT.md 
   com prioridade média, assunto "Logs estruturados JSON em toda API 
   — sprint dedicado".
```

## 8.7 Sprint concluído

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SPRINT 01 — CONCLUÍDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gates passados: 7/7
Tasks concluídas: 5/5
Tempo real: 1h47min (estimativa: 8h)
Divergências reconciliadas: 2

Testes:
  ✓ 12 testes passaram
  ✓ coverage: 84%
  ✓ lint: clean

Arquivos criados:
  backend/Dockerfile
  backend/docker-compose.yml
  backend/app/core/database.py
  backend/app/api/health.py
  backend/tests/test_health.py
  README.md (atualizado)
  .env.example

Próximo: bin/collect-metrics.sh sprint-01-docker-fastapi
```

## 8.8 Validar manualmente DoD

**Antes de `bin/collect-metrics.sh`, valide você mesmo:**

```bash
cd backend
cp .env.example .env
docker-compose up -d
sleep 10
curl http://localhost:8000/health
# Esperado: {"status":"ok","db":"connected"}

# Se deu certo:
docker-compose down -v
cd ..
```

Se não funcionou, volte e corrija antes de fechar.

Commit:

```bash
git add .
git commit -m "feat(sprint-01): setup docker + fastapi + mysql + health check"
```

---

# FASE 9 — Fechar sprint e métricas (15 min)

## 9.1 Rodar métricas

```
bin/collect-metrics.sh sprint-01-docker-fastapi
```

## 9.2 O que acontece

Workflow:
1. Verifica todos gates passaram (7/7)
2. Gera `.planning/retros/sprint-01-docker-fastapi.md`
3. Pausa para você preencher qualitativo
4. Roda `bin/collect-metrics.sh`
5. Anexa em `.planning/METRICS.md`

## 9.3 Preencher retrospectiva HONESTAMENTE

Arquivo gerado:

```markdown
---
sprint: sprint-01-docker-fastapi
date: 2026-04-23
duration_actual_hours: 1.75
estimated_hours: 8
---

# Retrospectiva — Sprint 01

## Dados automáticos
- Gates bypassados: 0
- Plan revisions: 1
- Fix iterations: 0
- Tests: 12 passed, 84% coverage
- Reconcile divergences: 2 (resolvidos)

## Preencha (QUALITATIVO — SEJA HONESTO)

### 1. O que funcionou bem? (2-3 linhas)


### 2. O que atrapalhou? (2-3 linhas)


### 3. O que faltou? (skill, contexto, ferramenta)


### 4. Claude entendeu o que eu queria? (1-5)
1 = não entendeu nada | 5 = entendeu perfeitamente
Score: 
Justifique:

### 5. Qualidade do código? (1-5)
1 = lixo | 5 = excelente
Score:
Justifique:

## Observações livres
```

**Exemplo preenchido (honestamente):**

```markdown
### 1. O que funcionou bem?
Plan phase leu skills direito — Dockerfile ficou com multi-stage e 
non-root user bem aplicados. docker-compose subiu sem fricção.
Health check funcionou de primeira.

### 2. O que atrapalhou?
Reconcile detectou divergência pool_size só depois do código pronto. 
Se tivesse detectado durante execução teria evitado atualizar 
PLAN.md depois. Gate 6 deveria ser gate 5.5 idealmente.

### 3. O que faltou?
Skill específica "mysql 8 async com SQLAlchemy" — precisei abrir 
docs externas para resolver driver (escolhi aiomysql). Seria bom 
ter como reference.

### 4. Claude entendeu? Score: 4
Entendeu o sprint. Só pool_size em T03 saiu do esperado, mas não 
foi drama.

### 5. Qualidade do código? Score: 5
Limpo, testável, seguindo patterns. Merge direto.

## Observações livres
Primeiro sprint rodou em 1h47min vs 8h estimado. Estimativa estava 
muito inflada OU setup de fato é rápido em projeto novo. Próximos 
sprints vão calibrar.
```

## 9.4 Resultado

Claude anexa em `.planning/METRICS.md`:

```markdown
# METRICS — MercadoPRO

| Sprint | Dur (h) | Plan Rev | Fix Iter | Gates Bypass | Score Comp | Score Code | Notes |
|--------|---------|----------|----------|--------------|------------|------------|-------|
| 01-docker-fastapi | 1.75 | 1 | 0 | 0 | 4 | 5 | Reconcile tardio em pool_size |
```

Commit:

```bash
git add .planning/retros/ .planning/METRICS.md
git commit -m "chore(sprint-01): retrospectiva e métricas"
```

---

# FASE 10 — Ciclo contínuo

## 10.1 Sprint seguinte

```
/gsd:plan-phase sprint-02-auth-jwt
```

**Sempre prompt forçando leitura de skills:**

```
PARE antes de executar sprint-02-auth-jwt. Leia as 4 skills 
obrigatórias em ordem:
1. .claude/skills/product/api-design-contracts/SKILL.md
2. .claude/skills/owasp-security/SKILL.md
3. .claude/skills/quality/observability-production/SKILL.md
4. .claude/skills/quality/error-ux-patterns/SKILL.md

Para cada uma, me liste 3 regras principais que vai aplicar, 
colando linha literal de cada para provar leitura. NÃO comece 
a codar até eu confirmar.
```

Depois:

```
/gsd:execute-phase sprint-02-auth-jwt
```

```
bin/collect-metrics.sh sprint-02-auth-jwt
```

## 10.2 Fim de milestone

Quando M0 acaba (todos sprints fechados):

```
/gsd:milestone-summary M0-setup-infra
```

Gera `.planning/milestones/M0-setup-infra/SUMMARY.md` consolidando.

Próximo milestone:

```
/gsd:plan-phase M1-foundation
```

## 10.3 Rituais semanais (30 min/semana, toda sexta ou a cada 3 sprints)

### Atualizar INDEX se adicionou docs
```
/gsd:docs-index
```

### Converter novos binários
```bash
bash bin/convert-docs.sh
```

### Revisar métricas
```bash
cat .planning/METRICS.md
```

**Sinais de saúde (ao longo de 3-5 sprints):**
- Fix Iter caindo sprint a sprint ✓
- Plan Rev estabilizando em 1-2 ✓
- Gates Bypass raro com motivo real ✓
- Scores ≥ 3.5 consistentes ✓

**Sinais de atenção:**
- Plan Rev > 3 repetido → planner não entende projeto
- Fix Iter > 2 → skills citadas não aplicadas
- Gates Bypass frequente → framework atrapalhando
- Score < 3 → volta ao project-brief, ambiguidade

---

# FASE 11 — Telemetria e iteração

## 11.1 Exportar

A cada 3-5 sprints:

```bash
bash bin/export-telemetry.sh
```

```
Export: telemetry-export-20260505.json (4.2 KB)
- Framework v0.4.0
- Projeto: anonimizado como "project-A"
- 4 sprints consolidados
- Métricas + retros
- Sem dados pessoais
```

## 11.2 Próxima iteração

Em próxima conversa comigo ou próxima versão Claude:

```
Tenho telemetria de 5 sprints rodando gsd-framework v0.9.4 em 
projeto real. Quero iterar para v0.5 baseado no que quebrou.

Anexei telemetry-export.json. Analise e sugira:
1. Quais skills se provaram úteis vs. inúteis
2. Quais gates são retrabalho constante
3. Onde fricção é maior que valor
4. Sugestão concreta de mudanças para v0.5
```

**Esse loop é o único caminho real para o framework melhorar.** Sem dados seus, iteração é especulação.

---

# APÊNDICE A — Prompts de emergência (copie quando precisar)

## Claude ignorou instrução

```
Você ignorou [X]. Releia minha mensagem anterior linha por linha. 
Me confirme explicitamente cada uma das 3 coisas que pedi antes de 
fazer qualquer outra coisa.
```

## Claude está alucinando

```
Pare. Você está inventando informação. Reabra docs/project-brief.md 
e specs/stack.yaml e cole aqui a seção relevante ANTES de continuar. 
Não pode inferir o que não está escrito.
```

## Sprint saiu de escopo

```
Este sprint saiu do escopo. A narrativa era: "[cole]".
Reverta mudanças fora do escopo. Se acha que precisa escopo maior, 
pare e me fale antes de continuar.
```

## Forçar leitura real de skill

```
Você disse que leu [skill X] mas seu output não demonstra aplicação 
dela. Cole aqui as 3 primeiras regras LITERAIS da SKILL.md dessa 
skill. Texto exato entre aspas, não paráfrase.
```

## Auditoria honesta antes de fechar sprint

```
Antes de fechar este sprint, faça auditoria honesta:
1. Qual skill você citou mas NÃO aplicou de fato?
2. Qual parte do código tem "TODO" ou "FIXME" que vira dívida?
3. Qual teste você pulou ou simplificou?
Seja autocrítico. Quero saber o que NÃO está pronto, não o que está.
```

## Desfazer última ação

```
Desfaça a última mudança. Reverta para o estado anterior ao meu 
último prompt. Use git se precisar.
```

## Salvar estado e parar

```
Salve estado atual em .planning/STATE.md:
- Milestone/sprint atual
- Task exata em que paramos (com linha se possível)
- O que já foi commitado
- Próximo passo necessário

Depois pare. Vou iniciar sessão nova.
```

## Resumir onde estou

```
Resuma em 3 linhas: em que milestone, em que sprint, em que task 
estou agora. Baseie-se em .planning/STATE.md e último git log.
```

## Verificar que não há contaminação de projeto anterior

```
Antes de prosseguir, rode:
grep -rn -iE "nome-do-projeto-antigo|contaminacao-conhecida" \
  docs/ specs/ .planning/ backend/ app-mobile/ 2>/dev/null

Se retornar match, pare e me mostre antes de continuar. Se vazio, 
ok para prosseguir.
```

---

# APÊNDICE B — Modo Web (Claude.ai sem Claude Code)

Framework ainda funciona sem Claude Code, só sem automação de slash commands.

## B.1 Setup

Claude.ai → criar Projeto → upar framework zipado. Nas instruções do projeto:

```
Estou usando o gsd-framework v0.9.4. 
Leia CLAUDE.md e FRAMEWORK-STATUS.md antes de qualquer interação. 
Quando eu pedir um workflow, abra o arquivo em 
.claude/get-shit-done/workflows/<nome>.md e execute o fluxo 
descrito ali.
```

## B.2 Substitutos

| Slash command | Equivalente web |
|---------------|-----------------|
| `/gsd:bootstrap` | "Execute `.claude/get-shit-done/workflows/bootstrap.md`" |
| `/gsd:plan-phase M1-x` | "Execute `workflows/gsd:plan-phase.md` para M1-x" |
| `/gsd:plan-phase sprint-01-x` | "Execute `workflows/plan-phase.md` para sprint-01-x" |
| `/gsd:execute-phase sprint-01-x` | "Execute `workflows/execute-phase.md` para sprint-01-x" |
| `bin/collect-metrics.sh sprint-01-x` | "Execute `workflowsbin/collect-metrics.sh.md` para sprint-01-x" |
| `/gsd:docs-index` | "Execute `workflows/gsd:docs-index.md`" |

## B.3 Hooks não rodam

Você perde:
- Statusline dinâmico → compensar: `cat .planning/STATE.md` periodicamente
- Context monitor → você observa "context X% used" e decide parar
- Workflow guard → seguir ordem rigorosamente

Funcional, só mais manual.

---

# APÊNDICE C — Troubleshooting

## "Bootstrap falhou: arquivo ausente"

```bash
test -f docs/project-brief.md && echo "OK" || echo "FALTA BRIEF"
test -f specs/project.yaml && echo "OK" || echo "FALTA PROJECT"
test -f specs/stack.yaml && echo "OK" || echo "FALTA STACK"
test -f specs/rules.yaml && echo "OK" || echo "FALTA RULES"
```

Preencha os faltando.

## "Sprint bloqueia em visual_tokens_mode"

A) Complete tokens.json (correto)

B) Marque provisional (prazo até sprint 3):
```bash
python3 -c "
import json
c = json.load(open('.planning/config.json'))
c['visual_tokens_mode'] = 'provisional'
json.dump(c, open('.planning/config.json','w'), indent=2)
"
```

## "Plan-checker bloqueia skill que não faz sentido"

Ajuste flags no SPRINT.md:
```yaml
---
has_ui: false     # era true mas sprint é backend-only
has_forms: false
---
```

Ou edite matriz em `.claude/skills/SKILLS_INDEX.md > sprint_ui_matrix`.

## "gsd-tools.cjs: command not found"

```bash
which node
node --version
```

Se < 18: `nvm install 20 && nvm use 20`.

## "Hook dispara CRITICAL muito cedo"

Edite `.claude/hooks/gsd:context-monitor.js`:
```javascript
const WARNING_THRESHOLD = 50;   // era 35
const CRITICAL_THRESHOLD = 35;  // era 25
```

## "Reconcile sempre reporta divergências triviais"

Adicione em `.planning/config.json`:
```json
"reconcile": {
  "ignore_patterns": ["# TODO:", "# NOTE:", "// FIXME:"]
}
```

## "Sprint demorou 10x estimativa"

Duas causas:
1. Estimativa otimista — calibre pelas retros reais
2. Sprint grande demais — `/gsd:insert-phase` para quebrar

## "Quero pular um gate"

```
/gsd:execute-phase sprint-01-x --skip-gate 4 --reason "security review 
feita externamente no PR #123"
```

Bypass registrado em `.planning/METRICS.md`. Use parcimoniosamente.

## "Perdi o fio da meada"

```bash
cat .planning/STATE.md
```

Ou:
```
Resuma em 3 linhas: em que milestone, em que sprint, em que task 
estou. Base: .planning/STATE.md + último git log.
```

## "Desfazer tudo e recomeçar"

```bash
git log --oneline | head -20            # identifica ponto de retorno
git reset --hard <hash-do-commit>
rm -rf .planning/sprints/
# Re-rodar /gsd:plan-phase
```

## "Claude não está lendo skills mesmo insistindo"

1. Confirme arquivo existe: `ls .claude/skills/<categoria>/<nome>/SKILL.md`
2. Verifique tamanho: `wc -l .claude/skills/<categoria>/<nome>/SKILL.md` (> 50 linhas)
3. Peça para listar arquivo no diretório primeiro antes de abrir:
   ```
   Primeiro liste arquivos em .claude/skills/. Depois em 
   .claude/skills/quality/. Confirma que accessibility-pro está lá.
   AGORA abre o SKILL.md.
   ```

## "Quero trocar strategy de slicing no meio do projeto"

```
Quero trocar slicing strategy de vertical_value para admin_first a 
partir do próximo milestone. Atualize .planning/config.json e 
documente em .planning/DECISIONS.md com justificativa.
```

---

# CHECKLIST FINAL (imprima e use)

## Antes de começar
- [ ] Node 18+, Python 3.10+, Git
- [ ] Pandoc opcional (apenas se tem .docx/.pptx)
- [ ] Claude Code instalado OU decidido modo web
- [ ] Editor aberto

## Fase 1 (5-10 min)
- [ ] `unzip` + `mv` + `cd`
- [ ] `git init` + commit baseline
- [ ] `bash tests/framework/run-all.sh` → 5/5
- [ ] `chmod +x` em bin e hooks
- [ ] `node gsd-tools.cjs --help` funciona

## Fase 2 (60-90 min)
- [ ] `docs/project-brief.md` — 12 seções preenchidas
- [ ] `specs/project.yaml` preenchido
- [ ] `specs/stack.yaml` preenchido concretamente
- [ ] `specs/database.yaml` preenchido (se tem DB)
- [ ] `specs/rules.yaml` com ≥ 3 regras
- [ ] Commit

## Fase 3 (30-60 min, se tem UI)
- [ ] `tokens.json` com color + space mínimo
- [ ] `brand.md` com voz, tom, vocabulário
- [ ] Commit

## Fase 4 (20-30 min, se tem arquivos extras)
- [ ] `docs/business/`, `docs/research/` criadas
- [ ] Arquivos copiados
- [ ] Wireframes em `docs/identidade-visual/wireframes/`
- [ ] `bash bin/convert-docs.sh` rodado
- [ ] INDEX.md em cada subpasta
- [ ] Commit

## Fase 5 (10 min)
- [ ] `.claude/settings.json` com bloco hooks
- [ ] Teste de hook sem erro
- [ ] Commit

## Fase 6 (15-20 min)
- [ ] Primeiro prompt de validação (força leitura CLAUDE.md e FRAMEWORK-STATUS)
- [ ] `/gsd:bootstrap`
- [ ] Síntese revisada/ajustada
- [ ] Strategy escolhida
- [ ] Orchestrator mode (recomendo inline)
- [ ] `visual_tokens_mode` definido
- [ ] `ROADMAP.md` revisado e ajustado
- [ ] Commit

## Fase 7 (15-20 min)
- [ ] `/gsd:plan-phase M0-<slug>` ou `M1-<slug>`
- [ ] Cada SPRINT.md revisado
- [ ] Ajustes aplicados
- [ ] Commit

## Fase 8 (30 min a 3h)
- [ ] `/gsd:plan-phase sprint-01-<slug>`
- [ ] **PROMPT DE FORÇAR LEITURA DE SKILLS ENVIADO**
- [ ] Claude colou linha literal de cada regra
- [ ] PLAN.md revisado
- [ ] `/gsd:execute-phase sprint-01-<slug>`
- [ ] Divergências de reconcile resolvidas
- [ ] Teste manual da DoD rodou
- [ ] Commit

## Fase 9 (15 min)
- [ ] `bin/collect-metrics.sh sprint-01-<slug>`
- [ ] Retrospectiva preenchida HONESTAMENTE
- [ ] Scores dados (sem self-deception)
- [ ] Commit

## A cada 3-5 sprints
- [ ] `bash bin/export-telemetry.sh`
- [ ] Revisão de `METRICS.md`
- [ ] Identificar tendências de problema
- [ ] Guardar export para próxima conversa

---

# Resumo filosófico

O framework cobra fricção no começo (preencher docs, forçar leitura de skills, validar DoDs, preencher retros) porque é essa fricção que separa projeto disciplinado de projeto vibe-coded.

- Quem pula **fase 2-3** (docs + identidade visual) vai sofrer nos sprints com ambiguidade
- Quem pula **fase 8.3** (forçar leitura de skills) vai ter skills citadas mas não aplicadas
- Quem pula **fase 9** (retro honesta) perde o sinal que faz v0.5 existir com dados reais

**O framework não te faz ir mais rápido no sprint 1.** Te faz ir mais rápido no sprint 5 porque o contexto acumulou e as armadilhas foram mapeadas.

Se você odiar o framework nos 3 primeiros sprints, provavelmente está funcionando. Se odiar no sprint 8, aí sim tem problema — me avise com telemetria.
