<purpose>
Inicializa o planning de um projeto.

**3 caminhos** (escolhidos automaticamente em ordem):

1. **`projeto/` existe e tem conteúdo** (caminho preferido v0.9.1+):
   Bootstrap redireciona para `/gsd:ingest` — lê tudo em `projeto/` e gera `.planning/` automaticamente.

2. **`docs/project-brief.md`, `specs/project.yaml`, `specs/stack.yaml` existem** (caminho clássico):
   Bootstrap lê esses arquivos e gera `.planning/` (comportamento original v0.8.x).

3. **Nenhum dos dois existe**:
   Bootstrap orienta operador a escolher: (a) criar `projeto/` e jogar arquivos lá, ou (b) preencher manualmente os specs canônicos.

Este é o PRIMEIRO comando a ser executado em qualquer projeto novo que usa este framework.
Lê documentação do projeto (não inventa) e produz o .planning/ inicial.
</purpose>

<routing_decision>

```bash
# Detecção de caminho — primeira coisa após validar pré-requisitos

PROJETO_HAS_CONTENT="false"
if [ -d "projeto/" ]; then
  # Tem ao menos 1 arquivo (excluindo READMEs) em alguma subpasta?
  FILES_FOUND=$(find projeto/ -type f ! -name "README.md" 2>/dev/null | head -1)
  if [ -n "$FILES_FOUND" ]; then
    PROJETO_HAS_CONTENT="true"
  fi
fi

LEGACY_SPECS_EXIST="false"
if [ -f "docs/project-brief.md" ] && [ -f "specs/project.yaml" ] && [ -f "specs/stack.yaml" ]; then
  LEGACY_SPECS_EXIST="true"
fi

if [ "$PROJETO_HAS_CONTENT" = "true" ]; then
  cat << ROUTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ DETECTADO: pasta projeto/ com conteúdo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bootstrap v0.9.1+ usa /gsd:ingest como caminho preferido.

Redirecionando para /gsd:ingest...

ROUTING
  # Invocar /gsd:ingest passando todos os argumentos do bootstrap original
  # O ingest faz o trabalho e gera .planning/ + INGESTOR-HANDOFF.json
  # Bootstrap termina aqui com sucesso.
  exec_command "/gsd:ingest $ORIGINAL_ARGS"
  exit 0

elif [ "$LEGACY_SPECS_EXIST" = "true" ]; then
  echo "Detectado: specs canônicos em docs/ e specs/. Usando fluxo clássico."
  # Segue para o process tradicional abaixo

else
  cat << GUIDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠  PROJETO NÃO INICIALIZADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bootstrap precisa de input de uma das 2 formas:

OPÇÃO A (recomendada — automática):
  1. Crie a pasta projeto/ (ou já existe vazia)
  2. Jogue os arquivos do seu projeto em qualquer formato:
     - Regras de negócio em projeto/regras-negocio/
     - Wireframes (HTML, PNG, PDF) em projeto/wireframes/
     - Identidade visual em projeto/identidade-visual/
     - Stack escolhida em projeto/stacks/
     - Docs externos em projeto/docs-externos/
  3. Rode /gsd:bootstrap novamente

OPÇÃO B (clássica — manual):
  1. Crie docs/project-brief.md
  2. Crie specs/project.yaml
  3. Crie specs/stack.yaml
  4. Rode /gsd:bootstrap novamente

Veja exemplos em projeto/README.md ou docs/PLATFORM-NOTES.md.
GUIDE
  exit 1
fi
```

</routing_decision>

<required_reading>
@$CLAUDE_PROJECT_DIR/CLAUDE.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/gates-v3.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/skills-enforcement.md
</required_reading>

<when_to_run>
- Projeto novo, sem `.planning/PROJECT.md` ou `.planning/STATE.md`
- Re-bootstrap após mudança maior de escopo (novo ROADMAP a partir de novos documentos)
- **NUNCA** rode se `.planning/STATE.md` já tem progresso gravado sem antes consultar o humano
</when_to_run>

<hard_block>
Se `.planning/STATE.md` existe E contém linhas de histórico além do template inicial:
  Exibir:
  ```
  ⚠️  STATE.md já contém progresso.
  Re-bootstrap sobrescreve PROJECT.md e pode conflitar com ROADMAP em andamento.
  Para re-bootstrap forçado, rode: /gsd-bootstrap --force
  ```
  Abortar.
</hard_block>

<process>

## 1. Validar fontes de verdade

Verificar existência obrigatória:

```bash
REQUIRED_FILES=(
  "docs/project-brief.md"
  "specs/project.yaml"
  "specs/stack.yaml"
)

MISSING=()
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    MISSING+=("$f")
  fi
done
```

**Se qualquer arquivo obrigatório faltar:**

Exibir mensagem detalhada com templates para preenchimento:

```
❌ Bootstrap bloqueado: documentação de projeto incompleta.

Arquivos obrigatórios que faltam:
{lista de MISSING}

Templates disponíveis em:
  .claude/get-shit-done/templates/docs/project-brief.md
  .claude/get-shit-done/templates/specs/project.yaml
  .claude/get-shit-done/templates/specs/stack.yaml

Preencha os arquivos e rode /gsd-bootstrap novamente.
Este framework exige esses documentos porque NÃO inventa contexto de projeto.
```

Abortar.

Arquivos opcionais (bootstrap aproveita se existirem):
- `specs/database.yaml` — convenções de banco
- `specs/rules.yaml` — regras de negócio invariantes
- `docs/adrs/ADR-*.md` — decisões arquiteturais
- `docs/identidade-visual/design-system.md` — design system
- `docs/identidade-visual/tokens.json` — tokens de design
- `docs/identidade-visual/brand.md` — tom de voz, personalidade

## 2. Ler e parsear todos os documentos

```bash
# Ler project-brief (markdown)
BRIEF=$(cat docs/project-brief.md)

# Parsear YAMLs (usar Python inline, sem dependência externa)
PROJECT_YAML=$(python3 -c "
import yaml, json
with open('specs/project.yaml') as f: data = yaml.safe_load(f)
print(json.dumps(data))
")
STACK_YAML=$(python3 -c "
import yaml, json
with open('specs/stack.yaml') as f: data = yaml.safe_load(f)
print(json.dumps(data))
")

# Listar ADRs existentes
ADRS=$(ls docs/adrs/ADR-*.md 2>/dev/null | sort)
ADR_COUNT=$(echo "$ADRS" | grep -c . || echo 0)

# Detectar design system
HAS_DESIGN_SYSTEM=false
[ -f "docs/identidade-visual/design-system.md" ] && HAS_DESIGN_SYSTEM=true
HAS_TOKENS=false
[ -f "docs/identidade-visual/tokens.json" ] && HAS_TOKENS=true
```

## 3. Apresentar síntese ao humano e confirmar

Antes de gerar qualquer arquivo, exibir síntese do que foi lido:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP — síntese do projeto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Projeto: {project.name}
Dono: {project.owner}
Locale: {project.locale}
Domínio prod: {project.domain_prod}

Proposta de valor:
  {project.description}

Stack:
  Backend: {stack.backend.language} + {stack.backend.framework}
  Frontend: {stack.frontend.framework}
  Mobile: {stack.mobile.framework if any else "não se aplica"}
  DB: {stack.database.prod}

Documentos de projeto detectados:
  ✓ docs/project-brief.md
  ✓ specs/project.yaml
  ✓ specs/stack.yaml
  {✓|✗} specs/database.yaml
  {✓|✗} specs/rules.yaml
  {N ADRs em docs/adrs/}
  {✓|✗} docs/identidade-visual/design-system.md
  {✓|✗} docs/identidade-visual/tokens.json

Gaps identificados:
  {lista de arquivos opcionais faltantes — bootstrap funciona, mas certas
   skills/gates ficam inativos sem eles. Ex: sem identidade-visual, o ui-phase
   pede design durante cada fase UI em vez de herdar do sistema.}

Prossigo com o bootstrap? [s/N]
```

Se humano confirmar, seguir. Caso contrário, abortar sem gerar arquivos.

## 3.5. Escolher estratégia de slicing

Antes de gerar o ROADMAP e qualquer sprint, o humano decide como os milestones serão quebrados em unidades testáveis. Esta decisão vai para `.planning/config.json > slicing_strategy` e vale para todo o projeto (pode ser mudada depois, mas não é barato).

Perguntar ao humano:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP — estratégia de slicing em sprints
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ao final de cada sprint você vai querer demonstrar algo testável em 30 min.
Existem duas ordens padrão para isso, e a escolha depende de QUEM é o usuário
principal do produto.

[A] Vertical Value Slicing  (recomendado para produtos com usuário externo)
    Cada sprint atravessa todas as camadas (UI + API + regra) e entrega um
    caminho do usuário EXTERNO ponta-a-ponta. Admin cresce puxado pela demanda
    operacional, não antes.
    
    Exemplo: sprint 1 — usuário cadastra e cria recurso com 1 regra de dono.
             sprint 2 — usuário muda estado do recurso com histórico.
             sprint 3 — usuário faz pagamento (mock).
             sprint 4+ — expande fluxo. Admin aparece quando operação precisa.

[B] Admin-First Slicing  (recomendado para backoffice/ERP interno)
    Cadastros de admin primeiro, depois CRUDs de negócio, depois regras
    críticas e relatórios. Aqui o admin É o produto — operador é o usuário
    principal.
    
    Exemplo: sprint 1 — CRUD usuários/permissões.
             sprint 2 — CRUD tenants/config.
             sprint 3 — CRUD produtos. ... sprint 8+ — transições de estado,
             relatórios com joins, filtros avançados.

Sugestão automática baseada em docs/project-brief.md:
  {analisar project-brief e sugerir com base em quem é o "usuário alvo" declarado:
   - "consumidor", "cliente final", "prestador", "paciente", "aluno" → [A]
   - "operador", "atendente", "admin", "financeiro", "gerente" → [B]
   - ambíguo → [A] como default}

Sua escolha [A/B]: 
```

Após resposta:

- Grava em `.planning/config.json > slicing_strategy`: `"vertical_value"` ou `"admin_first"`
- Se escolha diverge da sugestão automática, registra em `.planning/DECISIONS.md`:
  > "D-001 — Estratégia de slicing: {escolha}. Justificativa do humano: {se fornecida, senão 'override manual da sugestão automática'}. Referência: `.claude/get-shit-done/references/sprint-slicing.md`."

**Validação adicional:** se escolha é `vertical_value`, verificar que `docs/identidade-visual/tokens.json` tem categorias mínimas (`color` + `space`). Se não, avisar que sprints com UI serão bloqueados:

```
⚠ docs/identidade-visual/tokens.json incompleto.
  Sprints com UI serão bloqueados até você preencher pelo menos `color` + `space`.
  
  Opções:
    1) Preencher agora (ver docs/identidade-visual/tokens.json — template já está lá)
    2) Continuar assim — primeiro sprint com UI vai bloquear no plan-checker
    3) Marcar como provisional (config.json > visual_tokens_mode: "provisional")
       → checker avisa mas não bloqueia; revisão forçada antes do Sprint 3

Opção [1/2/3]:
```

Gravar `visual_tokens_mode` em config.json conforme escolha.

## 3.6. Detectar agentes orchestrator disponíveis

Depois da strategy, verificar se agentes orchestrator estão instalados e registrar em `config.json > orchestrator`.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP — detecção de agentes orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

O framework GSD orquestra processos (gates, skills, reconcile). Para execução
paralela especializada (backend, frontend, UX, testes), ele invoca agentes
orchestrator DENTRO dos workflows.

Agentes detectados na instalação: {listar o que o ambiente reportar;
  se nada detectado, listar "nenhum"}

Opções:
  [1] Usar agentes detectados (mais rápido; GSD invoca em paralelo quando possível)
  [2] Fallback inline (Claude principal faz tudo; mais lento; ok para começar)
  [3] Personalizar lista (escolher quais usar)

Escolha [1/2/3]:
```

Grava em `.planning/config.json > orchestrator`:
- `enabled: true/false`
- `available_agents: [...]`
- `fallback_mode: "inline"` (sempre, salvo raras exceções)

**Recomendação:** começar com opção [2] em projetos novos para entender o fluxo GSD; migrar para [1] quando o time estiver confortável. Sem agentes, tudo funciona — só serial.

## 3.7. Escanear e indexar `docs/`

Antes de gerar `.planning/`, bootstrap escaneia `docs/` para listar o que será usado como contexto do projeto.

1. Lê `docs/INDEX.md` — se não existe, oferece criar template
2. Lista subpastas e conta arquivos em cada
3. Detecta binários (.xlsx, .docx, .pptx) sem espelho `.md` — pergunta se roda `bin/convert-docs.sh`
4. Valida presença de canônicos:
   - `docs/project-brief.md` (obrigatório — bootstrap falha se ausente)
   - `docs/identidade-visual/tokens.json` (obrigatório se projeto tem UI)
   - `docs/identidade-visual/brand.md` (warning se ausente)
   - `docs/identidade-visual/design-system.md` (warning se ausente)

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP — scan de docs/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

docs/
  ✓ INDEX.md presente
  ✓ project-brief.md canônico presente

docs/identidade-visual/
  ✓ INDEX.md presente
  ✓ tokens.json presente (tem color + space)
  ✓ brand.md presente
  ⚠ design-system.md ausente (opcional, mas recomendado)
  
docs/identidade-visual/wireframes/
  ⚠ INDEX.md ausente
  ? 2 arquivos: create-listing.html, checkout.pdf

docs/business/
  ⚠ INDEX.md ausente
  ? 3 arquivos: pitch.pdf, swot.xlsx, notas.md
  ⚠ swot.xlsx sem espelho .md

Gostaria de rodar /gsd-docs-index agora para organizar os INDEX.md
faltantes + converter binários? [s/N]
```

Se humano aceita, invoca `/gsd-docs-index` antes de prosseguir. Se recusa, bootstrap prossegue mas avisa que alguns arquivos serão ignorados pelo Claude por não estarem no índice.

## 4. Gerar `.planning/PROJECT.md`

Template preenchido a partir dos dados lidos. Não inventar. Citar fonte de cada bloco:

```markdown
# PROJECT — {project.name}

> Gerado por `/gsd-bootstrap` em {date}.
> Fonte: `docs/project-brief.md`, `specs/project.yaml`, `specs/stack.yaml`.
> Este documento reflete os arquivos-fonte. Mudanças de escopo vão via ADR.

## O que é este projeto

{extração de docs/project-brief.md — seção de visão/tese}

## Dono e domínio

- **Owner:** {project.owner}
- **Domínio prod:** {project.domain_prod}
- **Locale primário:** {project.locale}

## Valor único

{extração do project-brief — proposta de valor}

## Modelo de negócio

{extração do project-brief ou project.yaml — se declarado}

## Stack fechada (referência completa em `specs/stack.yaml`)

- Backend: {stack.backend.language} + {stack.backend.framework}
- Frontend: {stack.frontend.framework}
- Mobile: {stack.mobile.framework} (se aplicável)
- Banco: {stack.database.prod}
- Infra: {stack.infra}
- LLMs / integrações: {stack.external_services, se houver}

Mudança de stack = ADR nova em `docs/adrs/`.

## ADRs vigentes

{listagem dos ADRs encontrados com link — exibir título e 1 linha de resumo}

## Documentação de referência

- Brief: `docs/project-brief.md`
- Stack técnica: `specs/stack.yaml`
- Convenções DB: `specs/database.yaml` (se existir)
- Regras de negócio: `specs/rules.yaml` (se existir)
- ADRs: `docs/adrs/`
- Identidade visual: `docs/identidade-visual/` (se existir)

## Princípios

{extração do project-brief — seção de princípios, se houver}
```

## 5. Gerar `.planning/ROADMAP.md` inicial

Se o `project-brief.md` contém seção "Roadmap" ou "Fases" estruturada, extrair e formatar. Caso contrário, gerar skeleton com instrução:

```markdown
# ROADMAP — {project.name}

> Gerado por `/gsd-bootstrap`. Preencha as fases antes de rodar `/gsd-plan-phase`.
> Cada fase declara: goal, success criteria, duração estimada, dependências, flags (ui, mobile, integration_check).

## Visão geral

| Phase | Tema | Duração | Release | Depende | UI | Mobile | Integration |
|-------|------|---------|---------|---------|----|----|-----|
| **1** | Foundation | 1 sem | — | — | ☐ | ☐ | ☐ |
| **2** | ... | ... | ... | ... | ☐ | ☐ | ☐ |

## Semântica de flags

- **UI**: fase toca interface visual. Marcar `true` dispara o gate de UI-SPEC (Regra 4 do CLAUDE.md).
- **Mobile**: fase toca app mobile. Marcar `true` ativa seções extras no ui-phase (safe area, keyboard, haptic, offline).
- **Integration**: fase conecta múltiplas camadas (ex: mobile consumindo API). Marcar `true` dispara o integration-checker obrigatório pós-execução (Regra 6).

---

## PHASE 1 — {tema} ({duração})

**Goal:** {objetivo claro em 1 linha}

**Flags:** ui=false, mobile=false, integration_check=false

### Plan 01-01 — {nome do plano} ({duração})
{descrição 2-3 linhas}
**Success:** {critérios verificáveis}

### Plan 01-02 — ...

**Success criteria da Phase 1 (para fechar):**
- {critério 1}
- {critério 2}

---

{repetir estrutura para cada phase}

## Integration checks declarados (preencher para cada fase com integration_check=true)

Phase N:
  - endpoint: {método + path}
    consumer: {arquivo/cliente que chama}
    verify: {que precisa bater — body, headers, response shape}
```

Se o project-brief não declara fases, gerar apenas o header com instrução para o humano preencher, e abrir uma conversa:

```
ROADMAP skeleton criado em .planning/ROADMAP.md com 1 phase de exemplo.
O project-brief.md não declara fases estruturadas.

Quer que eu proponha um roadmap inicial baseado no brief? [s/N]
```

Se sim, analisar o brief (goals, diferenciais, MVP vs. v2) e propor 3-5 fases. Apresentar para aprovação antes de escrever.

## 6. Gerar `.planning/STATE.md` zerado

```markdown
# STATE — Current Execution State

> Documento vivo. Claude Code lê ao iniciar sessão. Atualiza ao fechar plano.
> Gerado por `/gsd-bootstrap` em {date}.

## Project Reference

See: `.planning/PROJECT.md` (bootstrap em {date})

**Core value:** {1 linha do PROJECT.md}
**Current focus:** Phase 1 Plan 01-01 — {nome}.

---

## Current Position

- **Phase:** 1 of {total} ({tema da phase 1})
- **Plan:** 01-01 (Ready to start)
- **Status:** Bootstrap completo, aguardando primeiro /gsd-discuss-phase 1.
- **Last activity:** {date} — Bootstrap.

**Progress:** `[░░░░░░░░░░░░░░░] 0% (0 of {total} phases complete)`

---

## Phase 1 — {tema}

Plans:
- [ ] **01-01** {nome}
- [ ] **01-02** ...

Success criteria to close Phase 1:
- {do ROADMAP}

---

## Next Actions (imediato)

Primeiro workflow recomendado:
```
/gsd-discuss-phase 1
```

Este captura suas decisões não-óbvias antes do planner agir.

---

## Histórico de sessões

| Data | Ação | Plan | Commit |
|------|------|------|--------|
| {date} | Bootstrap inicial — PROJECT.md, ROADMAP.md gerados | — | — |
```

## 7. Gerar artefatos auxiliares vazios

```bash
# .planning/REQUIREMENTS.md — skeleton
# .planning/MILESTONES.md — skeleton
# .planning/DECISIONS.md — skeleton append-only
# .planning/SUGGESTIONS.md — vazio
# .planning/TECH-DEBT.md — skeleton tabela
# .planning/config.json — defaults (copiar de .claude/get-shit-done/templates/config.json)
```

Cada um recebe header com data e instrução de uso.

## 8. Validar gates ativos

Verificar se o `config.json` gerado tem os gates ativados conforme contexto do projeto:

```bash
# Se ROADMAP tem qualquer fase com ui:true → ui_phase_blocking deve estar true
# Se ROADMAP tem qualquer fase com integration_check → integration_check deve estar true
# Se project-brief menciona "dado pessoal", "LGPD", "PII" → security_baseline deve estar true
# Se locale=pt-BR → response_language=pt-BR
```

Apresentar resumo:

```
Gates ativos neste projeto:
  ✓ ui_phase_blocking     (detectado ui=true em N fases)
  ✓ skills_enforcement    (sempre ativo)
  ✓ integration_check     (detectado integration_check em N fases)
  ✓ security_baseline     (detectado menção a LGPD/PII no brief)
  ✓ reconcile_before_close (sempre ativo)

Perf budget (LCP/INP/CLS/bundle) herdado do default. Ajustar em .planning/config.json se necessário.
```

## 9. Gerar commit inicial

```bash
git add .planning/ 2>/dev/null
git commit -m "chore(bootstrap): initial planning from docs/ and specs/

- PROJECT.md gerado de docs/project-brief.md
- ROADMAP.md gerado (N phases, M plans)
- STATE.md zerado em Phase 1 Plan 01-01
- config.json com gates apropriados ao escopo
"
```

Se não é repo git, avisar:

```
Este diretório não é um repositório git. Rode `git init` e `git add . && git commit -m "initial"` manualmente.
O framework depende de git para commits atômicos por plano.
```

## 10. Mensagem final

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► BOOTSTRAP COMPLETO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gerados:
  ✓ .planning/PROJECT.md
  ✓ .planning/ROADMAP.md ({N} phases, {M} plans)
  ✓ .planning/STATE.md (Phase 1 Plan 01-01 ready)
  ✓ .planning/REQUIREMENTS.md (skeleton)
  ✓ .planning/MILESTONES.md (skeleton)
  ✓ .planning/DECISIONS.md (append-only log)
  ✓ .planning/SUGGESTIONS.md (vazio)
  ✓ .planning/TECH-DEBT.md (skeleton)
  ✓ .planning/config.json

Próximos passos:
  1. Revise .planning/ROADMAP.md — confirme fases e flags
  2. Rode /gsd-discuss-phase 1 para capturar suas decisões da Phase 1
  3. Se Phase 1 tem ui:true, rode /gsd-ui-phase 1 em seguida (obrigatório)
  4. Depois /gsd-plan-phase 1 → /gsd-execute-phase 1

Lembretes:
  • Framework NÃO inventa requisito. Tudo vem de docs/ e specs/.
  • Para mudar stack ou escopo: propor ADR em docs/adrs/.
  • .planning/STATE.md é a bússola — lê em toda sessão.
```

</process>

<failure_modes>
- `docs/project-brief.md` vago ou genérico → bootstrap gera PROJECT.md vago. **Fix:** antes de rodar bootstrap, o brief deve ter: visão (1 parágrafo), valor único (1 parágrafo), público-alvo, diferenciais. Skeleton do template já tem estas seções.
- `specs/stack.yaml` incompleto → ROADMAP inicial impreciso. **Fix:** template do stack.yaml exige backend/frontend/db obrigatórios.
- `docs/adrs/` vazio em projeto existente → framework assume que não há decisões prévias. Se há, importar antes de rodar bootstrap.
- Projeto já populado com código → bootstrap só gera `.planning/`, não toca código. Código existente vira input do primeiro `/gsd-reconcile-state`.
</failure_modes>
