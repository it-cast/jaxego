# GUIA — Descoberta de Novo Projeto

> **Leia este arquivo INTEIRO antes de iniciar a sessão de descoberta.**
>
> Este manual é para Claude conduzir uma sessão estruturada de discussão com o humano sobre um projeto novo, terminando com TODOS os arquivos canônicos prontos para `/gsd:bootstrap` rodar com sucesso.

---

## 1. Para que serve este manual

**Cenário típico:** humano chega para começar projeto novo. Ainda não rodou nada do framework. Quer discutir a ideia primeiro, sair com docs estruturados, depois rodar bootstrap.

**O que este manual te dá (Claude):**
- Protocolo de discussão dirigida (ordem, perguntas, validações)
- Lista exata de arquivos que VOCÊ vai gerar ao final
- Templates de cada arquivo
- Critério de "pronto" para cada um
- Quando parar de perguntar e começar a escrever

**O que este manual NÃO faz:**
- Não substitui `/gsd:bootstrap` — ele continua sendo o passo seguinte
- Não inventa mecanismos novos no framework
- Não obriga estruturas que o framework não consome

---

## 2. Saída obrigatória da sessão (mínimo viável)

`/gsd:bootstrap` **só falha se faltar um destes 3 arquivos**:

```
docs/project-brief.md       (~120 linhas, 12 seções, narrativo)
specs/project.yaml          (~50 linhas, metadata estrutural)
specs/stack.yaml            (~100 linhas, stack técnica)
```

**Se você gerar só esses 3 arquivos com qualidade, o bootstrap vai rodar.** O resto é opcional, mas eleva muito a qualidade do roadmap gerado.

## 3. Saída recomendada (qualidade alta)

Para o framework gerar roadmap denso, milestones realistas e enforcement preciso, gere também:

```
specs/database.yaml                       (se projeto tem persistência)
specs/rules.yaml                          (regras de negócio invariantes)
docs/identidade-visual/tokens.json        (OBRIGATÓRIO se projeto tem UI)
docs/identidade-visual/brand.md           (recomendado se projeto tem UI)
docs/identidade-visual/INDEX.md           (recomendado se projeto tem UI)
docs/INDEX.md                             (recomendado sempre)
docs/adrs/ADR-XXX-{slug}.md               (uma para cada decisão arquitetural definitiva)
```

## 4. Saída para projetos complexos (opcional, alto investimento)

**Apenas se humano explicitamente pedir** ou se o projeto for grande (SaaS multi-tenant, marketplace, plataforma B2B com múltiplos atores):

```
docs/press-release.md                     (Working Backwards do Bezos)
docs/project-spec/01-VISAO-E-PROPOSITO.md
docs/project-spec/02-PUBLICO-E-CASOS-DE-USO.md
docs/project-spec/03-ENTREGAVEIS-DETALHADOS.md
... (e outros conforme natureza do projeto)
```

**Importante:** esses arquivos extras NÃO são lidos pelo `/gsd:bootstrap`. Eles vivem como contexto rico para humanos e para o Claude consultar em fases posteriores. Não exagerar — para 90% dos projetos, os 3 obrigatórios + identidade visual bastam.

---

## 5. PROTOCOLO DE SESSÃO — passo a passo

### Pré-requisitos (verificar antes de começar)

Antes de iniciar a discussão, confirmar:

- [ ] Humano descompactou o framework
- [ ] Estamos em sessão Claude Code com permissões aprovadas
- [ ] Pasta do projeto está vazia (ou só com framework bruto)
- [ ] Humano tem 60-120 min disponíveis para a sessão

Se algum item ausente, peça para resolver antes.

### Fase 1 — Aquecimento (5 min)

**Objetivo:** alinhar expectativas e estabelecer protocolo.

**Diga ao humano (literal):**

> "Vou conduzir uma sessão de descoberta do seu projeto. Vou perguntar sobre o produto, usuário, modelo de negócio, stack, regras críticas. Ao final, gero os arquivos que `/gsd:bootstrap` precisa para começar.
>
> Tempo estimado: 60-120 min dependendo da complexidade. Vou pausar a cada bloco para você validar.
>
> Antes de começar, me confirma: (a) é projeto comercial/produto ou interno/ferramenta? (b) já existe algum documento sobre ele que eu deveria ler primeiro? (c) você tem todas as decisões importantes tomadas ou vamos descobrir junto?"

**Aguarde resposta.** Calibra abordagem:
- Se tem docs prévios → leia primeiro, faça perguntas só sobre lacunas
- Se não tem nada → discussão completa do zero
- Se decisões já tomadas → mais validação, menos exploração

### Fase 2 — Descoberta (45-90 min, dividida em 7 blocos)

Em cada bloco, **uma pergunta por vez**, espere resposta, **resuma com suas palavras**, valide, anote, próxima.

**NUNCA invente respostas.** Se humano não souber, anote `a definir` e siga.

#### Bloco 2.1 — Identidade do produto (5 min)

1. "Em uma frase, o que é seu projeto e quem ele atende?"
2. "Qual o nome (final ou trabalho) e código curto (slug em kebab-case)?"
3. "É produto B2C, B2B ou ferramenta interna?"
4. "Já tem domínio ou está procurando?"

#### Bloco 2.2 — Usuário-alvo e dor (10 min)

1. "Descreve o usuário primário em 3 linhas: idade, contexto, comportamento atual."
2. "Que dor concreta esse usuário tem hoje? Como ele resolve hoje sem seu produto?"
3. "Tem usuários secundários? Quem?"
4. "Quem NÃO é seu usuário? (importante para escopo)"

**Cuidado especial:** se humano disser "todo mundo é meu usuário", pare e force especificidade. Produto sem usuário-alvo claro vira escopo infinito.

#### Bloco 2.3 — Proposta de valor e diferencial (10 min)

1. "O que seu produto faz que o usuário hoje não consegue ou faz mal?"
2. "Quais alternativas existem hoje (concorrentes diretos, indiretos, fazer manualmente)?"
3. "Por que o usuário escolheria seu produto em vez das alternativas?"
4. "Tem algum diferencial difícil de copiar? (rede, dados, regulamentação, marca, IP)"

#### Bloco 2.4 — Modelo de negócio (10 min)

1. "Como vai monetizar? (assinatura, pagamento por uso, comissão, freemium, B2B contrato)"
2. "Tem tiers ou pacotes definidos? Se sim, quais e quanto cada?"
3. "Qual sua meta de receita em 6 meses? E em 12?"
4. "Qual seu KPI primário (north star)? E os secundários?"

**Se humano não souber preço:** OK por enquanto. Anote `a definir` e siga.

#### Bloco 2.5 — Stack técnica (10 min)

1. "Linguagem e framework do backend? Versão?"
2. "Frontend é web, mobile, ambos? Que framework?"
3. "Banco de dados? Cache? Queue?"
4. "Onde vai hospedar? VPS, cloud (AWS/GCP/Azure), Vercel, outro?"
5. "Tem decisões arquiteturais já fechadas que viraram ADR? Quais?"
6. "Compliance que afeta arquitetura? (LGPD, HIPAA, PCI, SOX)"
7. "Integrações com terceiros já decididas? (pagamento, email, SMS, etc.)"

#### Bloco 2.6 — Escopo MVP e fora-de-escopo (15 min)

**Esta é a seção mais importante para o roadmap subsequente.**

1. "Quais features são MUST-HAVE para lançar a primeira versão?" (lista)
2. "Quais ficam para v2/v3?" (lista)
3. "Quais features VOCÊ NUNCA vai construir?" (lista — força escopo)
4. "Tem prazo definido? Solo dev, time? Quantas horas/semana?"
5. "Tem budget travado em algum aspecto? (ex: não pode pagar SaaS premium, não pode contratar dev senior)"

#### Bloco 2.7 — Riscos, princípios, regras críticas (10 min)

1. "Quais são os 3 maiores riscos do projeto que tiram seu sono?"
2. "Que princípio inviolável você tem? (ex: 'nunca pedir mais dados do usuário do que necessário', 'tudo testável em staging antes de prod')"
3. "Que erro de projeto anterior você quer evitar repetir?"
4. "Que regra de negócio é absolutamente crítica e não pode quebrar nunca? (ex: 'pedido só pode confirmar se pagamento foi capturado', 'soft delete em tudo, hard delete só por compliance')"

### Fase 3 — Validação (15 min)

**Antes de gerar arquivo nenhum**, faça recap honesto:

**Diga (literal):**

> "Vou resumir o que entendi até aqui. Por favor confirme ou corrija item por item:
>
> [Liste tudo que captou em 1 linha por item, organizando por bloco]
>
> Há algo que entendi errado, algo que ficou faltando, ou algum ponto que você quer aprofundar?"

**Espere resposta.** Itere até humano dizer "tá bom, pode gerar".

**Identifique buracos críticos:**
- Stack técnica sem versão definida → pergunte versão (não invente)
- Escopo MVP com >15 features → force priorização (15+ features = 6 meses, é muito)
- Sem KPI primário → force escolher um (não pode ser "tudo importa")
- Sem usuário-alvo concreto → bloqueie geração até definir

**Se buraco crítico, NÃO gere arquivo.** Diga:

> "Identifiquei [X] buraco(s) crítico(s) que se eu deixar passar vai gerar roadmap ruim. Vamos resolver antes de gerar arquivos: [lista]"

### Fase 4 — Geração dos arquivos (30-60 min)

**Ordem obrigatória de geração** (cada um depende do anterior):

1. `specs/project.yaml` (estrutural — base de tudo)
2. `specs/stack.yaml` (técnica — usado por skills enforcement)
3. `specs/rules.yaml` (regras — opcional mas recomendado)
4. `specs/database.yaml` (apenas se projeto tem DB)
5. `docs/project-brief.md` (narrativo, consolida tudo acima)
6. `docs/identidade-visual/tokens.json` (obrigatório se has_ui)
7. `docs/identidade-visual/brand.md` (recomendado se has_ui)
8. `docs/identidade-visual/INDEX.md`
9. `docs/INDEX.md`
10. `docs/adrs/ADR-001-{slug}.md`, `ADR-002-{slug}.md`, ... (uma por decisão fechada)

**Para cada arquivo:**

1. Anuncie qual está gerando: "Vou gerar agora `specs/project.yaml`. Volto com o conteúdo."
2. Use o template da seção 6 deste manual
3. Preencha **com os dados da discussão**, não invente
4. Onde faltou info, escreva `[a definir]` ou `null`
5. Apresente para humano revisar
6. Pergunte: "Está correto? Algo a ajustar?"
7. Se humano pediu ajuste, reescreva inteiro (não tente patches)
8. Quando humano confirmar, escreva no disco
9. Próximo arquivo

**Ao final dos 10 arquivos**, faça commit sugerido:

```bash
git add docs/ specs/
git commit -m "docs: especificação inicial do projeto pronta para /gsd:bootstrap"
```

---

## 6. TEMPLATES DOS ARQUIVOS

### 6.1 `specs/project.yaml`

```yaml
# ══════════════════════════════════════════
# SPECS — Identidade e configuração do projeto
# ══════════════════════════════════════════

project:
  name: "{Nome formal}"
  codename: "{slug-kebab-case}"
  description_pt_br: |
    {1 parágrafo descrevendo o projeto, em português,
    incluindo proposta de valor e usuário primário.}

  type: "{saas | b2b-saas | b2c-app | internal-tool | marketplace | api-product}"
  locale: "pt-BR"
  domain_prod: "{ex: meuprojeto.com.br ou null}"
  domain_staging: "{ex: staging.meuprojeto.com.br ou null}"

owner:
  name: "{Nome do dono / decisor}"
  email: "{email}"
  org: "{empresa ou null se solo}"

team:
  size: {1 | 2 | ...}
  roles: ["dev", "designer", "..."]
  hours_per_week: {N}

timeline:
  mvp_target_months: {N}
  hard_deadline: "{ISO date ou null}"

compliance:
  - "LGPD"
  - "{outros aplicáveis ou remova}"

created: "{YYYY-MM-DD}"
```

**Critério de pronto:**
- Todos os campos preenchidos ou explicitamente `null`
- `codename` em kebab-case válido (sem espaços, sem acentos)
- `type` é um dos valores aceitos

---

### 6.2 `specs/stack.yaml`

```yaml
# ══════════════════════════════════════════
# SPECS — Stack técnica fechada
# ══════════════════════════════════════════
# Versões travadas ditam decisões. Não use "talvez X ou Y".

backend:
  language: "{python | typescript | go | rust | php | ...}"
  language_version: "{ex: 3.13, 22.0, 1.22}"
  framework: "{ex: fastapi, nestjs, gin, actix}"
  framework_version: "{travado}"
  orm: "{ex: sqlalchemy, prisma, gorm | null}"
  package_manager: "{uv, pnpm, go-mod, ...}"
  test_runner: "{pytest, jest, ...}"
  linter: "{ruff, eslint, ...}"
  type_checker: "{basedpyright, tsc | null}"

# Apenas se projeto tem frontend web:
frontend_web:
  framework: "{angular | react | vue | svelte | null se não tem}"
  framework_version: "{travado}"
  ui_kit: "{material, mui, shadcn, ionic, antd, none}"
  build: "{vite, turbopack, webpack}"
  styling: "{scss, tailwind, css-modules, styled-components}"

# Apenas se projeto tem mobile:
frontend_mobile:
  framework: "{angular-ionic | react-native | flutter | swift | kotlin | null}"
  wrapper: "{capacitor, expo | null}"
  targets: ["android", "ios"]

database:
  primary: "{mysql | postgres | sqlite | mongodb | null}"
  primary_version: "{travado}"
  migrations: "{alembic, prisma, knex, flyway}"
  cache: "{redis | memcached | null}"
  queue: "{celery, arq, bullmq, sidekiq | null}"
  search: "{elasticsearch, meilisearch, typesense | null}"

infra:
  hosting: "{vps-hetzner | aws | gcp | vercel | railway | ...}"
  containerization: "{docker, podman | null}"
  orchestration: "{docker-compose, kubernetes, ecs | null}"
  ci_cd: "{github-actions, gitlab-ci, circleci, ...}"
  reverse_proxy: "{nginx, traefik, caddy | null}"
  ssl: "{letsencrypt, cloudflare | null}"

observability:
  logs: "{stdout, loki, datadog, ...}"
  metrics: "{prometheus, datadog | null}"
  errors: "{sentry, bugsnag | null}"
  apm: "{datadog, newrelic | null}"

auth:
  strategy: "{jwt | session | oauth2 | clerk-managed | ...}"
  password_hash: "{argon2id | bcrypt | scrypt}"
  mfa: "{totp, webauthn | null se não tem}"
  session_storage: "{redis, db, jwt-stateless}"

# Apenas se projeto cobra:
payment:
  psp_primary: "{stripe, asaas, pagarme, mercadopago | null}"
  methods: ["card", "pix", "boleto", "..."]

# Apenas se projeto faz upload:
storage:
  object: "{s3, backblaze-b2, cloudflare-r2 | null}"
  cdn: "{cloudfront, cloudflare | null}"

# Apenas se projeto manda email:
email:
  transactional: "{sendgrid, postmark, ses | null}"
  marketing: "{mailchimp, sendgrid-marketing | null}"

# Apenas se projeto integra com LLMs:
llm:
  providers: ["claude", "openai", "..."]
  router: "{custom, langchain, llamaindex | null}"
  cache: "{redis, ...}"

# Constraints técnicos
constraints:
  must_run_offline: {true | false}
  multi_tenant: {true | false}
  reproducibility_critical: {true | false}
  performance_budget:
    api_p95_ms: {ex: 200 | null}
    web_lcp_ms: {ex: 2500 | null}
```

**Critério de pronto:**
- Versões travadas (não "latest", não "TBD")
- Campos não-aplicáveis explicitamente `null` (não omitidos)
- Sem mistura de stack (não pode ter `python` E `typescript` no backend principal)

---

### 6.3 `specs/rules.yaml`

```yaml
# ══════════════════════════════════════════
# SPECS — Regras de negócio invariantes
# ══════════════════════════════════════════
# Estas regras são LEI do projeto. Código que viole bloqueia gate de skills.

rules:
  - id: R-001
    description: "{Regra clara, declarativa, em pt-BR}"
    criticality: "{high | medium | low}"
    rationale: "{por que essa regra existe}"
    enforcement: "{onde no código essa regra deve viver}"

  - id: R-002
    description: "{ex: Pedido só pode ser confirmado se pagamento foi capturado}"
    criticality: high
    rationale: "Evita inadimplência e estorno"
    enforcement: "PaymentService.confirm() valida payment_status == captured"

  # ... mínimo 3, máximo 30 regras

# Convenções técnicas que afetam skills:
conventions:
  api:
    versioning: "{url-prefix | header | none}"
    error_format: "{json:api | rfc7807 | custom}"
    pagination: "{cursor | offset | none}"
  database:
    soft_delete: {true | false}
    audit_log: {true | false}
    naming: "{snake_case | camelCase}"
  frontend:
    state_management: "{signals | redux | none}"
    forms: "{reactive | template | hook-form}"
```

**Critério de pronto:**
- Cada regra com `id`, `description`, `criticality`, `rationale`, `enforcement`
- Pelo menos 3 regras `high` (se < 3, projeto provavelmente está mal escopado)
- Convenções coerentes com `stack.yaml`

---

### 6.4 `specs/database.yaml` (apenas se tem DB)

```yaml
# ══════════════════════════════════════════
# SPECS — Schema de dados
# ══════════════════════════════════════════
# Esboço inicial — vai evoluir. Foco em entidades core.

tables:
  users:
    description: "Autenticação base"
    columns:
      - id: "uuid, PK"
      - email: "string 255, unique, not null"
      - password_hash: "string 255, not null"
      - status: "enum(pending, active, suspended)"
      - created_at: "timestamp, default now()"
      - updated_at: "timestamp, default now()"
    indexes:
      - "email"
      - "status + created_at"

  # ... outras tabelas core

relacionamentos:
  - "{descrição em texto: Pedidos têm 1:N com Itens}"

constraints:
  - "Soft delete em tabelas de domínio (deleted_at nullable)"
  - "FKs com ON DELETE RESTRICT em tabelas críticas"
```

**Critério de pronto:**
- 3-15 tabelas (mais de 15 = projeto grande demais para MVP)
- Campos com tipo + constraint
- Pelo menos 1 índice por tabela

---

### 6.5 `docs/project-brief.md`

**Estrutura obrigatória de 12 seções** (espelha o que o framework espera):

```markdown
# PROJECT BRIEF — {Nome do Projeto}

> Fonte de verdade do projeto. Tudo o mais (PROJECT.md, ROADMAP.md) deriva deste arquivo.
> Mudanças aqui = considere abrir ADR em `docs/adrs/`.

## 1. Identidade

- **Nome:** {nome}
- **Codename/slug:** {slug-kebab}
- **Domínio prod:** {url ou "a definir"}
- **Tipo:** {SaaS B2B | App B2C | Ferramenta interna | ...}
- **Owner:** {nome — email}
- **Time:** {1 dev solo / 2 devs / etc.}
- **Capacidade:** {N horas/semana}

## 2. Visão (1 parágrafo)

{Descrição em 3-5 linhas do que o produto faz, para quem, e qual o resultado pretendido.}

## 3. Tese (1 parágrafo)

{Por que esse produto existe agora? Que mudança no mercado, comportamento ou tecnologia abriu espaço para ele? Qual a "tese" que se valida ou cai com esse projeto.}

## 4. Público-alvo

### Primário
{Persona, idade, ocupação, comportamento, dor concreta. 3-5 linhas.}

### Secundário
{Se houver. Pode ser "Nenhum" se for foco único.}

### NÃO é público
{Lista explícita de quem não é alvo. Importante para escopo.}

## 5. Valor único

{O que esse produto faz que alternativas existentes não fazem? Por que o usuário troca de comportamento atual? Diferencial difícil de copiar — se houver.}

## 6. Modelo de negócio

- **Como monetiza:** {assinatura | comissão | uso | freemium | B2B contrato}
- **Tiers/pacotes:** {tabela ou lista}
- **Meta MRR 6m:** {R$ X}
- **Meta MRR 12m:** {R$ X}
- **KPI primário (north star):** {qual e meta}
- **KPIs secundários:** {3-5 itens}

## 7. Roadmap de releases

### v1.0 — MVP (semanas 1-{N})
- {Feature 1}
- {Feature 2}
- ...

### v1.1 — Pós-MVP (semanas {N+1}-{M})
- ...

### v2.0 — Futuro (>6 meses)
- ...

## 8. Princípios invioláveis

- {Princípio 1 — ex: "Toda alegação preditiva tem evidence_ref obrigatório"}
- {Princípio 2 — ex: "Nenhum endpoint sem auth exceto health check"}
- {Princípio 3 — ex: "LGPD: anonimização em 30d após exclusão"}
- {3-7 princípios totais}

## 9. Anti-patterns conhecidos (NÃO fazer)

- {Coisa que projetos similares erram e seu projeto NÃO vai cometer}
- {Lista de no-go's claros}

## 10. Fases de desenvolvimento propostas

### Fase 1 — Foundation (semanas 1-{N})
{Descrição: setup, auth, models básicos, CI}

### Fase 2 — {Nome} (semanas {N}-{M})
{Descrição}

### Fase 3 — ...
...

## 11. Contexto externo relevante

- **Concorrentes diretos:** {lista}
- **Concorrentes indiretos:** {lista}
- **Regulamentação aplicável:** {LGPD, fiscal, setorial}
- **Integrações terceiros já decididas:** {Stripe, SendGrid, etc.}

## 12. Riscos conhecidos e mitigações

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| {risco 1} | high | {como mitigar} |
| {risco 2} | medium | {como mitigar} |
| ... | ... | ... |

## Checklist antes de rodar `/gsd:bootstrap`

- [ ] specs/project.yaml preenchido
- [ ] specs/stack.yaml preenchido
- [ ] specs/rules.yaml com ≥3 regras
- [ ] specs/database.yaml (se tem DB)
- [ ] docs/identidade-visual/tokens.json (se tem UI)
- [ ] docs/identidade-visual/brand.md (se tem UI)
- [ ] ADRs principais documentadas em docs/adrs/
- [ ] Este project-brief.md revisado pelo owner
```

**Critério de pronto:**
- Todas as 12 seções preenchidas
- Sem `[a definir]` em seções 1, 2, 4, 6, 8 (são fundamentais)
- Roadmap (seção 7) com pelo menos 3 releases
- Mínimo 3 princípios invioláveis (seção 8)
- Mínimo 3 fases (seção 10)
- Mínimo 3 riscos (seção 12)

---

### 6.6 `docs/identidade-visual/tokens.json` (obrigatório se has_ui)

```json
{
  "_meta": {
    "mode": "{provisional | final}",
    "note": "Direção visual {definitiva | aguarda designer}",
    "last_updated": "{YYYY-MM-DD}"
  },
  "color": {
    "brand": {
      "50":  { "value": "#xxxxxx" },
      "500": { "value": "#xxxxxx", "note": "primary" },
      "600": { "value": "#xxxxxx" },
      "900": { "value": "#xxxxxx" }
    },
    "text": {
      "primary":   { "value": "#111827" },
      "secondary": { "value": "#6b7280" },
      "disabled":  { "value": "#9ca3af" },
      "inverse":   { "value": "#ffffff" }
    },
    "surface": {
      "default":  { "value": "#ffffff" },
      "elevated": { "value": "#f9fafb" }
    },
    "border": {
      "default": { "value": "#e5e7eb" }
    },
    "semantic": {
      "success": { "value": "#10b981" },
      "warning": { "value": "#f59e0b" },
      "danger":  { "value": "#ef4444" },
      "info":    { "value": "#3b82f6" }
    }
  },
  "space": {
    "xs":  { "value": "4px" },
    "sm":  { "value": "8px" },
    "md":  { "value": "16px" },
    "lg":  { "value": "24px" },
    "xl":  { "value": "32px" },
    "2xl": { "value": "48px" }
  },
  "radius": {
    "sm":   { "value": "4px" },
    "md":   { "value": "8px" },
    "lg":   { "value": "12px" },
    "full": { "value": "9999px" }
  },
  "typography": {
    "family": {
      "sans": { "value": "Inter, system-ui, sans-serif" },
      "mono": { "value": "JetBrains Mono, monospace" }
    },
    "size": {
      "xs":   { "value": "12px" },
      "sm":   { "value": "14px" },
      "base": { "value": "16px" },
      "lg":   { "value": "18px" },
      "xl":   { "value": "24px" },
      "2xl":  { "value": "32px" }
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
    }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px rgba(0,0,0,0.05)" },
    "md": { "value": "0 4px 6px rgba(0,0,0,0.1)" },
    "lg": { "value": "0 10px 15px rgba(0,0,0,0.1)" }
  }
}
```

**Critério de pronto:**
- Mínimo: `color.brand.500`, `color.text.primary`, `color.surface.default`, `color.border.default`, `color.semantic.{success,warning,danger}`, `space.{xs,sm,md,lg}`
- Modo `provisional` aceita campos vazios; `final` exige completude
- Sem hex repetidos em categorias semânticas diferentes (sem confundir brand com semantic)

---

### 6.7 `docs/identidade-visual/brand.md` (recomendado se has_ui)

```markdown
# Brand — {Nome do Projeto}

> Voz, tom e vocabulário canônico. Usar em toda copy (UI, email, landing).

## Voz da marca

**É:** {3-5 adjetivos: ex: direta, calibrada, brasileira}
**NÃO é:** {3-5 adjetivos: ex: corporativa engessada, hype de IA, mística}

## Tom por contexto

| Contexto | Tom | Exemplo bom | Exemplo ruim |
|----------|-----|-------------|--------------|
| Hero/landing | ... | ... | ... |
| Onboarding | ... | ... | ... |
| CTA primária | ... | "{verbo + substantivo concreto}" | "{evitar}" |
| Erro recuperável | ... | ... | ... |
| Erro grave | ... | ... | ... |
| Empty state | ... | ... | ... |
| Confirmação | ... | ... | ... |

## Vocabulário canônico

### Usar
- {palavra} (não {sinônimo}) — {por quê}
- ...

### Evitar
- {palavra ruim} → {alternativa}
- ...

### Números e formatos
- Valores: "R$ 1.234,56" (ponto de milhar, vírgula decimal)
- Percentuais: "82%" (sem espaço antes)
- Datas: "{formato em UI vs logs}"

## Gramática e estilo

- Tratamento: {você | tu | senhor}
- Voz: {ativa | passiva}
- Frases curtas em {CTA, hero}: máximo {N} palavras
- {Outras regras de estilo}

## Acessibilidade de copy

- Linguagem nível {ensino fundamental | médio | técnico}
- {Regras específicas}

## Checklist de copy

- [ ] Não usa palavras do vocabulário "Evitar"
- [ ] Tom bate com tabela "Tom por contexto"
- [ ] Sem certezas absolutas ("100%", "sempre")
- [ ] Números formatados corretamente
- [ ] CTAs com verbo + substantivo
```

**Critério de pronto:**
- 5+ contextos na tabela de tom
- Mínimo 5 termos no vocabulário "Usar" e 5 no "Evitar"
- Regras de tratamento e voz definidas

---

### 6.8 `docs/identidade-visual/INDEX.md`

```markdown
# docs/identidade-visual/ — INDEX

> Sistema visual e de voz do {projeto}. Sprints com `has_ui: true` consultam.

## Arquivos canônicos

- `tokens.json` — design tokens (status: {provisional | final})
- `brand.md` — voz, tom, vocabulário
- `INDEX.md` — este arquivo

## A criar conforme sprints avançam

- `design-system.md` — documentação humana dos componentes (cresce sprint a sprint)
- `wireframes/` — wireframes (v0.dev, Lovable, Figma)
- `mockups/` — mockups finais por tela
- `logo/` — variações do logo

## Última revisão: {YYYY-MM-DD}
```

---

### 6.9 `docs/INDEX.md`

```markdown
# docs/ — INDEX

> Documentação canônica do {projeto}. Leia em ordem ao chegar.

## Ordem de leitura

1. `project-brief.md` — fonte de verdade do projeto
2. `adrs/` — decisões arquiteturais
3. `identidade-visual/brand.md` — voz e tom
4. Demais subpastas conforme contexto

## Subpastas

- `adrs/` — ADRs (decisões arquiteturais)
- `identidade-visual/` — tokens, brand (se projeto tem UI)
- `archaeology/` — arqueologia (se projeto legado)
- `business/` — pitch, SWOT (se houver)
- `research/` — pesquisa, concorrentes (se houver)
- `post-mortems/` — TEMPLATE.md + post-mortems gerados

## Última revisão: {YYYY-MM-DD}
```

---

### 6.10 `docs/adrs/ADR-NNN-{slug}.md`

Para **cada decisão arquitetural fechada** mencionada na discussão:

```markdown
# ADR-{NNN}: {Título da decisão}

## Status

{Accepted | Proposed | Superseded by ADR-XXX}

## Contexto

{Que problema motivou essa decisão? Qual era o estado antes?}

## Decisão

{O que foi decidido. 1-3 parágrafos.}

## Consequências

### Positivas
- {benefício 1}
- {benefício 2}

### Negativas
- {tradeoff 1}
- {tradeoff 2}

### Dívida técnica resultante
- {se houver, ID em TECH-DEBT.md futuro}

## Alternativas consideradas

### {Alternativa A}
{Por que foi rejeitada}

### {Alternativa B}
{Por que foi rejeitada}

## Data
{YYYY-MM-DD}
```

**Quando criar ADR:** sempre que durante a discussão o humano disser:
- "Já decidi que vai ser X" (decisão tomada)
- "Considerei Y mas escolhi X porque..." (com tradeoff)
- "Não vai ser X de jeito nenhum" (decisão negativa)

**Quando NÃO criar ADR:**
- Stack default sem deliberação ("vou usar Postgres porque é o que conheço") → vira `stack.yaml`, não ADR
- Decisão futura ainda não tomada → não é ADR ainda

---

## 7. PROMPTS PRONTOS PARA SITUAÇÕES COMUNS

### 7.1 Iniciar a sessão (Claude diz ao humano)

```
Vou conduzir uma sessão de descoberta do seu projeto seguindo o
GUIA-DESCOBERTA-NOVO-PROJETO.md.

A sessão tem 4 fases:
1. Aquecimento (5 min)
2. Descoberta em 7 blocos (45-90 min, com pausas para validar)
3. Validação consolidada (15 min)
4. Geração dos arquivos canônicos (30-60 min)

Ao final, você terá pronto:
- specs/project.yaml, stack.yaml, rules.yaml, database.yaml
- docs/project-brief.md
- docs/identidade-visual/{tokens.json, brand.md, INDEX.md} (se tem UI)
- docs/adrs/ (uma ADR por decisão fechada)
- docs/INDEX.md

Esses são os arquivos exatos que /gsd:bootstrap precisa para gerar
seu .planning/ inicial com qualidade.

Antes de começar, me confirma:
1. É projeto comercial/produto ou interno/ferramenta?
2. Já existe algum documento sobre ele que eu deveria ler primeiro?
3. As principais decisões técnicas já estão tomadas?
```

### 7.2 Forçar especificidade quando humano vagueia

```
Você disse {citar exatamente}. Preciso de mais especificidade aqui
porque {qual seção do output isso afeta}. Pode dar um exemplo
concreto ou descrever em 2-3 linhas?

Se ainda não decidiu, anoto como "[a definir]" e seguimos. Mas
campos críticos (usuário primário, KPI, MVP scope) precisam de
resposta antes de gerar arquivos.
```

### 7.3 Detectar buraco crítico

```
Identifiquei um buraco crítico antes de gerar arquivos:

{descrever buraco específico — ex: "MVP scope tem 18 features
para 4 meses solo dev = irrealista"}

Vamos resolver isso agora porque se eu deixar passar:
- {consequência 1 no roadmap gerado}
- {consequência 2}

Como prefere atacar:
A) {opção concreta}
B) {opção concreta}
C) {opção concreta}
```

### 7.4 Validação antes de gerar

```
Vou consolidar tudo que captei. Por favor confirma item por item:

**Identidade:**
- Nome: {X}
- Tipo: {SaaS B2B | App B2C | ...}

**Usuário primário:**
- {Resumo em 2 linhas}

**Modelo de negócio:**
- {Como monetiza}
- {Meta primária}

**Stack:**
- Backend: {X versão Y}
- Frontend: {X versão Y}
- DB: {X versão Y}

**Escopo MVP:**
- {Lista das features}

**FORA de escopo:**
- {Lista}

**Riscos top 3:**
- {Lista}

Confirma? Algo errado, faltando ou incompleto?
```

### 7.5 Antes de cada arquivo gerado

```
Vou gerar agora `{caminho/arquivo.ext}`.

Vai conter:
- {3-5 bullets do que vai dentro}

Baseado em: {bloco da discussão que originou}

Pronto pra eu escrever?
```

### 7.6 Ao final da sessão

```
Sessão de descoberta concluída.

Arquivos gerados:
✓ specs/project.yaml ({N} linhas)
✓ specs/stack.yaml ({N} linhas)
✓ specs/rules.yaml ({N} regras)
{✓ ou —} specs/database.yaml ({N} tabelas, ou "não aplicável — sem DB")
✓ docs/project-brief.md ({N} linhas)
{✓ ou —} docs/identidade-visual/tokens.json
{✓ ou —} docs/identidade-visual/brand.md
✓ docs/identidade-visual/INDEX.md
✓ docs/INDEX.md
✓ docs/adrs/ ({N} ADRs criados)

Próximo passo:
1. git add docs/ specs/
2. git commit -m "docs: especificação inicial do projeto"
3. /gsd:bootstrap

O bootstrap vai ler todos esses arquivos e gerar:
- .planning/PROJECT.md (consolida tudo)
- .planning/ROADMAP.md (milestones derivados do roadmap do brief)
- .planning/STATE.md (estado zero)
- .planning/REQUIREMENTS.md, MILESTONES.md, DECISIONS.md
```

---

## 8. CHECKLIST DE QUALIDADE (rodar antes de finalizar sessão)

Antes de declarar "pronto para `/gsd:bootstrap`", verifique cada item:

### project.yaml

- [ ] `name`, `codename`, `type`, `locale` preenchidos
- [ ] `codename` em kebab-case válido
- [ ] `owner.email` é email real
- [ ] `team.size` ≥ 1
- [ ] `timeline.mvp_target_months` é número (não "alguns")

### stack.yaml

- [ ] Versões travadas (ex: "3.13", não "latest")
- [ ] Sem stack ambígua ("python ou nodejs" → escolher um)
- [ ] Campos não-aplicáveis explicitamente `null`
- [ ] Coerência interna (se `frontend_mobile.framework: ionic`, então `frontend_mobile.wrapper: capacitor`)

### project-brief.md

- [ ] 12 seções todas preenchidas
- [ ] Seção 4 tem usuário primário concreto (não "todo mundo")
- [ ] Seção 7 tem ≥3 releases
- [ ] Seção 8 tem ≥3 princípios invioláveis
- [ ] Seção 10 tem ≥3 fases com duração estimada
- [ ] Seção 12 tem ≥3 riscos com mitigação

### rules.yaml (se gerado)

- [ ] ≥3 regras `criticality: high`
- [ ] Cada regra com `id`, `description`, `criticality`, `rationale`, `enforcement`
- [ ] IDs sequenciais: R-001, R-002, ...

### tokens.json (se has_ui)

- [ ] `_meta.mode` é `provisional` ou `final`
- [ ] `color.brand.500` definido
- [ ] `color.text.primary` e `color.surface.default` definidos
- [ ] `color.semantic.{success,warning,danger}` definidos
- [ ] `space` tem ≥4 escalas

### brand.md (se has_ui)

- [ ] Voz definida (é / não é, com 3-5 adjetivos cada)
- [ ] Tabela de tom com ≥5 contextos
- [ ] Vocabulário com ≥5 "usar" e ≥5 "evitar"

### ADRs (se houver decisões fechadas)

- [ ] Uma ADR por decisão arquitetural definitiva
- [ ] Cada ADR tem Contexto, Decisão, Consequências, Alternativas
- [ ] Status `Accepted`

---

## 9. ANTI-PATTERNS DA SESSÃO (evitar)

**Don't 1:** Pular validação de bloco e ir direto pro próximo
→ Humano cansa, decisões ficam mal formadas, arquivos saem ruins.

**Don't 2:** Inventar resposta quando humano não sabe
→ Anote `[a definir]`. Bootstrap vai destacar o que falta.

**Don't 3:** Gerar todos os arquivos de uma vez no fim
→ Gere um por vez, valide um por vez. Arquivos consolidados saem inconsistentes.

**Don't 4:** Deixar "todo mundo" como usuário-alvo
→ Bloqueie geração até humano definir. Produto sem alvo claro vira escopo infinito no roadmap.

**Don't 5:** Aceitar stack ambígua ("vamos ver", "talvez X ou Y")
→ Force decisão antes do `stack.yaml`. Roadmap depende disso.

**Don't 6:** Escrever ADR para decisão default sem deliberação
→ ADRs são para decisões com tradeoff considerado. "Vou usar Postgres porque é o que conheço" não é ADR.

**Don't 7:** Forçar todos os 10 arquivos em projeto pequeno
→ Para ferramenta interna simples, os 3 obrigatórios + brand.md já bastam. Não infle output.

---

## 10. INTEGRAÇÃO COM `/gsd:bootstrap`

Após sessão concluída e arquivos commitados:

```
/gsd:bootstrap
```

O que o bootstrap vai fazer com seus arquivos:

1. **Lê** `docs/project-brief.md`, `specs/project.yaml`, `specs/stack.yaml` (obrigatórios)
2. **Aproveita** se existirem: `specs/database.yaml`, `specs/rules.yaml`, `docs/adrs/`, `docs/identidade-visual/`
3. **Apresenta síntese** consolidada para humano validar
4. **Pergunta** strategy de slicing (`vertical_value` ou `admin_first`), orchestrator mode, `visual_tokens_mode`
5. **Gera** `.planning/PROJECT.md`, `ROADMAP.md`, `STATE.md`, `REQUIREMENTS.md`, `MILESTONES.md`, `DECISIONS.md`

**Se bootstrap reclamar de campo faltando** ou inconsistência:
- Volte ao arquivo correspondente, corrija
- Rode `/gsd:bootstrap` de novo
- O bootstrap é idempotente até `.planning/STATE.md` ter progresso real

**Depois do bootstrap, próximo passo:**

```
/gsd:autopilot v1.0      # roda primeiro milestone end-to-end
```

Ou modo conservador:

```
/gsd:plan-phase 1
/gsd:execute-phase 1
/gsd:verify-work 1
```

---

## 11. RESUMO EM UMA TELA

**Manual em 10 linhas:**

1. Saúde o humano e explique o protocolo (Fase 1)
2. Conduza descoberta em 7 blocos, uma pergunta por vez (Fase 2)
3. Resuma e valide tudo (Fase 3)
4. Gere arquivos um por um, na ordem: project.yaml → stack.yaml → rules.yaml → database.yaml → project-brief.md → tokens.json → brand.md → INDEX.md → ADRs (Fase 4)
5. Cada arquivo: anuncie, gere com template, valide com humano, escreva no disco
6. Rode checklist de qualidade (seção 8)
7. Sugira commit
8. Aponte para `/gsd:bootstrap` como próximo passo

**Sucesso da sessão = humano consegue rodar `/gsd:bootstrap` sem erros e gerar `.planning/` coerente.**

Falha = humano roda bootstrap e bootstrap reclama de arquivo ausente, ou roadmap gerado é tão genérico que humano vai precisar editar à mão.
