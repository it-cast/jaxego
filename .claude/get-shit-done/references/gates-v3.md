# Gates v3 — Enforcement detalhado

> **Esta é a especificação normativa dos gates bloqueantes do framework.**
> Referência citada por `CLAUDE.md` (Regras 4, 5, 6, 7, 8).

Um gate é um **check obrigatório** que, ao falhar, **interrompe o fluxo** e exige correção humana antes de prosseguir. Não é warning, não é sugestão. É bloqueio.

O framework tem 8 gates. Todos têm override via flag explícita (ex: `--skip-ui`), mas cada override é registrado em `.planning/DECISIONS.md` com a razão — override silencioso é impossível.

---

## Gate 1 — Bootstrap

**Onde:** Entrada de qualquer workflow de fase (plan-phase, discuss-phase, ui-phase, etc.).

**O que verifica:** `.planning/PROJECT.md` existe.

**Block se:** Arquivo não existe.

**Mensagem de erro:**
```
❌ Bootstrap não foi executado.

Este framework exige bootstrap antes de qualquer operação de fase.
Rode primeiro:
  /gsd-bootstrap

Bootstrap lê docs/project-brief.md + specs/*.yaml e gera .planning/ inicial.
```

**Override:** Não existe. Bootstrap é verdadeiramente obrigatório.

---

## Gate 2 — UI-SPEC antes de PLAN

**Onde:** `plan-phase.md`, logo após parsear argumentos.

**O que verifica:** Se a fase declarou `ui: true` no `ROADMAP.md`, verifica se existe `.planning/phases/<NN>-<slug>/UI-SPEC.md`.

**Como detectar `ui: true`:**

```bash
# Procurar a linha da phase no ROADMAP.md e dentro do bloco, encontrar 'ui:'
PHASE_UI=$(awk -v phase="$PHASE_NUMBER" '
  /^## PHASE/ && $0 ~ phase { in_phase=1 }
  /^## PHASE/ && $0 !~ phase { in_phase=0 }
  in_phase && /^\*\*Flags:\*\*/ {
    if ($0 ~ /ui=true/) { print "true"; exit }
    else { print "false"; exit }
  }
' .planning/ROADMAP.md)
```

Alternativa: tabela-resumo no topo do ROADMAP com coluna `UI` tem `✓` ou `true`.

**Block se:** `ui=true` E `UI-SPEC.md` não existe E não há flag `--skip-ui` E não há ADR aprovada justificando.

**Mensagem de erro:**
```
❌ Esta fase toca UI mas não tem UI-SPEC.md.

UI-SPEC.md é o design contract: define tokens, tipografia, copy, estados,
micro-interações ANTES do código. Sem ele, frontend é escrito ad-hoc e
precisa de redesign retroativo (observado em projetos anteriores).

Rode primeiro:
  /gsd-ui-phase {N}                   # para fase web
  /gsd-ui-phase {N} --mobile          # para fase mobile

Se você tem razão documentada para pular (ex: fase de bugfix que não toca design):
  /gsd-plan-phase {N} --skip-ui --reason "bugfix only, no visual changes"

O skip será registrado em .planning/DECISIONS.md.
```

**Override:** `--skip-ui --reason "<texto>"`. Registra em DECISIONS.md.

---

## Gate 3 — Skills coverage no PLAN.md

**Onde:** `gsd-plan-checker` (rodando após `gsd-planner`).

**O que verifica:** O `PLAN.md` gerado tem as seções obrigatórias `## Skills Consultadas` e `## Skills Dispensadas (com justificativa)`, e as skills citadas cobrem as áreas tocadas pelas tasks.

**Matriz de skills obrigatórias por tipo de task:**

| Tipo de task (detecção por keyword/path) | Skill(s) obrigatória(s) |
|---|---|
| Path `apps/*/src/`, `frontend/`, `admin/` + criação/edição de component/template | Skill de framework (ex: `angular-material-patterns`, `react-patterns`) + `design-to-code` |
| Path `apps/mobile/`, keyword "ionic", "capacitor" | `ionic-patterns` + `mobile/*` (safe-areas, offline-first quando aplicável) |
| Endpoint novo ou edição de router (FastAPI, Express, etc.) | `owasp-security` + `api-design-contracts` |
| Keyword "auth", "jwt", "login", "password", "token" | `owasp-security` (obrigatório) |
| Campo de formulário com CPF/CNPJ/CEP/telefone BR | `brazilian-forms` + `ux-copywriting-ptbr` |
| Texto visível ao usuário (labels, mensagens, empty states) | `ux-copywriting-ptbr` (se locale=pt-BR) ou equivalente |
| Endpoint retornando dado pessoal | `lgpd-compliance` |
| Upload de arquivo | `file-upload-ux` |
| Pagamento (Stripe, Asaas, Mercado Pago, {gateway-pagamento}, PayPal, etc.) | Skill do gateway específico |
| Nova tabela / migration | `mysql-schema-design` (ou equivalente) |
| Handler de erro / mensagem de erro | `error-ux-patterns` |
| Qualquer endpoint servindo em produção | `observability-production` |
| Componente visual com estado | `error-ux-patterns` + `empty-states-polish` |

**Block se:** 2+ skills obrigatórias não citadas (nem em Consultadas, nem em Dispensadas com justificativa).

**Warning (FLAG, não BLOCK) se:** 1 skill obrigatória não citada.

**Mensagem de block:**
```
❌ PLAN.md não cobre skills obrigatórias.

Tasks identificadas por área:
  • Task T-03 (criar componente admin/src/.../proposals-list.component.ts)
    → exige: angular-material-patterns, design-to-code, error-ux-patterns
    → no PLAN.md: nenhuma citada.
  • Task T-05 (POST /api/v1/proposals/{id}/accept)
    → exige: owasp-security, api-design-contracts, observability-production
    → no PLAN.md: apenas api-design-contracts citada.

Total de skills obrigatórias não cobertas: 5.

Ações possíveis:
  1. Revisar o PLAN.md, adicionar skills em ## Skills Consultadas
  2. Se uma skill não se aplica, declará-la em ## Skills Dispensadas com justificativa
  3. Se alguma skill não existe, criar com /gsd-skill-creator

O plan-checker VAI reprovar novamente se as lacunas persistirem.
```

**Override:** Único override é escrever justificativa em `## Skills Dispensadas`. Ex:
```markdown
## Skills Dispensadas (com justificativa)
- `lgpd-compliance` — endpoint não manipula PII, apenas lê UUIDs
- `angular-material-patterns` — esta fase só tem código backend
```

O plan-checker aceita justificativas escritas, não flags.

---

## Gate 4 — Security Baseline no RESEARCH.md

**Onde:** `plan-phase.md`, antes de invocar o `gsd-planner`.

**O que verifica:** Se a fase tem características de risco de segurança, o `RESEARCH.md` tem seção `## Security Baseline`.

**Características de risco (qualquer uma ativa o gate):**
- ROADMAP diz que fase cria ou modifica endpoints
- ROADMAP diz que fase toca autenticação, sessão, token, OAuth
- Fase trata PII (dados pessoais), conforme declarado em `specs/rules.yaml` ou `CONTEXT.md`
- Fase integra gateway de pagamento, webhook externo, ou serviço 3rd-party
- Fase expõe admin/área privilegiada

**Block se:** Características de risco presentes E `RESEARCH.md` sem seção `Security Baseline`.

**Mensagem de erro:**
```
❌ Phase {N} tem risco de segurança mas RESEARCH.md não tem Security Baseline.

Gaps detectados:
  • {lista das características de risco}

O researcher deve produzir seção ## Security Baseline no RESEARCH.md consultando
a skill owasp-security, cobrindo:
  1. Autenticação/autorização apropriada por endpoint
  2. Input validation + sanitização
  3. Storage seguro de tokens (httpOnly cookies, NUNCA localStorage para JWT)
  4. Rate limiting nos endpoints sensíveis
  5. CSRF/CORS policy correta
  6. Logging sem vazar PII

Rode:
  /gsd-research-phase {N} --security-focus

Se a fase realmente não tem risco (declarado incorretamente no ROADMAP):
  Ajuste ROADMAP.md removendo características de risco da descrição da fase,
  e registre em DECISIONS.md.
```

---

## Gate 5 — Integration checkpoint pós-execução

**Onde:** `execute-phase.md`, no fim do processamento de waves.

**O que verifica:** Se a fase tem `integration_check` declarado no `ROADMAP.md`, o `gsd-integration-checker` foi invocado e retornou CLEAN (sem gaps).

**Como detectar integration_check:** procurar bloco no ROADMAP:
```yaml
integration_check:
  - endpoint: POST /proposals/{id}/accept
    consumer: mobile/client/chat/chat.page.ts
    verify: body tem payment_method, resposta tem service_request_id
```

**Block se:** Integration_check declarado E checker não rodou ou retornou GAPS.

**Mensagem de erro:**
```
❌ Phase {N} declara integration_check mas gaps foram encontrados.

Contratos a validar:
  • POST /api/v1/proposals/{id}/accept
    → consumer: apps/mobile/src/app/chat/chat.page.ts:156
    → esperado: body tem {payment_method, service_request_id}
    → encontrado: consumer envia body VAZIO
    → gap: INTEG-01

  • ws://{host}/api/v1/ws/conversations/{id}
    → consumer: apps/mobile/src/core/websocket.service.ts:28
    → esperado: URL inclui prefixo /api/v1/
    → encontrado: URL sem prefixo
    → gap: INTEG-02

Ações:
  1. Corrigir consumers antes de fechar a fase
  2. Ou corrigir servers se o consumer está certo
  3. Criar tasks de hotfix em PLAN.md: T-fix-INTEG-01, T-fix-INTEG-02
  4. Re-rodar /gsd-execute-phase {N} para aplicar fixes

Este bloqueio previne bugs que só aparecem no audit semanas depois (padrão
observado em projetos anteriores: 5 bugs críticos de integração chegaram
ao audit em projetos sem integration-checker como gate).
```

**Override:** Não existe. Integration gaps são por definição blockers.

---

## Gate 6 — Reconciliation antes de fechar fase

**Onde:** `verify-phase.md`, como último passo antes de marcar fase COMPLETE.

**O que verifica:** Arquivo `.planning/phases/<NN>-<slug>/RECONCILIATION.md` existe E seu campo "Status geral" é `✅ CLEAN`.

**Block se:**
- `RECONCILIATION.md` não existe, OU
- Status é `⚠️ GAPS` com gaps não resolvidos, OU
- Status é `❌ DIVERGENT`.

**Mensagem de erro:**
```
❌ Phase {N} não pode ser marcada COMPLETE antes da reconciliação.

Status atual: {GAPS | DIVERGENT | AUSENTE}

Afirmações divergentes:
  • {lista de divergências do RECONCILIATION.md}

Rode:
  /gsd-reconcile-state {N}           # gera/atualiza RECONCILIATION.md
  /gsd-reconcile-state {N} --apply   # aplica patches propostos

Este gate previne o padrão observado: documentação que diverge do código
(ex: um service declarado como "4/26 features" quando código já tinha 26/26) persistindo
por semanas sem detecção.
```

**Override:** Resolver todas divergências ou declarar em DECISIONS.md porque uma divergência é aceita temporariamente (raro).

---

## Gate 7 — Tests + Lint verdes

**Onde:** Entrada final de cada plano, antes do commit.

**O que verifica:**
- `make test` (ou `pnpm test`, `cargo test`, conforme projeto) retorna exit 0
- `make lint` (ou `ruff check .`, `eslint`, etc.) retorna exit 0

**Block se:** Qualquer exit != 0.

**Mensagem de erro:** Padrão. Sem ajuste necessário.

**Override:** Não existe. Testes e lint são piso absoluto.

---

## Gate 8 — Senior Quality Bar (v0.9.5)

**Onde:** Em `verify-phase`, após Gate 6 (Reconciliation) e antes de fechar a phase. Em `execute-phase`, o `gsd-code-reviewer` já avalia os mesmos critérios em modo advisory; o Gate 8 é o veredito bloqueante.

**O que verifica:** A phase atende a Definição de Pronto sênior codificada em `quality/senior-quality-bar` (blocos A-dev, B-segurança, C-deploy, D-UX). Cada item aplicável recebe PASS / FAIL-BLOCK / FAIL-DEBT / N/A.

**Block se:** Existe qualquer **FAIL-BLOCK** aberto. A lista de FAIL-BLOCK é deliberadamente curta e inegociável:
- Segredo (chave/senha/token) commitado no repo ou hardcoded
- Deploy sem rollback, ou migração sem backup pré-migração obrigatório
- N+1 detectado em endpoint de lista
- Input do usuário interpolado em SQL/comando (injection possível)
- Endpoint novo sem decisão explícita de auth (público vs protegido)
- PII em log

**FAIL-DEBT:** item não atendido mas não perigoso → exige linha em TECH-DEBT.md com `urgency_class` + aceite humano. Não bloqueia, mas fica visível. É o que impede a barra de virar teatro: o perigoso bloqueia, o melhorável é contabilizado.

**Override:** FAIL-BLOCK só pode ser ignorado com `--skip-gate 8 --reason "<motivo real>"`, registrado em DECISIONS.md. Para segredo no repo e backup ausente, o override é desencorajado a ponto de exigir confirmação dupla — são as falhas que mais custam em produção.

**Executor:** `gsd-verifier` invoca a avaliação lendo `quality/senior-quality-bar/SKILL.md`; em phase de release, `gsd-release-auditor` cobre os blocos C e parte do B.

---

## Ordem dos gates por workflow

### `/gsd-bootstrap`
1. Verificar que docs/specs obrigatórios existem (falha com mensagem de template)

### `/gsd-discuss-phase <N>`
1. Gate 1 (Bootstrap)

### `/gsd-ui-phase <N>`
1. Gate 1 (Bootstrap)
2. CONTEXT.md existe (warning, não block)

### `/gsd-research-phase <N>`
1. Gate 1 (Bootstrap)
2. Se fase tem risco: produzir Security Baseline

### `/gsd-plan-phase <N>`
1. Gate 1 (Bootstrap)
2. **Gate 2 (UI-SPEC)** ← bloqueia aqui
3. **Gate 4 (Security Baseline)** ← bloqueia aqui
4. Planner roda
5. **Gate 3 (Skills coverage)** ← plan-checker bloqueia

### `/gsd-execute-phase <N>`
1. Gate 1 (Bootstrap)
2. PLAN.md existe e passou plan-checker
3. Executor roda waves
4. **Gate 5 (Integration check)** ← bloqueia se integration_check declarado
5. Gate 7 (Tests + Lint) por plano

### `/gsd-verify-phase <N>`
1. Gate 1 (Bootstrap)
2. **Gate 6 (Reconciliation)** ← bloqueia aqui
3. Checagem de success criteria do ROADMAP
4. **Gate 8 (Senior Quality Bar)** ← bloqueia se há FAIL-BLOCK aberto

---

## Registro de overrides

Todo override (uso de `--skip-*` ou justificativa explícita) gera entrada em `.planning/DECISIONS.md`:

```markdown
## {DATE} — Override de gate

- **Gate:** Gate 2 (UI-SPEC)
- **Fase:** Phase 07
- **Flag:** --skip-ui
- **Razão:** Fase é de bugfix backend apenas, nenhum template tocado.
- **Aprovado por:** {humano}
- **Rollback se necessário:** Voltar e rodar /gsd-ui-phase 07 antes de qualquer
  nova fase com frontend.
```

Isso garante que overrides ficam auditáveis. Não existe override silencioso.

---

## Métricas de saúde dos gates

Coletado por `/gsd-health`:

- **Taxa de override por gate** — se um gate é sempre overridden, está desregulado
- **Taxa de fix commits por fase** — se alta, gates não estão pegando os problemas
- **Tempo entre bug → detecção** — se > 1 dia, integration-checker não está sendo efetivo
- **Divergência artefato ↔ código** após reconcile — deve ser zero consistentemente

Quando métricas degradam, revisar este arquivo e ajustar checks.
