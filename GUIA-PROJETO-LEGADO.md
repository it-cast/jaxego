# GUIA — Projeto Legado em Produção

**Quando usar este documento:** você tem um projeto **já em produção** (construído antes de conhecer o framework) e quer adotar o framework **apenas para ajustes e features novas**, sem refatorar o código existente.

**Tempo estimado total:** 12-20 horas espalhadas em 2-3 semanas. Não é para ser feito de uma vez.

**O que o framework VAI fazer no seu projeto legado:**
- Disciplinar código novo que você vai adicionar daqui pra frente
- Documentar o que já existe (via arqueologia) para gerar base de contexto
- Capturar incidentes e hotfixes em memória institucional
- Expor dívida técnica já existente de forma visível

**O que o framework NÃO vai fazer:**
- Refatorar código existente
- Migrar stack
- Criar testes retroativos
- Corrigir bugs legados
- Funcionar sem sua revisão humana da arqueologia

---

## ORDEM DE EXECUÇÃO

```
FASE 1: Instalar framework no projeto existente (20 min)
FASE 2: Arqueologia do código (4-8h, espalhadas)
FASE 3: Consolidar docs canônicos (2-3h, você revisando)
FASE 4: Bootstrap em modo adoção (1h)
FASE 5: Configurar para conviver com código legado (30 min)
FASE 6: Primeiro ajuste pelo framework (30 min a 2h)
FASE 7: Hotfix retrospectivo (30 min, quando acontecer)
FASE 8: Ciclo contínuo misto (contínuo)
```

---

## FASE 1 — Instalar framework no projeto existente (20 min)

### Passo 1.1 — Entender o que você tem

```bash
cd ~/projetos/seu-projeto-legado
ls -la
git log --oneline | head -20
```

Confira que você está no diretório raiz do projeto, com git inicializado.

### Passo 1.2 — Backup de segurança

```bash
git checkout -b adocao-framework-gsd
```

Trabalhar em branch separado. Se der errado, volta pro main sem prejuízo.

### Passo 1.3 — Instalar APENAS as partes necessárias

**Não descompacte o framework inteiro por cima do seu projeto.** Copie só o que precisa:

```bash
# Descompactar em /tmp primeiro
unzip ~/Downloads/gsd-framework.zip -d /tmp/

# Copiar APENAS as pastas do framework para seu projeto
cp -r /tmp/gsd-framework/.claude ./.claude
cp -r /tmp/gsd-framework/bin ./bin
cp -r /tmp/gsd-framework/tests ./tests

# Copiar docs do framework (não docs do projeto)
cp /tmp/gsd-framework/CLAUDE.md .
cp /tmp/gsd-framework/FRAMEWORK-STATUS.md .
cp /tmp/gsd-framework/TUTORIAL-COMPLETO.md .
cp /tmp/gsd-framework/INSTALLATION.md .
cp /tmp/gsd-framework/GUIA-PROJETO-NOVO.md .
cp /tmp/gsd-framework/GUIA-PROJETO-LEGADO.md .

# Criar estrutura onde docs do projeto vão morar
mkdir -p docs/adrs docs/identidade-visual docs/archaeology
mkdir -p specs
mkdir -p .planning
```

### Passo 1.4 — Atualizar `.gitignore`

Adicione ao seu `.gitignore` existente:

```
# gsd-framework
.claude/get-shit-done/bin/**/*.log
.planning/exports/*.json
/tmp/
```

### Passo 1.5 — Permissões

```bash
chmod +x bin/*.sh
chmod +x .claude/hooks/*.sh
chmod +x .claude/get-shit-done/bin/*.cjs 2>/dev/null || true
```

### Passo 1.6 — Validar

```bash
bash tests/framework/run-all.sh
```

Esperado: `11/11 suites passed`. Testa integridade do framework, não do seu projeto.

### Passo 1.7 — Commit

```bash
git add .
git commit -m "chore: adota gsd-framework v0.9.4 (modo legado)"
```

---

## FASE 2 — Arqueologia do código (4-8h, espalhadas)

**Este é o coração da adoção em projeto legado.** Você vai fazer Claude **reverse-engineer** seu projeto e gerar documentação que vai virar a base de conhecimento.

**Importante:** divida em múltiplas sessões. Não tente fazer tudo num dia. Qualidade > velocidade aqui.

### Passo 2.1 — Abrir Claude Code

```bash
claude
```

### Passo 2.2 — Prompt de validação inicial

Mesmo prompt do projeto novo — estabelece padrão:

```
Vou adotar o gsd-framework v0.9.4 em um projeto LEGADO em produção.
Antes de qualquer coisa:

1. Leia CLAUDE.md integralmente
2. Leia FRAMEWORK-STATUS.md — especialmente "O que esta versão NÃO resolve"
3. Leia GUIA-PROJETO-LEGADO.md (este arquivo)
4. Me confirme explicitamente:
   - "li todos os 3 arquivos"
   - "entendi que este é projeto legado, não novo"
   - "entendi que NÃO vou refatorar código existente"
   - "entendi que vou fazer arqueologia primeiro, depois bootstrap"

Só prossiga após eu confirmar.
```

### Passo 2.3 — Inventário estrutural (sessão 1, 30 min)

**Prompt:**

```
Vou fazer arqueologia deste projeto. PRIMEIRA FASE: inventário 
estrutural. Não analise conteúdo ainda.

Faça:
1. Árvore de pastas até profundidade 3, ignorando node_modules, 
   .git, dist, build, vendor, __pycache__, .venv, .claude

2. Para cada pasta principal, uma frase descrevendo propósito 
   inferido pelo nome e arquivos superficiais (NÃO abra código ainda)

3. Conte arquivos por extensão (quantos .py, .js, .ts, .html, etc.)

4. Liste arquivos de configuração na raiz SEM ABRIR:
   - package.json, composer.json, pyproject.toml, requirements.txt
   - Dockerfile, docker-compose.yml
   - .env.example, .env.sample
   - CI configs (.github/workflows/, .gitlab-ci.yml)

5. Liste tamanho total de linhas de código por linguagem

6. Me pergunte: quais áreas do projeto você quer que eu priorize 
   na análise profunda? Backend/Frontend/Database/Infra?
```

**Você responde** priorizando. Exemplo:
```
Priorize:
1. Backend (crítico — API em produção)
2. Database (importante documentar schema)
3. Frontend (análise superficial — time frontend vai fazer parte depois)
4. Infra (média prioridade)
```

### Passo 2.4 — Stack e dependências (sessão 1, 30 min)

**Prompt:**

```
Agora abra os arquivos de configuração da raiz e extraia:

1. Linguagens + versões (detectar por configs, não por palpite)
2. Frameworks + versões (travados ou com ^)
3. Banco(s) de dados (engine + versão)
4. Cache, queue, storage
5. Build tools, test runners, linters configurados
6. Dependências críticas (versões travadas = decisão arquitetural)
7. Configurações de deploy
8. Variáveis de ambiente esperadas (listar todas do .env.example)

Gere specs/stack.yaml com os dados reais.

Se algum campo for dúbio, escreva "a confirmar: <por quê>" — NÃO INVENTE.
```

**Revise o stack.yaml gerado.** Corrija se Claude inferiu errado. Commit:

```bash
git add specs/stack.yaml
git commit -m "docs: extrai stack real do projeto legado"
```

### Passo 2.5 — Arqueologia do Backend (sessão 2, 1-2h)

**Prompt:**

```
SEGUNDA FASE: arqueologia do backend em ~/backend/ (ou caminho 
equivalente do seu projeto — adapte).

Produza docs/archaeology/BACKEND.md com estas seções:

1. **Estrutura geral**
   - Padrão de organização (MVC, domain-driven, layered, clean arch?)
   - Pastas principais e responsabilidade

2. **Endpoints** (liste TODOS)
   Para cada um:
   - Método HTTP e rota completa
   - Nome do handler/função + arquivo:linha
   - Descrição inferida do que faz (baseada em nome e código)
   - Auth requerida? (detectar decorators, middlewares)
   - DTOs/schemas de input e output se existirem

3. **Models/entidades**
   - Nome, tabela associada
   - Campos principais e tipos
   - Relacionamentos

4. **Services/use-cases** (camada de lógica de negócio)
   - Principais classes/funções
   - Responsabilidade

5. **Integrações externas**
   - APIs chamadas (procure por URLs, clients HTTP)
   - Webhooks recebidos
   - SDKs usados

6. **Jobs assíncronos**
   - Celery tasks, cron, schedulers
   - Frequência inferida

7. **Autenticação e autorização**
   - Como está implementada
   - Onde está o middleware/decorator

8. **Anti-patterns detectados**
   - N+1 queries, senha em plaintext, raw SQL com input de usuário, 
     try/except bare, etc.
   - Máximo 10 itens, com arquivo:linha

9. **TODOs e FIXMEs no código**
   - Liste literalmente com path:linha

REGRAS:
- Se arquivo é grande (>500 linhas), faça sumário, não análise linha 
  por linha
- Se lógica é complexa, escreva "lógica complexa — revisar manualmente"
- Se não conseguir entender, escreva "a confirmar: <pergunta>"
- NÃO fale sobre frontend, database ou infra agora
- NÃO proponha refatoração
- NÃO invente descrições para código que você não entendeu
```

**Revise o BACKEND.md gerado.** É aqui que você precisa ser crítico. Claude vai:
- Inferir coisas erradas — você corrige
- Omitir decisões não-óbvias — você adiciona contexto
- Inventar justificativas — você deleta

Essa revisão toma 1-2 horas. É investimento único.

### Passo 2.6 — Arqueologia do Database (sessão 3, 30-60 min)

**Prompt:**

```
TERCEIRA FASE: arqueologia do banco de dados.

Fontes possíveis (use o que tiver):
- migrations/ ou alembic/ ou prisma/
- schema.sql ou schema.prisma ou similar
- Models do ORM (se projeto usa SQLAlchemy, Prisma, Hibernate, etc.)

Produza:

1. docs/archaeology/DATABASE.md com:
   - Lista de tabelas (nome, descrição)
   - Para cada tabela: colunas com tipos, PK, FKs, indexes, constraints
   - Relacionamentos em texto narrativo
   - Triggers, stored procedures, views (se detectar)
   - Evolução cronológica das migrations
   - Tabelas grandes suspeitas (por volume de migrations afetando)

2. specs/database.yaml com os mesmos dados em formato estruturado 
   YAML (igual template do framework)

3. Seção "Suspeitas" no DATABASE.md:
   - Colunas sem índice que parecem ser usadas em WHERE
   - FKs sem ON DELETE/UPDATE definido
   - Campos potencialmente desnecessários (nunca referenciados)
   - Nomes inconsistentes (snake_case misturado com camelCase)

Se não conseguir acessar DB real, use só migrations/schema. 
Marque "sem acesso a DB real — baseado em migrations apenas".
```

**Revise.** Commit:

```bash
git add docs/archaeology/DATABASE.md specs/database.yaml
git commit -m "docs: arqueologia do banco de dados"
```

### Passo 2.7 — Arqueologia do Frontend (sessão 4, 1-2h)

**Prompt:**

```
QUARTA FASE: arqueologia do frontend em ~/frontend/ ou caminho 
equivalente.

Produza docs/archaeology/FRONTEND.md com:

1. **Stack efetiva detectada**
   - Framework + versão
   - State management (Redux, NgRx, Pinia, Zustand, Context?)
   - Roteador
   - UI kit (Material, Tailwind, Bootstrap, shadcn, Ionic?)
   - Build tool (webpack, vite, turbopack?)

2. **Rotas/páginas**
   - Caminho da rota + componente
   - O que a página faz (baseado em nome e imports)
   - Auth requerida?

3. **Componentes principais**
   - Componentes usados em 3+ lugares
   - Localização, API de props

4. **Design system de fato**
   - Existe tokens.json, tokens.ts, theme.ts?
   - Cores hardcoded: QUANTOS hex únicos existem no código?
     (rode: grep -rhoE "#[0-9a-fA-F]{3,8}" src/ | sort | uniq -c | wc -l)
   - Fontes usadas
   - Espaçamentos hardcoded (px, rem soltos)

5. **Integração com backend**
   - Como chama API (fetch, axios, TanStack Query?)
   - Onde está autenticação armazenada (localStorage, cookie, memória?)
   - Interceptors, middlewares de request

6. **Internacionalização**
   - Existe? Em que línguas? Onde ficam os arquivos de tradução?

7. **Acessibilidade**
   - aria-labels consistentes?
   - Há testes de acessibilidade?
   - Skip links, landmark roles?

8. **Assets**
   - Ícones (biblioteca ou SVG próprio?)
   - Fontes (Google Fonts, arquivo próprio?)
   - Imagens (onde ficam, como otimizadas)

9. **Build e deploy**
   - Script de build de produção
   - Tamanho do bundle principal (se conseguir inferir)

Mesmas regras: não invente, marque dúvidas, não fale sobre backend.
```

### Passo 2.8 — Arqueologia de Infra (sessão 5, 30-60 min)

**Prompt:**

```
QUINTA FASE: arqueologia de infra e deploy.

Analise Dockerfile, docker-compose.yml, .github/workflows/, 
scripts de deploy, configs de produção.

Produza docs/archaeology/INFRA.md com:

1. **Containers**
   - Imagens base usadas (alpine? slim? distroless?)
   - Volumes, redes, portas expostas
   - Variáveis de ambiente de produção

2. **Pipeline CI/CD**
   - Gatilhos (push, PR, tag?)
   - Jobs e stages
   - Secrets esperados

3. **Ambientes**
   - Dev, staging, prod diferenciados?
   - Configs por ambiente

4. **Observabilidade configurada**
   - Logging (formato, destino)
   - Metrics (prometheus, datadog?)
   - Error tracking (sentry, bugsnag?)
   - APM?

5. **Secrets management**
   - .env file, vault, AWS secrets manager?
   - Como são injetados em produção?

6. **Backups**
   - Configurados? Frequência? Onde guardados?

7. **Disaster recovery**
   - Runbook existe? Testado?

Regras: não invente, marque dúvidas.
```

### Passo 2.9 — Regras de negócio implícitas (sessão 6, 1h)

**Esta é a fase mais valiosa e mais difícil.** Prompt:

```
SEXTA FASE: extrair REGRAS DE NEGÓCIO implícitas do código.

Com base em BACKEND.md e FRONTEND.md gerados antes, identifique 
regras de negócio implementadas em código mas não documentadas. 
Exemplos:
- "Usuário só pode criar pedido se email verificado"
- "Comissão padrão é 10%, exceção para plano premium"
- "CEP precisa começar com dígito válido do estado"
- "Desconto máximo é 30% do valor do pedido"

Procure em:
1. Validações em controllers/services (if/else com mensagens de erro)
2. Middlewares de autorização
3. Guards de frontend
4. Triggers de banco se houver
5. Jobs que rodam baseado em condição
6. Webhooks com lógica condicional

Gere docs/archaeology/BUSINESS-RULES.md com formato tabular:

| ID | Regra | Onde implementada (arquivo:linha) | Criticidade | Dúvida |
|----|-------|-----------------------------------|-------------|--------|

Critérios para criticidade:
- HIGH: regra financeira, fiscal, ou que bloqueia fluxo do usuário
- MEDIUM: regra operacional importante mas não crítica
- LOW: regra de conveniência ou UX

Se não tiver certeza, marque "Dúvida: sim" e explique o que confundiu.

Liste até 50 regras. Se houver mais, marque "análise parcial — 
regras adicionais aguardam revisão manual".
```

**Você revisa este documento carefully.** Esse é o material bruto que vai virar `specs/rules.yaml`. Regras de negócio mal documentadas são a principal causa de bugs depois de refatoração ou de entrada de dev novo no time.

Commit:

```bash
git add docs/archaeology/
git commit -m "docs: arqueologia completa do projeto"
```

---

## FASE 3 — Consolidar docs canônicos (2-3h, você revisando)

Agora você tem 5-6 arquivos em `docs/archaeology/`. Hora de gerar os canônicos do framework a partir deles.

### Passo 3.1 — Gerar `project-brief.md`

**Prompt:**

```
Com base em tudo que foi documentado em docs/archaeology/, gere 
um rascunho de docs/project-brief.md seguindo as 12 seções do 
template padrão do framework.

MODIFICAÇÕES IMPORTANTES para projeto legado:
- Adicione SEÇÃO 0 antes da 1 chamada "Status atual em produção":
  - Desde quando está em produção
  - Volume estimado de usuários/uso
  - Features principais já entregues (lista curta)

- Na SEÇÃO 7 (Escopo MVP):
  - Subtítulo "Já entregue" listando features em produção
  - Subtítulo "Planejado" listando o que ainda falta
  
- Na SEÇÃO 11 (Decisões tomadas):
  - Gere ADRs retroativos a partir de docs/archaeology/
  - Uma linha por decisão arquitetural detectada

REGRAS:
- Não invente. Onde faltar info, deixe "[a preencher pelo humano]"
- Baseie-se APENAS em docs/archaeology/ e código — não em suposições
- Priorize honestidade sobre completude
```

**Revise e complete os `[a preencher]`.** Este é o documento mais importante do projeto.

### Passo 3.2 — Gerar ADRs retroativos

**Prompt:**

```
Com base em docs/archaeology/, identifique as 5-10 decisões 
arquiteturais mais importantes que foram tomadas ao longo do 
projeto mas nunca documentadas. Exemplos típicos:
- Escolha de stack (linguagem, framework, DB)
- Autenticação (JWT vs session, localStorage vs httpOnly cookie)
- Organização de código (monolith vs modular)
- Cache strategy
- Escolha de PSP, storage provider, etc.

Para cada uma, gere docs/adrs/ADR-XXX-<slug>.md seguindo template:

---
# ADR-XXX: <título>

## Status
Retroativo — decisão tomada em [data inferida] mas documentada em [hoje]

## Contexto
<o que motivou a decisão, inferido pelo código>

## Decisão
<o que foi decidido>

## Consequências
### Positivas
- ...
### Negativas
- ...
### Dívida técnica resultante
- [ID da entrada em TECH-DEBT.md]

## Alternativas consideradas
<se conseguir inferir>
---

Numere ADRs em ordem cronológica provável das migrations.
Se não conseguir inferir contexto/alternativas, escreva 
"Contexto histórico não disponível — preencher com quem tomou 
a decisão".
```

Revise cada ADR. Converse com quem tomou as decisões se ainda tiver contato. Commit:

```bash
git add docs/adrs/
git commit -m "docs: ADRs retroativos das principais decisões arquiteturais"
```

### Passo 3.3 — Gerar `specs/rules.yaml`

**Prompt:**

```
Com base em docs/archaeology/BUSINESS-RULES.md (revisado por mim), 
gere specs/rules.yaml canônico no formato do framework.

Inclua TODAS as regras marcadas como HIGH e MEDIUM.
Deixe LOW como "rules_minor" separadas.
Para regras com dúvida, marque campo "pending_review: true".
```

### Passo 3.4 — Preencher identidade visual (se tem UI)

**Prompt:**

```
Escaneie todos os arquivos .css, .scss, .less do frontend e:

1. Extraia TODAS as cores únicas em hex/rgb/hsl
2. Agrupe cores similares (diferença <5% RGB) e me mostre
3. Sugira nomes semânticos:
   - Cor mais usada em botões primários → brand/500
   - Cor mais usada em texto → text/primary
   - Branco/fundo → surface/default
   - Cinzas de borda → border/default
4. Gere docs/identidade-visual/tokens.json com as cores extraídas 
   + nomes semânticos
5. Liste em .planning/TECH-DEBT.md:
   - Quantos hex hardcoded existem e onde (grep count por arquivo)
   - Marque como "Dívida técnica: migrar hex para tokens"
   - Prioridade: LOW (dívida gradual, não bloqueante)

NÃO refatore CSS existente. Só extraia e documente.
```

**Revise tokens.json.** Se a extração deu nomes ruins, ajuste. Gere `brand.md` manualmente descrevendo voz/tom do produto existente.

Commit:

```bash
git add docs/identidade-visual/ .planning/TECH-DEBT.md
git commit -m "docs: identidade visual extraída do código existente"
```

---

## FASE 4 — Bootstrap em modo adoção (1h)

Agora o framework tem contexto suficiente para o bootstrap funcionar bem.

### Passo 4.1 — Prompt de bootstrap modificado

Em vez de `/gsd:bootstrap` direto, use este prompt para que o Claude entenda que é adoção em legado:

```
Vou rodar /gsd:bootstrap agora. Contexto crítico:

1. Este projeto JÁ EXISTE e está em produção
2. Você tem docs/archaeology/ com toda arqueologia feita
3. Você tem docs/adrs/ com ADRs retroativos
4. Você tem specs/*.yaml preenchidos com realidade
5. Você tem docs/identidade-visual/tokens.json extraído do código

Ao gerar .planning/ROADMAP.md:
- Divida em 2 seções: "Milestones já concluídos" (histórico) e 
  "Milestones futuros" (daqui pra frente)
- Milestones históricos: marque status COMPLETE, baseie-se em 
  docs/archaeology/BUSINESS-RULES.md + features em project-brief
- Milestones futuros: baseie-se no "Planejado" do project-brief

Ao gerar .planning/STATE.md:
- Marque current_phase como "adocao-framework"
- Não tente reconstruir estado de sprints passados

NÃO PROPONHA:
- Refatoração do código existente como sprint
- Migração de stack
- "Sprint 0 de setup" (já está em produção há anos)

Confirme que entendeu esses pontos antes de executar /gsd:bootstrap.
```

### Passo 4.2 — Executar bootstrap

Após confirmação:

```
/gsd:bootstrap
```

Responder perguntas:

- **Strategy de slicing:** geralmente `vertical_value` para projeto legado (features novas que entregam valor incremental)
- **Orchestrator mode:** `2` (inline) — conservador para começar
- **Visual tokens mode:** `provisional` se ainda tem CSS hardcoded significativo (a maioria), `final` só se já migrou tudo

### Passo 4.3 — CRÍTICO: revisar ROADMAP gerado

Abra `.planning/ROADMAP.md`. Confira:
- Seção "Já concluído" bate com realidade?
- Seção "Futuro" reflete o backlog real?
- Nenhum sprint de "refatorar projeto inteiro" sugerido?

Ajuste se necessário. Commit:

```bash
git add .planning/
git commit -m "chore: bootstrap em modo legado, roadmap com histórico + futuro"
```

---

## FASE 5 — Configurar framework para conviver com código legado (30 min)

### Passo 5.1 — Ajustar `sprint_ui_matrix` para legacy

Se seu projeto tem áreas legadas que NÃO seguem padrões das skills, você precisa excluir elas do enforcement para não bloquear ajustes pequenos.

Edite `.planning/config.json`:

```json
{
  "legacy_code_paths": [
    "src/legacy/**",
    "src/admin/old/**",
    "public/jquery/**"
  ],
  "enforcement_scope": {
    "mode": "new_code_only",
    "skip_skills_for_paths": "legacy_code_paths"
  }
}
```

Isso diz ao plan-checker: "ao ver task que toca só arquivos em `legacy_code_paths`, não exija skills UI rigorosamente".

### Passo 5.2 — Ajustar ESLint/linters para legacy

Se CSS antigo tem 2000 hex hardcoded, você não quer que ESLint bloqueie CI. Adicione override:

```json
{
  "overrides": [
    {
      "files": ["src/legacy/**", "src/admin/old/**"],
      "rules": {
        "no-hardcoded-colors": "off",
        "no-hardcoded-spacings": "off"
      }
    }
  ]
}
```

### Passo 5.3 — Ajustar hooks se necessário

Se `gsd-read-guard.js` está bloqueando leitura de arquivos do projeto, adicione exceções em `.claude/hooks/gsd-read-guard.js` (seção `ALLOWED_PATHS`).

### Passo 5.4 — Commit

```bash
git add .planning/config.json .eslintrc.json .claude/hooks/
git commit -m "chore: configura framework para conviver com código legado"
```

---

## FASE 6 — Primeiro ajuste pelo framework (30 min a 2h)

Hora de aplicar o framework em um ajuste real.

### Passo 6.1 — Escolher algo pequeno

**NÃO escolha** grande feature no primeiro uso. Escolha:
- Adicionar um campo a um form
- Corrigir cálculo de comissão
- Adicionar endpoint GET simples
- Melhorar error message

Algo que, sem framework, levaria 30-60 min.

### Passo 6.2 — Escolher caminho: quick ou sprint completo?

**Use `/gsd:quick` se:**
- Mudança tem < 50 linhas de código
- Toca 1-3 arquivos
- Não é arquitetural
- Você confia na sua DoD mental

**Use sprint completo se:**
- Mudança > 100 linhas
- Toca múltiplas camadas (backend + frontend + db)
- Tem implicação de segurança
- É feature nova (não só ajuste)

### Passo 6.3 — Caminho A: `/gsd:quick` (ajuste pequeno)

```
/gsd:quick "adiciona campo telefone no cadastro de cliente"
```

Claude vai:
1. Ler skills relevantes (`br/brazilian-forms` para formato telefone BR)
2. Fazer mini-plan mental
3. Implementar o ajuste aplicando skills
4. Escrever teste mínimo
5. Commitar com mensagem conventional

Tempo: 15-30 min.

### Passo 6.4 — Caminho B: Sprint completo

Para mudança maior, siga mesmo fluxo do projeto novo, mas **adaptado para legado**:

```
/gsd:plan-phase M<próximo>-<slug>
```

Dentro dos SPRINT.md gerados, atenção especial a:

```
Este sprint toca ARQUIVOS LEGADOS? Se sim, marque no front-matter:
---
legacy_scope: true
legacy_files:
  - src/legacy/old-form.tsx
  - backend/old_controllers/user.py
---

E na seção ## Riscos, liste:
- Dívida técnica conhecida em arquivos tocados
- Pontos de atenção durante modificação (não refatorar escopo extra)
```

Depois:

```
/gsd:plan-phase sprint-<N>-<slug>
```

### Passo 6.5 — CRÍTICO: prompt de contexto legado

Antes de `/gsd:execute-phase`, além do prompt padrão de forçar leitura de skills, use também este:

```
Este sprint toca arquivo legado em <path>. ANTES de modificar:

1. Leia o arquivo inteiro primeiro
2. Me resuma em 3 linhas:
   - O que esse arquivo faz
   - Que padrão/convenção já está estabelecido nele
   - Qual é a cara do código legado ao redor

3. Me diga como você vai modificar MINIMAMENTE para atingir o DoD, 
   SEM refatorar nada que não seja estritamente necessário

4. Liste em TECH-DEBT.md quais dívidas você NOTOU no arquivo mas 
   NÃO vai resolver neste sprint

Só comece a codar após eu confirmar seu plano.
```

Isso impede o comportamento "Claude resolve quer refatorar tudo ao redor" que é um vício em projeto legado.

### Passo 6.6 — Executar

```
/gsd:execute-phase sprint-<N>-<slug>
```

### Passo 6.7 — Reconcile vai reportar MUITO em projeto legado

Na primeira vez, reconcile pode reportar 20+ divergências do tipo "código não segue padrão X". Filtrar:

- Se divergência é em **código que você tocou**, resolva
- Se divergência é em **código ao redor que você não tocou**, marque como dívida técnica e siga
- Se divergência é em **arquivo marcado como `legacy_files`**, ignore

### Passo 6.8 — Fechar

```
bin/collect-metrics.sh sprint-<N>-<slug>
```

Preencha retro HONESTAMENTE. Se foi difícil, anote. Essa é sua telemetria real.

---

## FASE 7 — Hotfix retrospectivo (quando acontecer)

Projeto em produção tem hotfixes. **Não tente fazer hotfix pelo framework** — é lento demais para emergência.

### Passo 7.1 — Fluxo de emergência (sem framework)

```bash
# Incidente às 2h da manhã
git checkout -b hotfix/critico
# ... escreve fix ...
git commit -m "fix: bug crítico no processamento de pagamento" --no-verify
git push origin hotfix/critico
# Merge e deploy
```

O `--no-verify` pula hooks do framework. Para emergência, faz sentido.

### Passo 7.2 — Retrospectiva do hotfix (na manhã seguinte)

Depois que a dor passa, em sessão normal:

```
Tive incidente em produção ontem 22h. Hotfix commitado em <hash>:
- Sintoma: [descrever]
- Causa root: [descrever]
- Fix aplicado: [descrever brevemente]

Quero que você:

1. Leia o commit <hash> e confirme o que foi feito
2. Atualize .planning/TECH-DEBT.md:
   - Adicione dívida técnica que o incidente revelou
   - Liste arquivos frágeis detectados

3. Atualize .planning/SUGGESTIONS.md:
   - Padrão melhor que emergiu da investigação
   - Skill que se fosse aplicada antes teria prevenido

4. Se o fix modificou lógica de negócio importante, sugira ADR 
   em docs/adrs/ explicando mudança

5. Me proponha: devemos criar sprint dedicado para consolidar o 
   fix (testes, refatoração, observabilidade adicional) ou 
   documentar como dívida e seguir?

Seja direto. Não faça mais do que pedi.
```

Isso converte hotfix em aprendizado institucional. Sem esse passo, mesma causa volta em 6 meses.

---

## FASE 8 — Ciclo contínuo misto

Projeto legado em modo framework tem 3 tipos de trabalho convivendo:

### Tipo 1 — Hotfixes (sem framework)

Emergências. Resolve rápido, retrospectiva depois (Fase 7).

### Tipo 2 — Ajustes pequenos (`/gsd:quick`)

Mudanças menores e bugs não-críticos. Pegam padrão framework de leve.

### Tipo 3 — Features reais (sprint completo)

Novas funcionalidades, mudanças arquiteturais, integrações. Framework inteiro.

### Proporção típica em projeto legado maduro

- 10% hotfixes (imprevisíveis)
- 40% ajustes pequenos (`/gsd:quick`)
- 50% features reais (sprint)

### Rituais que você adota

**Semanal** (30 min):

```bash
# Revisar métricas da semana
cat .planning/METRICS.md | tail -20

# Revisar novos INDEX.md se adicionou docs
/gsd:docs-update

# Revisar TECH-DEBT acumulada
/gsd:td-review
```

**Mensal** (1-2h):

```bash
# Exportar telemetria para iteração
bash bin/export-telemetry.sh

# Revisar SUGGESTIONS acumuladas — promover ou descartar
/gsd:suggestions

# Revisar ADRs pendentes de contexto
ls docs/adrs/ | head
```

**Trimestral** (meio dia):

Revisar se alguma dívida técnica de `TECH-DEBT.md` já justifica sprint dedicado. Se sim, adicione ao ROADMAP.

---

## COMANDOS PRINCIPAIS — projeto legado

### Ajustes rápidos

```
/gsd:quick "descrição em 1 linha"   # ajuste pequeno (15-30 min)
```

### Sprint completo

```
/gsd:plan-phase M<N>-<slug>         # quebrar milestone novo em sprints
/gsd:plan-phase sprint-<id>          # gerar PLAN
/gsd:execute-phase sprint-<id>       # executar (ver Fase 6.5!)
bin/collect-metrics.sh sprint-<id>             # retro + métricas
```

### Retrospectivas

```
/gsd:note "texto curto"              # nota rápida à fase atual
/gsd:session-report                  # snapshot do que aconteceu na sessão
```

### Governança

```
/gsd:health                          # scan de divergências
/gsd:td-review                       # revisa dívida técnica
/gsd:suggestions                     # revisa sugestões promovidas
/gsd:docs-update                      # sincroniza INDEX.md de docs/
```

Lista completa em `ls .claude/commands/gsd/` (73 commands).

---

## PROMPTS ESSENCIAIS — projeto legado

### Início de sessão em legado (sempre)

```
Abri sessão nova em projeto legado com gsd-framework adotado.

1. Leia CLAUDE.md
2. Leia .planning/STATE.md
3. Leia docs/archaeology/README.md (se existir)
4. Me diga em 3 linhas: em que milestone estamos, qual o último 
   sprint fechado, que sprint está em andamento (se houver).

Não execute nada ainda.
```

### Antes de tocar código legado

```
Este sprint toca <arquivo-legado>. ANTES de modificar:
1. Leia o arquivo inteiro
2. Me resuma: o que faz, que padrão usa, como é código ao redor
3. Diga como vai modificar MINIMAMENTE sem refatorar extras
4. Liste em TECH-DEBT.md dívidas que notou mas NÃO vai resolver

Só comece a codar após eu confirmar o plano.
```

### Retrospectiva de hotfix

```
Tive incidente em produção. Hotfix commitado em <hash>:
- Sintoma: ...
- Causa: ...
- Fix: ...

Atualize TECH-DEBT.md e SUGGESTIONS.md com aprendizados. 
Proponha se vale sprint de consolidação ou só dívida.
```

### Claude quer refatorar demais

```
Pare. Você está querendo refatorar escopo maior que o sprint pediu. 
Este é projeto legado — não refatoramos fora do necessário.

1. Reverta refatorações que saíram do DoD do sprint
2. Documente em TECH-DEBT.md o que deixou de refatorar e por quê
3. Continue SÓ com o DoD original
```

### Auditoria honesta de sprint em código legado

```
Antes de fechar, auditoria honesta:
1. Que dívida técnica você RESOLVEU sem pedir autorização? Reverte.
2. Que regra de skill você ignorou por conta do código ao redor? Liste.
3. Que teste você NÃO escreveu por complexidade do legado? Liste.
4. Que incompatibilidade você encontrou entre tokens.json e CSS 
   legado? Liste.

Seja autocrítico. Projeto legado força compromissos — é normal, 
mas precisa estar documentado.
```

---

## CHECKLIST DE ADOÇÃO EM LEGADO

### Antes do Claude

- [ ] Projeto em branch `adocao-framework-gsd`
- [ ] Framework instalado (apenas pastas necessárias, sem sobrescrever projeto)
- [ ] `bash tests/framework/run-all.sh` → 5/5
- [ ] `.gitignore` atualizado
- [ ] Scripts com `chmod +x`

### Arqueologia

- [ ] Inventário estrutural gerado
- [ ] `specs/stack.yaml` extraído da realidade
- [ ] `docs/archaeology/BACKEND.md` gerado e revisado
- [ ] `docs/archaeology/DATABASE.md` + `specs/database.yaml` gerados
- [ ] `docs/archaeology/FRONTEND.md` gerado e revisado
- [ ] `docs/archaeology/INFRA.md` gerado
- [ ] `docs/archaeology/BUSINESS-RULES.md` extraído e revisado
- [ ] ADRs retroativos em `docs/adrs/`

### Consolidação

- [ ] `docs/project-brief.md` com seção "Status atual em produção"
- [ ] `specs/rules.yaml` canônico a partir de BUSINESS-RULES
- [ ] `docs/identidade-visual/tokens.json` extraído do CSS existente
- [ ] `.planning/TECH-DEBT.md` populado com dívidas identificadas

### Bootstrap

- [ ] Prompt de contexto legado enviado ANTES do `/gsd:bootstrap`
- [ ] `ROADMAP.md` com seção "Já concluído" e "Futuro"
- [ ] Strategy de slicing escolhida
- [ ] `visual_tokens_mode: provisional` se tem CSS hardcoded

### Convivência com legado

- [ ] `legacy_code_paths` configurado em `.planning/config.json`
- [ ] ESLint overrides para `src/legacy/**`
- [ ] Hook guards ajustados se bloqueando arquivos legítimos

### Primeiro uso

- [ ] Ajuste pequeno feito via `/gsd:quick` com sucesso
- [ ] Feature nova feita via sprint completo com sucesso
- [ ] Hotfix retrospectivo documentado em TECH-DEBT/SUGGESTIONS
- [ ] Retro do primeiro sprint preenchida HONESTAMENTE

---

## O QUE VOCÊ VAI GANHAR EM 3-6 MESES

**Mês 1:** Documentação do projeto existe pela primeira vez. Onboarding de dev novo vai de 2 semanas para 3-4 dias.

**Mês 2-3:** Ajustes novos nascem mais limpos. `TECH-DEBT.md` começa a ser usado para priorizar refatorações.

**Mês 4-6:** Padrão viraliza no time. Incidentes antigos começam a ter root cause identificado pelo histórico de SUGGESTIONS. Novos membros pegam padrão sem fricção.

**Ano 1:** Proporção de "código novo disciplinado" vs "código legado" atinge inflexão. Dívida técnica agregada começa a cair em valor absoluto.

---

## QUANDO NÃO ADOTAR

Ignore este guia e mantenha seu fluxo atual se:

- Projeto está em final de vida (sunset previsto em < 6 meses)
- Time de 1 pessoa que domina o código e não vai sair
- Projeto é script interno que ninguém mais vai tocar
- Mudanças futuras são apenas bugfix esporádico (< 1 por mês)

Nesses casos, custo de adoção não retorna.
