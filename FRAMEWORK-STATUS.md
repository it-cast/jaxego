# FRAMEWORK-STATUS.md

> Este arquivo rastreia o **desenvolvimento do próprio framework** — o que foi feito, o que falta, decisões tomadas durante o design, e contaminações detectadas.
> Diferente de `.planning/STATE.md` (que rastreia o projeto do usuário), este arquivo é sobre o framework em si.
> **Ao adotar o framework em novo projeto:** você pode apagar este arquivo ou mantê-lo como histórico. Não é consumido por nenhum workflow.

**Última atualização:** 2026-06-09
**Versão semântica do framework:** 0.9.7 (fidelidade de wireframe enforced ponta a ponta + guia de geração + gerador de documentação. Ver entrada v0.9.7 abaixo.)

---

## A. Changelog do desenvolvimento

### 2026-06-09 — v0.9.7 — "Wireframe como fonte de verdade: a cadeia de fidelidade fechada"

**Contexto:** o operador perguntou se um wireframe HTML colocado em `projeto/wireframes/` seria construído fielmente. A auditoria revelou que NÃO era garantido: o ingestor lia o DOM (DECISION-49) e extraía informação para a descoberta, mas o `ui-phase` não era obrigado a consultar o wireframe ao gerar o UI-SPEC, e nenhum checker validava a tela construída contra ele. O wireframe informava o início e era esquecido no meio — fidelidade dependia de boa vontade do agente.

**A cadeia fechada (4 elos novos):**
1. **`gsd-tools wireframe-contract <arquivo>`** (lib/wireframe.cjs) — extrai do HTML/JSX/TSX/Vue/Svelte um contrato estrutural determinístico: regiões semânticas, headings com texto, botões e links (texto + destino), inputs por name, estados (loading/empty/error/success), cores candidatas a token, nav_targets. Sem dependências externas. Limitação honesta documentada: cobre o DOM ESTÁTICO (HTML gerado por JS em runtime não aparece) — suficiente para outputs Lovable/v0/bolt.
2. **ui-phase passo 2.5 (obrigatório quando existe wireframe):** rodar o contrato por tela; UI-SPEC declara `wireframe_source:` por tela; TODO item do contrato aparece no spec OU em `deviations:` com razão explícita; cores do wireframe mapeadas a tokens (amarra no Gate 2); nav_targets viram rotas reais. Wireframe-imagem: declaração + deviations, sem check mecânico. Sem wireframe: `wireframe_source: none`.
3. **ui-checker Dimension 7 — Wireframe Fidelity (6→7 dimensões):** o checker RODA o contrato (não confia no auto-relato do spec) e bloqueia: tela com wireframe existente mas sem declaração; item ausente de spec E deviations (omissão silenciosa); deviation sem razão; cor mapeada a token inexistente. `wireframe_source: none` com wireframe existente no disco = BLOCK.
4. **verify-phase (Gate 8):** na coleta de evidência, confere os elementos interativos do contrato no CÓDIGO CONSTRUÍDO (textos de botão, rotas, inputs por name/formControlName). Divergência sem deviation registrada = FAIL-DEBT classe UX.

**Também nesta versão:**
- `GUIA-GERACAO-DE-APLICACAO.md` — passo a passo único do zero ao deploy (modelos → documentação → ingest → bootstrap → autopilot), na raiz do framework
- `GERADOR-DE-DOCUMENTACAO.md` — prompt-mestre para gerar toda a documentação que o framework consome a partir de uma conversa de discovery (gera `projeto/` completo + tokens.json + wireframes descritivos)

**Numericamente:** comandos gsd-tools 19→20; suites 10→11 (+test_wireframe_fidelity, 18 checks); ui-checker 6→7 dimensões.

**Limitações que continuam:** zero field data (inalterado — e o wireframe-contract é mais um mecanismo cuja utilidade real só o campo confirma); contrato cobre DOM estático; fidelidade de wireframe-IMAGEM continua validação visual (sem contrato mecânico).

---

### 2026-06-09 — v0.9.6 — entrada anterior

(versão de ENFORCEMENT e correção — não adiciona capacidade nova; converte prosa em código, fecha drift documental e aprofunda a skill-âncora de segurança. Ver entrada v0.9.6 abaixo. Modelo: revisão e implementação por Claude Fable 5.)


### 2026-06-09 — v0.9.6 — "Enforcement por código: Gate 8 script, partition determinístico, docs↔código testado"

**Contexto:** a revisão 360 da v0.9.5 (feita pelo mesmo modelo que a construiu — viés reconhecido) encontrou 4 problemas, e o operador pediu a correção de todos. Esta versão deliberadamente NÃO adiciona capacidade — adiciona verificabilidade. A tese: cada mecanismo crítico que vive como prosa para o LLM obedecer é um mecanismo que pode ser citado sem ser executado.

**Problema 1 — drift de documentação dentro do próprio pacote (corrigido + prevenido).**
A v0.9.5 corrigiu 733 paths Windows mas deixou no changelog duas entradas afirmando "159 arquivos ainda pendentes"; o `go.md` dizia "7 gates" num framework de 8; quatro docs instruíam `gsd-tools.cjs --help` com filename errado (`gsd:tools`) e flag que retornava erro. Correções:
- Entradas contraditórias anotadas `[RESOLVIDO em v0.9.5]` (histórico preservado, história falsa eliminada)
- Todas as referências a "7 gates" em docs atuais → 8 (README, CLAUDE.md, go.md, gates-v3.md, MIGRACAO)
- Typos `gsd:tools.cjs`/`gsd:framework`/`gsd:orchestrator.md`/`gsd:statusline.js`/`gsd:read-guard.js` corrigidos (sobras do sed da migração de namespace `/gsd-`→`/gsd:`)
- `gsd-tools --help` (flag sozinha) agora imprime usage com exit 0; a proteção contra flags alucinadas em COMANDOS permanece
- **Prevenção estrutural: `tests/framework/test_docs_consistency.sh`** — valida contagens declaradas vs disco, número de gates em docs atuais, zero `C:/` em código, toda invocação de gsd-tools documentada executável, e todo `/gsd:<cmd>` citado existindo como arquivo. **Na primeira execução o teste pegou 13 commands fantasma adicionais** que a revisão manual não tinha visto (`/gsd:docs-index`→docs-update, `/gsd:tech-debt`→td-review, `/gsd:reconcile`→reconcile-state, `/gsd:verify`→verify-phase, e `/gsd:suggestions` que era prometido nos guias mas nunca existiu — agora criado, fechando o ciclo com o hook gsd-suggestion-detector). O padrão ERRATA.md agora é detectável por máquina.

**Problema 2 — Gate 8 era enforcement por prosa (corrigido).**
O gate mais importante da v0.9.5 vivia só como instrução no workflow — a mesma classe de fraqueza do Gate 3, um nível acima. Correções:
- **`gsd-tools verify quality-bar <N>`** (lib/verify.cjs): valida presença do QUALITY-BAR.md, falha com qualquer FAIL-BLOCK aberto (resolvido = `[RESOLVIDO]` na linha, com evidência), falha com FAIL-DEBT não contabilizado em TECH-DEBT.md citando a phase, e falha com arquivo vazio/template (gate "avaliado" sem veredito não conta)
- **Hook `gsd-phase-transition-guard.sh`** roda o check automaticamente antes de qualquer transição de phase — bloqueio mecânico, com override consciente via `GSD_SKIP_TRANSITION_GUARD` + razão em DECISIONS.md
- Workflow `verify-phase.md` passo 5 exige a validação por script; suite `test_quality_bar_gate.sh` cobre os 5 cenários

**Problema 3 — skill-âncora de segurança rasa (corrigido).**
`owasp-security` tinha 59 linhas (média do framework: ~366) e prescrições discutíveis cristalizadas. Reescrita para ~240 linhas de densidade sênior:
- JWT: tabela de decisão por nº de validadores (HS256 mono-serviço; RS256/ES256 multi-serviço/JWKS) em vez de HS256 fixo — relevante para arquiteturas com worker + gateway validando o mesmo token
- Rate limits: heurísticas de derivação por classe de endpoint (auth = duas dimensões IP+conta; endpoints caros = orçamento de custo por plano) em vez de números mágicos; número sem derivação documentada = FAIL-DEBT
- Novos: ownership-na-query para multi-tenant (404 não 403), allowlist de SORT BY, `extra="forbid"` contra mass assignment, SSRF com revalidação pós-redirect (relevante para integrações LLM), redação estrutural de logs + conexão LGPD, "segredo commitado = rotacionar (rewrite de histórico é cosmético)", webhooks HMAC-antes-de-parse, mapa explícito Gate 8 Bloco B → seções

**Problema 4 — fingerprints cobriam 12 de 73 skills (corrigido + 2 bugs).**
- Cobertura expandida para **73/73** (validado 1:1 contra o disco por teste): skills de código com imports/keywords; skills de processo (meta/*) com fingerprints de ARTEFATO — o check já varria SUMMARY.md, então evidência de artefato conta
- Bug 1: key `standalone/owasp-security` nunca casava com a skill real `owasp-security` — aliases de normalização adicionados
- Bug 2: `extractSkills` exigia formato `categoria/nome` — TODAS as 6 skills standalone eram silenciosamente invisíveis ao check. Regex corrigida
- Honestidade registrada no próprio hook e no KNOWN-LIMITS: keyword presente ≠ aplicação profunda; o check otimiza para detectar skill citada e IGNORADA (zero sinais), que é o caso que importa. Profundidade é papel do Gate 8 + review

**Extra — particionamento de waves vira código (o componente de maior risco do paralelismo).**
A lógica de "particionar por fronteira de arquivos" do `gsd-wave-dispatcher` era prosa — o agente calculava de cabeça. Agora:
- **`gsd-tools partition`** (lib/partition.cjs): expansão determinística de implícitos estruturais (models/→`__init__.py`, pyproject.toml→lockfiles, package.json→lockfiles JS), serial-triggers (migrations, lockfiles, config global, .planning/), union-find por interseção, task sem files → serial (conservador por design), paths Windows normalizados
- Agente atualizado: **chama o comando e obedece à saída**; seu julgamento fica restrito a enriquecer implícitos de domínio, anexar grupos triviais ao serial e respeitar max_concurrent
- Suite `test_partition.sh`: 18 checks cobrindo 11 cenários, incluindo o realista misto (back∥front com migration e dep no serial)

**Telemetria:**
- Bug: coletor procurava `QUALITY-BAR.md`/`EXECUTION-LOG.md` por nome exato; a convenção prefixa com a phase (`01-QUALITY-BAR.md`) — coletaria zero para sempre. Corrigido para `*QUALITY-BAR.md`
- Métricas novas: `gate8_enforcement_script` (quantas phases passariam/bloqueariam HOJE, rodando o verify real — estado, não auto-relato) e `particoes_via_codigo`

**Numericamente:**

| Componente | v0.9.5 | v0.9.6 |
|---|---|---|
| Skills | 73 | 73 (owasp-security reescrita 59→~240 linhas) |
| Fingerprints de aplicação | 12 | **73** (cobertura 1:1, testada) |
| Commands | 92 | **93** (+`/gsd:suggestions`) |
| Comandos gsd-tools | 17 | **19** (+`verify quality-bar`, +`partition`) |
| Suites de teste | 7 | **10** (+quality_bar_gate, +docs_consistency, +partition) |
| Gates enforced por script | 6 | **7** (Gate 8 deixou de ser prosa) |

**Limitações que continuam (sem mudança — e é importante dizer):**
- **Zero field data validado.** Esta versão melhora a VERIFICABILIDADE do framework, não sua VALIDAÇÃO. Nenhuma linha daqui substitui rodar um milestone real do Áugure e exportar telemetria. A nota de validação/medição continua tetada por isso, por construção.
- Heurística de fingerprint detecta ausência, não profundidade (documentado em KNOWN-LIMITS §1).
- Ganho de paralelismo (30-45%) continua sendo projeção de design.
- Quem revisou e quem implementou é o mesmo modelo — a auditoria independente real é o campo.

---

### 2026-06-09 — v0.9.5 — "Entrada única, FastAPI/CI, tabelas/busca, wave-dispatcher"

**Contexto:** operador pediu análise crítica + amplificação com foco em (1) UX do próprio framework, (2) cobertura de stack, (3) paralelismo de múltiplos agentes. A revisão encontrou três classes de gap, atacadas cirurgicamente sem tocar na orquestração v0.9.4.

**Gap 1 — UX do framework: 93 comandos, nenhuma porta de entrada.** O operador precisava saber, a cada estado do projeto, qual dos comandos usar. Solução: **`/gsd:go`** — comando único que detecta o estado (novo com docs / novo sem docs / em andamento / milestone fechado / inconsistente) e roteia automaticamente para a cadeia certa, com pausas de revisão garantidas (DISCOVERY-REPORT, ROADMAP, gate block, fim de milestone). Reduz a superfície de decisão de 92 para 1 **sem desligar nenhum gate**. Não substitui os comandos granulares — é a porta para quem não quer decorá-los.

**Gap 2 — cobertura de stack incompleta.** Havia skill para Angular, Ionic, MySQL, Docker e LLM, mas **nenhuma para o backend FastAPI** (camada onde nascem endpoints, auth e a maioria dos bugs de integração) nem para o **CI** que chama os scripts de deploy já existentes. Além disso, todo painel B2B é tabela + busca/filtro — sem skills dedicadas. Adicionadas 5 skills:
- `domain/fastapi-production-patterns` (🔒 has_api) — estrutura router/service/repository, Pydantic v2, auth JWT, erros canônicos `{"error":{...}}`, async DB armadilhas (pool_recycle, N+1), Arq jobs, testes. Incorpora bugs de campo reais (pythonpath, alembic TEST_DATABASE_URL, arq/redis).
- `domain/github-actions-ci` — pipeline canônico (MySQL service real, `npm ci`/`uv sync --frozen`, migrations no CI, concurrency), build GHCR, deploy VPS chamando `bin/deploy-*.sh`, build mobile Capacitor, secrets. Pin de actions por SHA (caso apple-actions@v3).
- `ux-advanced/data-tables-ux` (🔒 has_admin) — paginação server-side, 3 estados vazios, bulk actions, mobile cards, trackBy, export do resultado filtrado.
- `ux-advanced/search-filter-ux` — chips de filtro ativo, estado na URL, debounce+switchMap, zero-results com saída, FULLTEXT MySQL, whitelist de colunas.
- `meta/parallel-orchestration` — base de segurança do paralelismo de escrita.

**Gap 3 — paralelismo só de leitura.** O `gsd-squad-orchestrator` paraleliza research/review/audit (leitura). Não havia contraparte para **execução** (escrita). Adicionado:
- Agente `gsd-wave-dispatcher` — particiona tasks de uma wave por fronteira de arquivos (incluindo implícitos: router de registro, migration, barrels, lockfile), serializa classes proibidas (migrations/lockfiles/registros centrais SEMPRE seriais), dispara até 3 `gsd-executor` em paralelo nos grupos disjuntos, trata `conflict_request` com lease, fecha a wave com test+lint integrado, registra wall-clock real vs estimativa serial em METRICS.
- `gsd-roadmapper` agora grava `flags:`, `pre-phase:`, `post-execute:` e `parallel-hint:` por phase — metadata que o autopilot já lia mas que ninguém escrevia (elo solto da v0.9.1).
- `autopilot` lê `parallel-hint` e ativa task_level por phase; `execute-phase` delega ao dispatcher quando ligado.

**Correções de integridade encontradas na revisão:**
- Referência fantasma a `gsd-task-executor` (agente inexistente) no `execute-phase.md` → corrigida para `gsd-executor` + branch do dispatcher.
- `plan-checker` ganhou clause type `config:` e reconhecimento explícito das flags `has_api`/`has_admin`/`has_ai` em `required_for`.
- SKILLS_INDEX ganhou nota de autoridade: contagem real vem de `find`, não da tabela curada (que defasava desde v0.3).

**Contadores v0.9.5:**

- 73 skills (era 67; +6: fastapi-production-patterns, github-actions-ci, data-tables-ux, search-filter-ux, parallel-orchestration, senior-quality-bar)
- 45 agents (era 44; +1 gsd-wave-dispatcher)
- 93 commands (era 91; +1 /gsd:go)
- 8 gates (era 7; +1 Gate 8 Senior Quality Bar)
- 19 hooks (mesmo — gsd-metrics-trigger ganhou disparo de framework-telemetry)
- 10 bin scripts (era 9; +1 collect-framework-telemetry.sh)
- 114+ testes (suíte framework agora 7 suites; test_v095_additions com 30+ checks)

**Modelos dos agentes (decisão do operador):** os 3 agentes de raciocínio pesado (`gsd-project-ingestor`, `gsd-squad-orchestrator`, `gsd-wave-dispatcher`) agora usam `claude-fable-5` (tier Mythos, acima do Opus). Executores e agentes táticos seguem em `claude-sonnet-4-6`. Trade-off explícito: mais capacidade de orquestração/partição vs custo maior por sessão — reverter é trocar uma linha de frontmatter.

**Segunda rodada (resposta a "garanta produtos acima da média" + "novos projetos serão medidos?"):**

- **Gate 8 — Senior Quality Bar.** O Gate 7 (test+lint verde) é o piso de um júnior competente, não a barra sênior. Adicionada skill `quality/senior-quality-bar` — a Definição de Pronto de uma equipe sênior em critérios **observáveis** (não "código limpo", e sim "função >50 linhas justificada", "endpoint de lista sem N+1", "migração reversível"), nos 4 blocos: dev, segurança, deploy, UX. O Gate 8 (bloqueante, em verify-phase após reconcile) classifica cada item PASS/FAIL-BLOCK/FAIL-DEBT/N/A. **FAIL-BLOCK** (segredo no repo, deploy irreversível, backup ausente, N+1, injection, auth indefinida, PII em log) impede a phase de fechar; **FAIL-DEBT** vira dívida consciente contabilizada. A distinção é o que evita que a barra vire teatro: o perigoso bloqueia, o melhorável fica visível. Honestidade explícita na própria skill: isso **eleva o piso**, não **garante** output sênior — garantir exigiria julgamento humano de adequação ao domínio que nenhum checklist substitui.

- **Camada framework-telemetry.** `bin/collect-framework-telemetry.sh` mede o **próprio framework** (distinto de `collect-metrics.sh`, que mede o projeto): quantos FAIL-BLOCK o Gate 8 capturou (valor entregue), taxa de rebaixamento serial do wave-dispatcher, uso de `/gsd:go`, aplicação das skills novas. Disparado automaticamente pelo `gsd-metrics-trigger` ao fim de phase. Tem campos `interpretacao_humana` (`<FILL>`) que são o que de fato fecha o gap de field data — sem eles, há números; com eles, validação. Responde diretamente "novos projetos na v0.9.5 serão medidos?": sim, e agora separadamente como métrica-de-framework vs métrica-de-projeto.

- **Bug de portabilidade corrigido (sério).** Encontrados **733 paths Windows hardcoded** (`C:/Projetos/global/...`) em 162 arquivos — incluindo 20+ agentes. Um framework que se diz cross-platform quebraria em qualquer máquina que não fosse a do autor original. Substituídos por caminhos relativos (`./`). Esse era um defeito real que nenhuma versão anterior tinha detectado, e que teria falhado no primeiro uso por outra pessoa.



**O que esta versão NÃO resolve (honesto — e é o ponto mais importante):**

- **Ainda zero field data.** Da v0.4 à v0.9.5, toda melhoria — inclusive estas — é raciocínio sobre o fluxo, não medição de campo. O caminho para nota 9+ **não é mais skill nem mais agente**; é rodar um projeto real (Áugure) ponta a ponta e exportar telemetria. Adicionar capacidade a um sistema não-validado tem risco de ser a direção errada se o gargalo real é validação.
- **`gsd-wave-dispatcher` não usa git worktrees.** Executores compartilham working tree; a segurança vem da disjunção de leases, não de isolamento físico. Tasks que regeram artefatos globais (build) devem ser seriais — o dispatcher rebaixa, mas a heurística de implícitos é por-stack (FastAPI/Angular cobertos; stacks exóticas → mais serialização conservadora).
- **`/gsd:go` foi escrito mas não testado em projeto real.** A árvore de decisão é raciocínio sobre os 5 estados; casos de borda (STATE parcialmente corrompido, projeto/ com lixo) podem precisar de calibração.
- **Skills novas são templates de conhecimento, não validadas em código gerado.** `fastapi-production-patterns` codifica padrões corretos, mas "skill citada ≠ skill aplicada" continua valendo (Regra 5).
- **Ganho de paralelismo é projeção:** back∥front ~30-45% wall-clock é estimativa de design. Só a telemetria do dispatcher (wall-clock real vs serial) dirá se compensa o custo de tokens (N× por N executores).

---

### 2026-05-22 — v0.9.4 — "Variante Docker: GHCR, MySQL nativo, recuperação de desastre"

**Contexto:**
Após v0.9.3 (deploy-safety com symlink físico), operador esclareceu o modelo de deploy desejado: Docker com rollback por tag, imagens no GHCR, MySQL nativo na VPS fora do Docker. Ênfase declarada: **integridade de dados é primordial** — sem risco de deploy/migration zerar o banco.

Conversa de design cobriu: por que imagem é descartável e dados são sagrados (separação física), por que MySQL fica fora do compose, três níveis de proteção de dados, e o RPO real de cada estratégia de backup (honestidade sobre "recuperação ao segundo" exigir replicação síncrona vs dump+binlog entregar "perda de minutos").

**Decisões de arquitetura (registradas):**
- App em Docker, imagens no GHCR (`ghcr.io/usuario/projeto-{api,web}:TAG`), tag imutável (SHA/timestamp)
- MySQL **nativo na VPS, fora do Docker** — dados em `/var/lib/mysql`, banco nunca no compose
- Backup: dump diário (30d retenção) + binlog arquivado (PITR de minutos) pro B2
- Migração de servidor: operação manual planejada (rara), runbook documentado
- Promoção para banco gerenciado (Nível 2): decisão futura por-projeto

**4 entregáveis:**

**1. Skill `monorepo-deploy-safety` ganha seção 5B (Docker)**

Conteúdo novo: princípio imagem-descartável-vs-dados-sagrados (tabela), arquitetura recomendada (diagrama VPS + container + MySQL nativo + B2), três níveis de proteção de dados com matriz de escolha, RPO honesto de cada estratégia, fluxo de deploy Docker (CI + VPS), volumes/persistência (compose conceitual), runbook de migração de servidor, anti-patterns específicos de Docker.

**2. `bin/deploy-docker.sh`**

Deploy via GHCR: pre-flight, pull, backup pré-migration obrigatório, migration antes do switch, up -d graceful, health check com 6 tentativas, rollback automático por tag, image prune. **Nunca usa `down -v`.** Suporta `--rollback`, `--rollback-to=TAG`, `--dry-run`. Aborta deploy se backup pré-migration falhar.

**3. `bin/backup-mysql-b2.sh` + `bin/restore-mysql-b2.sh`**

Backup: `full` (dump diário `--single-transaction --master-data=2`, sem downtime), `binlog` (arquiva binlogs para PITR), `pre-migration` (dump rotulado antes de migration), `prune` (retenção 30d full/binlog, 90d pré-migration). Verifica integridade do gzip. Upload via rclone ou b2 CLI. Documentação SETUP completa (usuário backup, ~/.my.cnf, ativar binlog, cron, teste de restore).

Restore: `--list`, `--date=` (restore de dump), `--pitr=` (dump base + replay binlog até instante exato). Dupla confirmação antes de sobrescrever. Dump de segurança do estado atual antes do restore.

**4. `gsd-release-auditor` ganha 8ª dimensão (Docker + data safety)**

Checks: tags imutáveis (não `latest`), imagens no registry, login configurado, MySQL fora do compose, backup pré-migration testado, backup diário no cron, binlog ativado, **nenhum `down -v` em scripts** (BLOCKER), secrets fora da imagem (BLOCKER se na imagem).

**Recuperação de desastre — RPO honesto (documentado):**
- Só dump diário: perde até 24h
- Dump + binlog PITR: perde minutos ← entregue
- Replicação síncrona: zero perda, mas caro/complexo — não implementado (over-engineering para o estágio)

**Contadores v0.9.4:**

- 67 skills (mesmo — skill existente expandida)
- 44 agents (mesmo — release-auditor expandido)
- 91 commands (mesmo)
- 19 hooks (mesmo)
- 350 permissions (mesmo)
- 9 bin scripts (era 6; +3: deploy-docker, backup-mysql-b2, restore-mysql-b2)

**O que esta versão NÃO resolve (honesto):**

- **Scripts são templates, testados só em dry-run/sintaxe.** Não há VPS, MySQL, nem GHCR no ambiente de dev do framework. O fluxo real precisa ser validado no primeiro deploy de campo.
- **PITR via binlog exige setup manual** (log_bin no my.cnf, server_id, cron de arquivamento). Documentado na seção SETUP, mas não automatizável pelo framework.
- **"Recuperação ao segundo" não é entregue** — é "perda de minutos" via dump+binlog. Zero perda exigiria replicação síncrona, deliberadamente fora de escopo.
- **Backup testado = responsabilidade do operador.** Script de restore existe, mas "backup não-testado não é backup" — operador precisa rodar restore de teste periodicamente. Framework documenta isso mas não força.
- **rclone/b2 CLI precisam estar instalados e configurados na VPS.** Pré-requisito externo.

### 2026-05-22 — v0.9.3 — "Deploy-safety: symlink atomic, release-auditor, anti-Turborepo"

**Contexto:**
Operador perguntou se devia incluir Turborepo para "deploy seguro e confiável" no monorepo. Análise (pesquisa 2026 + retros) concluiu: **Turborepo não resolve o problema**. Turborepo é orquestrador de build/cache JS-first; não faz deploy seguro (rollback, health check, canary). Para stack FastAPI+Angular+Capacitor (3 dirs poliglotas), cobriria só Angular (que já tem cache nativo) e ignoraria Python (não suporta uv/poetry).

Os problemas reais de deploy nos retros (Rota Certa phase-09: secrets/plists/app records faltando; Augur phase-11: smoke tests/scans pendentes) são **release readiness**, não build orchestration.

v0.9.3 ataca o problema real com 4 entregáveis.

**4 entregáveis:**

**1. Skill `domain/monorepo-deploy-safety` (DECISION-55a)**

Estratégia padrão: **symlink atomic deploy** (releases versionadas + `current` symlink + `shared/` para config/logs/uploads). Blue-green documentado como upgrade futuro condicional (só com SLA contratual, tráfego alto, ou downtime que custa dinheiro).

Conteúdo:
- Tabela symlink vs blue-green (quando cada um)
- Estrutura de diretórios `/opt/{app}/{releases,shared,current}`
- 5 invariantes que symlink impõe ao código DESDE A PHASE 1 (sem paths hardcoded, secrets em shared, logs/uploads em shared, app lê via current/, migrations forward-only)
- Ordem de deploy poliglota (migrations → backend → switch → frontend → health check)
- Expand-contract para migrations destrutivas
- Mobile (Capacitor) fora do ciclo de symlink
- **Seção anti-Turborepo:** quando usar orquestrador (Nx se 4+ pacotes TS; nenhum se 3 dirs poliglotas; nunca Turborepo na stack Angular)

**2. Agent `gsd-release-auditor` (DECISION-55b)**

7 dimensões de release readiness (distintas de qualidade de código): secrets & env vars, mobile release artifacts, migrations readiness, deploy-safety invariantes, smoke & quality gates, observability readiness, CI/CD pipeline.

Cada check tem origem rastreável a retro real. Output `file:line:severity:fix` com checklist de release-safety item a item.

**3. Template `bin/deploy-atomic.sh` (DECISION-55c)**

Script cross-platform executável implementando os 9 passos do symlink atomic deploy: pre-flight (env-smoke-check), criar release, migrations antes do switch, switch atômico (`mv -T`), graceful reload, nginx reload, health check, rollback automático em fail, cleanup (retém últimas 5). Suporta `--rollback` e `--dry-run`. Testado em dry-run.

**4. Conexão ao autopilot (DECISION-55d)**

Novo Step 5.2.5 no workflow autopilot: release-auditor dispara após squad-audit em phases pre-release. BLOCKER bloqueia milestone close com opção de "fechar sem deploy (código pronto, deploy depois)". Release-auditor também adicionado à squad-audit do orchestrator (5ª dimensão).

**Decisão sobre Turborepo (registrada para referência):**

NÃO incluído. Razões:
- Turborepo é Next.js/React-first; stack usa Angular
- Cache não entende uv/poetry (Python fica de fora)
- Remote cache é Vercel-centric; deploy é VPS
- Não faz deploy "seguro" (é build cache, não release safety)
- Para 3 dirs poliglotas, Makefile + scripts bastam

Se algum projeto crescer para 4+ pacotes TS compartilhados (design system como pacote, libs), recomendação é **Nx** (Angular-first, plugin Python), não Turborepo. Documentado na skill.

**Contadores v0.9.3:**

- 67 skills (era 66; +1: monorepo-deploy-safety)
- 44 agents (era 43; +1: release-auditor)
- 91 commands (mesmo)
- 19 hooks (mesmo)
- 350 permissions (mesmo)
- 6 bin scripts (era 5; +1: deploy-atomic.sh)

**O que esta versão NÃO resolve (honesto):**

- **deploy-atomic.sh é template, não plug-and-play.** Precisa adaptar paths, service names, comandos ao projeto. Testado só em dry-run (não há VPS no ambiente de dev do framework).
- **release-auditor usa análise estática.** Não valida rollback real, load test, ou scan — esses precisam de staging. Declara isso honestamente no output.
- **Blue-green não foi implementado.** Documentado como upgrade futuro, mas sem template. Se algum projeto precisar, é trabalho novo.
- **Sem field data ainda do deploy-safety.** Skill e auditor calibrados com retros de problemas passados, mas o symlink atomic em si não rodou em deploy real via framework. Próximo deploy de Áugure/Pulso valida.

### 2026-05-15 — v0.9.2 — "Calibração com 30 retros de campo (Rota Certa, Augur, Alfie)"

**Contexto:**
Análise de 30 retrospectivas de campo distribuídas em 3 projetos sérios:
- **Rota Certa** (9 phases, delivery mobile SaaS)
- **Augur** (12 phases, plataforma simulação B2B)
- **Alfie** (9 phases, AI conversational)

Pattern identificado: framework tinha **gates fortes** mas **gaps de profundidade**. Especificamente:
- **43% dos retros mencionam friction de setup** (uv sync conflito, alembic env.py errado, ng build pré-existente quebrado, pythonpath ausente)
- **27% mencionam TD acumulando** sem resolução (mesmo bug TS aparecendo em 3 phases consecutivas)
- **~7% de bugs passaram pelo plan-checker** por validar existência, não assinatura

v0.9.2 endereça **os 3 gaps cirurgicamente**, sem tocar na orquestração v0.9.1.

**3 melhorias implementadas:**

**1. `bin/env-smoke-check.sh` — Hook environment validation (DECISION-52)**

Script cross-platform que valida ambiente ANTES de phase começar:
- Git working tree clean
- Python: versão, uv lock sync, venv existe, pythonpath em pyproject.toml
- Node: versão >=18, package manager certo pelo lockfile, node_modules existe, tsc --noEmit errors
- DB: clientes disponíveis, alembic/env.py respeita TEST_DATABASE_URL, redis ping
- TD aging: blockers em aberto bloqueiam phase
- Disk space (<2GB blocker)

**Integrado em autopilot Step 4.1.5** (entre banner e skip), antes de qualquer trabalho.

Exit codes: 0=ok, 1=blocker, 2=warning. Customização via `GSD_ENV_SMOKE_SKIP` e `GSD_ENV_SMOKE_STRICT`.

**Cobertura empírica:**
- Rota Certa phase-03 `arq + redis conflict` → pego
- Rota Certa phase-02 `pythonpath ausente` → pego
- Rota Certa phase-04 `alembic env.py errado` → pego
- Rota Certa phases 2-4 `TS errors acumulando` → pego como blocker (>=10 errors)
- Alfie phase-31 `Tailwind v4 PostCSS` → pego no ng build check

**2. Hook `gsd-td-aging.js` + Command `/gsd:td-review` (DECISION-53)**

Hook SessionStart analisa `TECH-DEBT.md` cruzando com retros em `.planning/retros/` para detectar TDs aparecendo em N phases consecutivas. Quando excede threshold da urgency_class, propõe promoção:

| Urgency atual | Threshold (phases) | Promoção sugerida |
|---|---|---|
| post_launch_quarter | 4 | post_launch_30d |
| post_launch_30d | 3 | pre_launch_high |
| pre_launch_medium | 3 | pre_launch_high |
| pre_launch_high | 2 | pre_launch_blocker |
| pre_launch_blocker | 1 | bloqueia phase atual |

Command `/gsd:td-review` revisa interativamente com 3 ações por TD aging:
- **Promover** urgency_class
- **Resolver agora** (cria phase de fix)
- **Aceitar como ADR** (vira decisão consciente em `docs/adrs/`)

**Cobertura empírica:**
- Rota Certa: bug TS2352/TS2322 mencionado em phases 2, 3, 4 como "out-of-scope" → seria promovido após phase 4
- Rota Certa: alembic env.py issue desde phase 03-01 nunca resolvida → seria promovido para pre_launch_high
- Alfie: 9 TDs registradas na phase 31 → começam a ser monitoradas a partir da phase 32

**3. Plan-checker Dimension 13 — API Surface Compliance (DECISION-54)**

Nova dimensão valida que PLAN.md referencia funções/classes/endpoints com **assinaturas corretas**, não apenas que existem:

- Function signatures: parâmetros declarados vs usados
- Schema fields: nomes reais da tool vs assumidos no PLAN
- Endpoint paths: prefix completo (`/api/v1/` vs `/v1/`)
- Dead code parallelism: warning se função paralela criada quando canônica existe

Skip automático se PLAN.md greenfield (sem refs a código existente).

**Cobertura empírica:**
- Alfie phase-26 `LLM factory auto-wrap` → detectado como signature mismatch
- Alfie phase-28 `schemas assumidos incorretamente` → detectado como schema field mismatch
- Rota Certa phase-08 `_compute_and_persist_single` dead code → detectado como parallelism warning
- Rota Certa phase-04 `/v1/ vs /api/v1/` → detectado como endpoint path mismatch

**Contadores v0.9.2:**

- 66 skills (mesmo)
- 43 agents (mesmo)
- 91 commands (era 90; +1: td-review)
- 19 hooks (era 18; +1: td-aging)
- 350 permissions (mesmo)
- 11 env vars (era 10; +1: GSD_TD_AGING_ENABLED)
- `bin/env-smoke-check.sh` novo (370 linhas, cross-platform)
- Plan-checker Dimension 13 adicionada (~110 linhas)

**O que esta versão NÃO resolve (honesto):**

- **Hooks não modificam arquivos automaticamente.** TD aging hook só alerta — operador decide via `/gsd:td-review`. Decisão consciente (vs auto-promoção arriscada).
- **Plan-checker Dimension 13 depende de grep/Glob.** Não é AST parse real. Pode dar falso positivo em funções com nomes muito comuns.
- **Env-smoke-check pode dar falso bloqueio em projetos não-convencionais.** `GSD_ENV_SMOKE_SKIP` existe para isso, mas precisa ser configurado caso a caso.
- **Falsos positivos de code reviewer (~7% no campo) não foram endereçados.** Rota Certa phase-07 mostrou caso onde reviewer reportou CRITICAL em código real. Solução requer mudança no `gsd-code-reviewer` agent, fica para v0.10.

### 2026-05-15 — v0.9.1 — "Conexões: ingestor↔autopilot, squad automático, e2e test"

**Contexto:**
v0.9.0 entregou peças (pasta projeto/, ingestor, squad-orchestrator, 4 audit agents) mas **não conectou as peças entre si**. Operador precisava saber manualmente que após `/gsd:ingest` deveria rodar `/gsd:bootstrap` depois `/gsd:autopilot`. Squad só era chamado se operador digitasse `/gsd:squad` manualmente. Não havia teste de integração ponta-a-ponta.

v0.9.1 fecha esses gaps com 8 conexões.

**8 conexões implementadas:**

**1. INGESTOR-HANDOFF.json (DECISION-48)**

Ingestor termina sempre escrevendo `.planning/INGESTOR-HANDOFF.json` — contrato machine-readable que o autopilot lê. Contém: counts (REQs, milestones, phases, open_questions_blocking, conflicts), `ready_for_autopilot: bool`, `suggested_command`, milestone_overview.

Substitui o handoff implícito por handoff explícito.

**2. Wireframes HTML/JSX/Vue/Svelte como caso especial (DECISION-49)**

Ingestor agora trata `.html`, `.jsx`, `.tsx`, `.vue`, `.svelte` **não como imagem** mas com extração estruturada:
- Árvore de componentes detectada (Sidebar, Card, Input)
- Navegação mapeada via `<a href>` e `<button onClick>`
- Estados detectados (loading, error, empty, success)
- Tokens extraídos de CSS/Tailwind classes (cores, spacing, fontes)
- Resultado vira REQ específico e seção em `design-system/MASTER.md`

Suporta output de Lovable/v0/bolt sem perda de informação.

**3. Autopilot Fase 0 — leitura do handoff (DECISION-50)**

Workflow do autopilot ganha `<step name="0-read-ingestor-handoff">` que executa antes do bootstrap check. Detecta `.planning/INGESTOR-HANDOFF.json`, valida `ready_for_autopilot`, **bloqueia** se há Open Questions bloqueantes não-resolvidas, mostra banner informativo se OK.

**4. Bootstrap routing automático**

`/gsd:bootstrap` agora detecta:
- Se `projeto/` tem conteúdo → redireciona para `/gsd:ingest` (caminho preferido)
- Se `docs/project-brief.md` + `specs/` existem → fluxo clássico (compat)
- Se nada existe → orienta operador a escolher

Criado também o **command** `/gsd:bootstrap` que estava faltando (workflow existia mas sem command frontend).

**5. Autopilot invoca squad em 3 pontos automáticos (DECISION-51)**

- **4.2.5 squad-research** (antes de discuss-phase, se ROADMAP marca)
- **4.9.5 squad-review** (depois de execute+verify, se ROADMAP marca) — CRITICAL bloqueia avanço
- **5.2 squad-audit** (antes de complete-milestone, se há phase com `is_pre_release: true`) — CRITICAL bloqueia close

Decisão de "qual squad disparar" é pré-feita pelo ingestor no ROADMAP (campo `Squad recomendado:`). Autopilot só obedece. Não há paralelismo cego.

**6. Ingestor gera ROADMAP executável com skills pré-citadas**

ROADMAP gerado pelo ingestor tem TODOS os campos que o autopilot precisa para executar sem inferir:
- Flags (`has_ui`, `has_ai`, `has_pii`, `is_pre_release`, etc.)
- Skills obrigatórias pré-citadas baseado em flags (matriz de obrigatoriedade documentada na Fase 6.5 do ingestor)
- Squad recomendado por phase (pre-phase, post-execute, pre-release)
- Verificações automatizadas (truths verificáveis)
- Dependências entre phases

Resultado: `gsd-plan-checker` aceita PLAN.md sem questionar skills (foram pré-aprovadas no ROADMAP).

**7. Hook projeto-watcher**

Novo hook `SessionStart` (`gsd-projeto-watcher.js`) compara mtime de `INGESTOR-HANDOFF.json` com mtime mais recente de arquivos em `projeto/`. Se há arquivos novos/modificados desde o último ingest, mostra aviso sugerindo `/gsd:ingest --only=requirements`. Não bloqueia — apenas alerta.

**8. Teste e2e do fluxo principal**

Novo `tests/integration/test_e2e_ingest_autopilot.sh` com **65 assertions** em 12 suites cobrindo:
- Estrutura da pasta projeto/
- Agent ingestor produz contratos esperados
- Commands ingest e bootstrap funcionam
- Autopilot lê handoff e invoca squad nos 3 pontos
- Squad orchestrator e 4 audit agents existem
- Hook projeto-watcher tem sintaxe válida e está no settings
- Permissions cross-platform
- ERRATA eliminada
- Todos os 14 hooks JS têm sintaxe válida

Executado: **65/65 passed**. Roda em <2s. Não exige LLM (valida apenas estrutura).

**Contadores v0.9.1:**

- 66 skills (mesmo de v0.9.0)
- 43 agents (mesmo)
- 90 commands (era 89; +1: bootstrap)
- 18 hooks (era 17; +1: projeto-watcher)
- 350 permissions (mesmo)
- 10 env vars (era 9; +1: GSD_PROJETO_WATCHER_ENABLED)
- Total zip: ~2.2MB

**O que esta versão NÃO resolve (honesto):**

- **Ainda sem field data.** v0.9.0 e v0.9.1 não rodaram em projeto real. Conexões implementadas com base em raciocínio sobre fluxo, não em medição de campo. v0.10 vai calibrar.
- **Squad recommendation no ROADMAP é heurística.** A matriz "3+ flags = squad-research" é razoável mas não validada empiricamente. Em campo, pode ser que phases com 2 flags + has_ai já justifiquem squad.
- **Ingestor com 9-fase workflow é ambicioso.** Em projetos médios (20+ arquivos com PDFs grandes), pode estourar contexto na fase de leitura. Detecção automática de "preciso fragmentar" não foi implementada — fica como pré-condição manual.
- **Wireframe HTML extração depende de qualidade do markup.** Output de Lovable é bom (componentes nomeados, semantic HTML); HTML legado com `<div>` everywhere reduz utilidade da extração estruturada.
- **CRITICAL bloqueando autopilot pode frustrar.** Se squad-audit acha CRITICAL em pre-release, autopilot para e pede decisão humana. Em sessões longas, isso é bem-vindo; em batch overnight runs, é fricção.

### 2026-05-15 — v0.9.0 — "Autossuficiência: projeto/, squad paralelo, permissões totais, sem erratas"

**Contexto:**
v0.8.1 entregou skills UX. v0.9.0 é **rework arquitetural** baseado em 6 demandas do operador: (1) eliminar ERRATA.md, (2) pasta `projeto/` para auto-bootstrap, (3) mais agents paralelos, (4) permissões cross-platform totais, (5) framework como equipe de devs/infra/back/db, (6) skills pente fino.

**5 mudanças desta versão:**

**1. Pasta `projeto/` de entrada (DECISION-43)**

Pasta single-purpose onde operador joga inputs do projeto em qualquer formato (MD, PDF, PNG, YAML, DOCX). 7 subpastas semânticas (regras-negocio, wireframes, identidade-visual, stacks, docs-externos, referencias, decisoes-existentes). Comando `/gsd:ingest` aciona agent `gsd-project-ingestor` que lê tudo recursivamente, extrai estrutura, detecta conflitos, gera `.planning/` completo (PROJECT, REQUIREMENTS, MILESTONES, ROADMAP, STATE, DECISIONS, TECH-DEBT, SUGGESTIONS), `docs/` (personas, glossário, identidade-visual, integrações, regras de negócio) e `design-system/MASTER.md` (se houver material visual). Produz `DISCOVERY-REPORT.md` na raiz com extração, assumptions, open questions, conflitos detectados.

Substitui completamente o bootstrap manual. Operador agora não preenche `.planning/` na mão.

Princípios: agent **nunca modifica** `projeto/` (input one-way), cita arquivo+linhas em todo REQ gerado, idempotente (pode re-rodar).

**2. ERRATA.md eliminado (DECISION-44)**

Decisão editorial: framework não deve ter erratas. Conteúdo dividido em 2 docs honestos:

- `docs/PLATFORM-NOTES.md` — Win/Mac/Linux specifics, sintaxe por shell, pré-requisitos, FAQ
- `docs/KNOWN-LIMITS.md` — 12 limitações conscientes documentadas (não bugs, escolhas de escopo)

Documentação interna inline corrigida: 270+ refs `/gsd-` migradas para `/gsd:` (formato canônico Claude Code 2026+); 4 commands inexistentes (`/gsd-sprint-plan`, `/gsd-reconcile-state`, `/gsd-metrics`, `/gsd-verify-phase`) substituídos pelos commands reais em todos os guias.

Após v0.9.0, o que o framework promete = o que o framework faz.

**3. Permissões totais Win/Linux/macOS (DECISION-45)**

`.claude/settings.json` expandido de 174 → **350 allow entries**. Cobertura cross-platform:

- **Shells:** bash, zsh, fish, dash, ksh, PowerShell (`pwsh`, `powershell.exe`), cmd.exe
- **Package managers:** npm, yarn, pnpm, bun, pip, uv, poetry, conda, mamba, cargo, gem, composer, dotnet, brew, apt, dnf, pacman, snap, flatpak, winget, choco, scoop
- **Frameworks:** ng, ionic, capacitor, expo, react-native, flutter, dart, xcodebuild, gradle, mvn, fastlane, adb
- **Infra:** docker, kubectl, helm, terraform, tofu, ansible, packer, vagrant, pulumi
- **Cloud CLIs:** aws, gcloud, az, doctl, fly, railway, heroku, vercel, netlify, wrangler
- **DBs:** mysql, psql, redis-cli, mongo, mongosh, sqlite3, litecli, cqlsh, influx
- **PowerShell cmdlets:** Get-*, Set-*, New-*, Remove-*, Move-*, Copy-*, Test-*, Invoke-*, Expand-Archive
- **macOS:** open, brew, port, osascript, pbcopy, pbpaste, launchctl, diskutil
- **Windows-native:** winget, choco, scoop, where, takeown, icacls, robocopy

`defaultMode: bypassPermissions` mantido. Campo `_note_for_claude` instrui zero diálogos exceto destrutivo claro (rm -rf /, drop database produção, push --force em main).

Resultado: zero "Allow this action?" no fluxo normal de dev/infra/QA.

**4. Squad de agents paralelos (DECISION-46)**

Arquitetura nova: `gsd-squad-orchestrator` dispara N agents em paralelo via Task tool e sintetiza outputs. 3 squads pré-configurados:

- **squad-research** (pre-phase): domain + ui + ai + security researchers em paralelo → consolidated-research.md
- **squad-review** (post-execute): code-reviewer + security-auditor + integration-checker + ui-auditor em paralelo → consolidated-review.md  
- **squad-audit** (pre-release): performance + accessibility + i18n + observability auditors em paralelo → consolidated-audit.md

Comando: `/gsd:squad research|review|audit --phase=NN`.

**Princípio honesto:** paralelismo apenas onde dimensões são ortogonais. Planning, execução, decisão continuam serial (state machine). Squad não é "10 devs trabalhando ao mesmo tempo" — é "4 perspectivas independentes seguidas de síntese".

Latência: ~2-3min (squad) vs 8-12min (serial dos 4). Custo: ~4x tokens. Qualidade: comparável ou superior (perspectivas diversas pegam coisas que single-pass perde).

**5. 4 novos audit agents dimension-specific (DECISION-47)**

Suportam squad-audit:

- `gsd-performance-auditor` — 6 dimensões (Web Vitals LCP/CLS/INP, bundle size, DB N+1, API perf, cache, build/CI)
- `gsd-accessibility-auditor` — 8 dimensões (semantic HTML, ARIA, focus, keyboard, touch targets ≥44pt, motion, contraste WCAG AA, forms)
- `gsd-i18n-auditor` — 6 dimensões (strings hardcoded, formatação locale-aware, pluralização, RTL, encoding, locale propagation)
- `gsd-observability-auditor` — 5 dimensões (error tracking Sentry, structured logging, metrics 4 golden signals + business, distributed tracing OpenTelemetry, alerting baseline)

Cada agent: output em formato `file:line:rule_id:severity:description`, agrupado por severity (CRITICAL > HIGH > MEDIUM > LOW), com fix sugerido, esforço estimado, e seção "não verificado" honesta.

**Contadores v0.9.0:**

- 66 skills (mesmo de v0.8.1)
- 43 agents (era 37 em v0.8.1; +6: project-ingestor, squad-orchestrator, performance/accessibility/i18n/observability auditors)
- 89 commands (era 87; +2: ingest, squad)
- 17 hooks (mesmo)
- 350 permissions allow entries (era 174)
- Total framework descompactado: ~10MB; zip: ~2.3MB

**O que esta versão NÃO resolve (honesto):**

- **Sem field data ainda das mudanças.** `projeto/` ingestion e squad paralelo precisam testar em projeto real para validar. v0.10 vai calibrar com telemetria.
- **`gsd-project-ingestor` é ambicioso.** 9-fase workflow para ler qualquer formato, extrair estruturado, detectar conflitos, gerar 8 docs de `.planning/` + design system. Em projetos médios (20+ arquivos), pode estourar contexto. Mitigação: lê em chunks, mas não testado em escala.
- **Squad paralelo custa 4x tokens.** Use com critério. Não vire default — só onde justifica (pre-release, phase complexa).
- **350 permissions é amplo.** `_note_for_claude` instrui prudência, mas se há risco real de comando destrutivo, dependemos de Claude usar juízo. Para ambientes corporate/auditoria, considere `defaultMode: "acceptEdits"` em vez de `bypassPermissions`.
- **Skills pente fino skipped.** 66 skills atuais são sólidas; adicionar mais sem field data seria especulação. Mantido como está.

### 2026-05-09 — v0.8.1 — "Skills UX calibradas com pesquisa de campo"

**Contexto:**
v0.8.0 entregou todos os 17 itens do diagnóstico Rota Certa. Após release, pesquisa nos últimos 15 dias do ecosistema de skills Claude Code (mar–mai 2026) identificou: (1) `ui-ux-pro-max` v2.1 (major upgrade do autor já confiado em v0.8.0), (2) skills vetted da Vercel Labs que cobrem gaps específicos. Decisão: incluir cirurgicamente em v0.8.1 sem alterar core do framework.

**3 mudanças desta versão:**

**1. ui-ux-pro-max upgraded v1 → v2.1 (DECISION-39)**

Substituição completa do conteúdo de `.claude/skills/ui-ux-pro-max/`:

| Métrica | v1 | v2.1 |
|---------|-----|------|
| Estilos visuais | 67 | **84** |
| Paletas de cores | 96 | **161** |
| Product types | 95 | **161** com Reasoning Rules |
| Font pairings | 56 | **73** + 1924 google fonts indexed |
| Stacks | 13 | **16** (+Angular, Astro, Laravel, Three.js, Jetpack Compose) |
| SKILL.md | 377 linhas | **658 linhas** |
| Engine | Search simples | **BM25 + 5 buscas paralelas + reasoning rules JSON** |
| Persistência | ❌ | ✅ `design-system/MASTER.md` + page overrides |
| Pre-delivery checks | ❌ | ✅ Validação contra anti-patterns |

**Security check executado:**
- ✅ Zero `urllib`, `requests`, `socket`, `subprocess`, `os.system`, `exec()`, `eval()` em scripts Python
- ✅ Zero prompt injection patterns em SKILL.md (apenas `password-toggle` legítimo em UX rules)
- ✅ Imports só de stdlib + locais (csv, re, json, os, datetime, pathlib, math, collections)
- ✅ Autoria vetted (29.6k stars, MIT, mantida)

**2. Skill nova: `meta/composition-patterns` (DECISION-40)**

Adaptado de [vercel-labs/agent-skills/composition-patterns](https://github.com/vercel-labs/agent-skills) (MIT, 19k stars). Resolve "boolean prop proliferation" via:
- Compound components (Radix-style: `<Select>`, `<Select.Trigger>`, `<Select.Content>`)
- State lifting via providers
- Explicit variants em vez de boolean modes
- Children sobre render props
- React 19 APIs (use, actions, useFormStatus)

Trigger: componentes com 5+ booleans, design de API de component library, refactor de design system.

**3. Skill nova: `quality/web-design-audit` (DECISION-41)**

Adaptado de [vercel-labs/agent-skills/web-design-guidelines](https://github.com/vercel-labs/agent-skills) (MIT, 133k installs/sem). Auditoria sistemática contra 100+ regras de Web Interface Guidelines (Vercel Engineering): ARIA & Semantic HTML, Focus & Keyboard, Forms, Touch & Pointer (44pt min), Motion (reduced-motion respect), Heading hierarchy, Color & Contrast (WCAG AA min), Performance (LCP, CLS, layout shift).

Diferença vs `quality/accessibility-pro`: accessibility-pro é WCAG-narrow durante implementação; web-design-audit é cobertura ampla **ao final da phase**. Use AS DUAS.

**4. Documentação `/gsd:` vs `/gsd-` em ERRATA (DECISION-42)**

Esclarecimento honesto: o framework usa subdiretório `commands/gsd/` (formato canônico Claude Code 2026+), então o prefixo correto é `/gsd:` (dois pontos). A documentação interna ainda usa `/gsd-` (~270 refs) por inércia histórica. Não fizemos search-replace cego (risco > benefício). Documentação foi corrigida inline em todos os guias e CLAUDE.md. `/gsd:` em autocomplete.

**Contadores v0.8.1:**

- 46 skills (era 44; +2 novas + 1 upgraded)
- 16 hooks (mesmo de v0.8.0)
- 174 permissions allow entries (mesmo)
- ui-ux-pro-max: 36 arquivos / 1.8MB (era 4 arquivos / 48KB sem dados sincronizados na v0.8.0)
- Total framework descompactado: ~9MB; zip: ~2.0MB (era 1.9MB)

**O que esta versão NÃO resolve (honesto):**

- **Sem field data ainda da v0.8.x.** Nenhum projeto rodou com hooks novos da v0.8.0; v0.8.1 adiciona mais sem ter feedback do que já entregou. Mitigação: skills novas são tier 2 (não bloqueiam por default) e ui-ux-pro-max v2.1 é substituição direta de skill já existente.
- **`ui-ux-pro-max` triggers.yaml foi recriado**, não migrado. v1 tinha 5 linhas; v2.1 tem 80 linhas. Pode mudar comportamento do skill-loader em casos edge.
- **Plan-checker pode citar skills demais** entre `ui-ux-pro-max` (broad), `meta/composition-patterns` (narrow), `quality/web-design-audit` (audit). SKILLS_INDEX documenta diferenças mas orquestrador pode pecar por excesso.
- **Não foi feito search-replace `/gsd-` → `/gsd:`** em 270+ refs. Documentação inline corrigida: 270+ refs migradas de `/gsd-` para `/gsd:`.

### 2026-05-09 — v0.8.0 — "Calibração com field data: Rota Certa diagnóstico"

**Contexto:**
v0.7.x foi a primeira versão a rodar em projeto real (Rota Certa: mobile delivery SaaS, 9 phases completadas, 233 commits, 2 milestones). O diagnóstico estruturado retornado pelo Claude que executou listou **17 issues** em 4 buckets: (A) bugs reais, (B) mecanismos prometidos que não funcionam, (C) gaps de rastreamento, (D) ambiente/DX.

v0.8.0 endereça **todos os 17 itens** usando o input de campo como gabarito, não palpite.

**Bucket A — Bugs reais corrigidos:**

- **DECISION-28: Multi-milestone STATE.md corruption.** `getMilestoneInfo()` em `lib/core.cjs` reescrevia `milestone: v1.0 / status: completed` mesmo com v1.1 in_progress (4x em 2 sessões na Rota Certa). Loop de corrupção: STATE corrompido → tools confirma → reescreve → continua corrompido. **Fix**: hierarquia de fontes refeita: (1) MILESTONES.md `in_progress` é authoritative agora, (2) ROADMAP.md `🚧` marker, (3) heading + marker próximo, (4) cleaned heading. Test de regressão `tests/framework/test_state_integrity.sh` (3 cases) — todos verde.

- **DECISION-29: settings.json formato canônico + PowerShell.** v0.7.x usava formato `{command, args}` que é incompatível com Claude Code 2.x+ (formato canônico é `{type, command}`). Também faltava PowerShell explícito (`powershell.exe`, `pwsh`, `cmd.exe`, `.ps1`). v0.9.0 settings.json reescrito com 165 entries em formato canônico, suporte Linux/macOS/Windows.

- **DECISION-30: Changelog grep e placeholders no CI** (template-level). Adicionado `templates/workflows/release-validation.yml` com pattern correto `^(feat|fix)(\(.*\))?!?:` (aceita escopo) e `validate-placeholders` job. Templates não bloqueiam — projetos copiam para seus workflows.

**Bucket B — Mecanismos não-funcionais agora ativos:**

- **DECISION-31: METRICS.md auto-trigger.** `bin/collect-metrics.sh` existia em v0.7.x mas exigia rodada manual que ninguém lembrava. Hook novo `gsd-metrics-trigger.js` (PostToolUse) detecta SUMMARY.md de fim-de-phase e dispara o script automaticamente. Idempotente: não duplica entry.

- **DECISION-32: SUGGESTIONS.md detector.** Hook novo `gsd-suggestion-detector.js` (PostToolUse) escaneia SUMMARY/RETRO/VERIFICATION por keywords ("descobri", "armadilha", "lição", "pitfall", etc.). Se detectar 2+ indicadores e SUGGESTIONS.md vazio → alerta loud com instrução de promover insights.

- **DECISION-33: Tech debt surfacing no PLAN.md.** Template PLAN.md ganhou seção "Tech debt deste plano (verificação obrigatória v0.8+)". Plan-phase deve consultar TECH-DEBT.md e listar TDs com prazo na phase atual ou urgency_class apropriado. TECH-DEBT.md formaliza `urgency_class` (pre_launch_blocker/high/medium, post_launch_30d/quarter, wont_fix_documented) com critérios de promoção.

**Bucket C — Gaps de rastreamento fechados:**

- **DECISION-34: LOW confidence items.** Template PLAN.md ganhou seção "Open questions / LOW confidence do RESEARCH (obrigatório se RESEARCH tem itens LOW)". Cada LOW confidence vira task explícita ou TD formal — não pode mais ficar invisível em RESEARCH.md.

- **DECISION-35: Skills citação ≠ aplicação.** Hook novo `gsd-skill-application-check.js` (PostToolUse) compara skills citadas em PLAN.md com fingerprints (imports + keywords) no código + SUMMARY/DECISIONS. Skill citada mas sem fingerprint detectado vira WARNING. Cobre 12 skills com fingerprint definido (observability-production, accessibility-pro, owasp-security, lgpd-compliance, llm-integration-patterns, etc.). Detectou exatamente o caso Sentry da Phase 9 Rota Certa em teste.

- **DECISION-36: HUMAN-UAT-BACKLOG consolidado.** Template novo `.planning/HUMAN-UAT-BACKLOG.md` (status counters: pendentes, validados, falharam, bloqueados). Hook `gsd-uat-promoter.js` (PostToolUse) auto-promove items human_needed de VERIFICATION.md/HUMAN-UAT.md para o backlog. Idempotente: detecção por ID + título evita duplicação.

- **DECISION-37: Fix rate categorizado.** `bin/categorize-fixes.sh` separa `fix(review)` e `fix(integration)` (esperados — framework funcionou) de `fix(escape)` (bug que escapou — sinal real). Reporta escape rate com tiers (excelente <5%, saudável <10%, aceitável 10-25%, alto >25%). Convenção de commit documentada em `templates/workflows/README.md`.

**Bucket D — Ambiente e DX:**

- **DECISION-38: ERRATA Windows/PowerShell.** Seção em ERRATA documentou (em v0.9 movida para docs/PLATFORM-NOTES.md): 6 problemas redescobertos sessão após sessão: heredoc bash, `uv run` trampoline, `python -m pytest`, paths `/` vs `\`, `gh` auth por shell, scripts `.sh` no Windows. Para cada problema, workaround documentado.

**Hooks novos (v0.9.0):**

| Hook | Trigger | Função |
|------|---------|--------|
| `gsd-state-integrity-check.js` | SessionStart | Detecta STATE.md corrompido na entrada da sessão |
| `gsd-state-guard.js` | PostToolUse | Detecta corrupção em runtime após modificações |
| `gsd-suggestion-detector.js` | PostToolUse | Detecta keywords de insight em SUMMARY/RETRO |
| `gsd-skill-application-check.js` | PostToolUse | Compara skills citadas vs aplicadas no código |
| `gsd-metrics-trigger.js` | PostToolUse | Auto-roda collect-metrics.sh ao fechar phase |
| `gsd-uat-promoter.js` | PostToolUse | Auto-promove human_needed para HUMAN-UAT-BACKLOG |

Total hooks v0.9.0: **15** (era 9 em v0.7.x; + 6 novos).

**Templates atualizados:**

- `templates/PLAN.md` — 2 seções novas obrigatórias (Tech debt deste plano + LOW confidence handler)
- `.planning/TECH-DEBT.md` — formalização de `urgency_class`
- `.planning/HUMAN-UAT-BACKLOG.md` — template novo
- `templates/workflows/release-validation.yml` — exemplo de CI com validate-placeholders + changelog correto

**Tests:**

- 5/5 suites originais continuam verde
- 1 suite nova: `test_state_integrity.sh` (3 cases para getMilestoneInfo prioritization)
- **Total: 6/6 suites passing**

**O que esta versão NÃO resolve (honesto):**

- **Skill fingerprints incompletos.** `gsd-skill-application-check.js` cobre 12 skills com fingerprint. As outras ~52 skills não têm fingerprint — pular silenciosamente. Adicionar fingerprints conforme observação de campo nos próximos releases.
- **Plan-checker dimension 7 (TECH-DEBT integration) não foi adicionada.** Template PLAN.md exige seção mas plan-checker ainda não valida automaticamente que ela está preenchida com dados reais. Mitigação: revisão visual humana (ainda).
- **MILESTONES.md ainda assume formato tabela.** Heurística de detecção pode falhar em formatos exóticos. Cobertura testada: tabela com `in_progress` ou `⏳`.
- **`gsd-uat-promoter.js` modifica HUMAN-UAT-BACKLOG.md sem confirmação.** Hook escreve direto no arquivo. Aceitável porque é idempotente, mas pode surpreender em primeiro uso. Documentado.
- **Auto-promoção produz items com placeholders.** Items extraídos viram entries com "Tipo: [auto-extraído — refinar]" e "Pré-condição: [preencher]". Operator precisa refinar antes do milestone fechar. Sem isso, backlog vira ruído.

### 2026-04-29 — v0.7.x — "Skill enforcement automático + permissões completas"

**Contexto:**
v0.7.0 entregou 12 skills densificadas mas dependia de Claude (orchestrator) ler manualmente os triggers.yaml para decidir quais skills carregar. Na prática isso falha — Claude não escaneia triggers automaticamente. Também: settings.json tinha permissões básicas mas faltavam comandos comuns (gh, ng generate, prisma migrate, kubectl, etc.) gerando prompts no meio do trabalho.

**3 mudanças desta versão:**

**1. Triggers enriquecidos (12 skills densificadas)**

Cada triggers.yaml das 12 skills densificadas agora tem:
- Campo `priority: high` para ordenação no skill-loader
- 8-15 keywords pt-BR + en por skill (vs ~5 na v0.7.0)
- Cobertura de phase_types específicos (ui-design, design-system, refactor-ui, dashboard, etc.)
- Flags adicionais (has_ui, has_external_users, has_async_operations, has_user_actions, no_dedicated_designer)

**2. Hook gsd-skill-loader.js (NOVO)**

UserPromptSubmit hook que:
- Escaneia prompt do user contra todos os triggers.yaml (64 skills)
- Detecta keywords com word boundary (evita "cor" matching em "score")
- Suporta keywords compostas pt-BR ("jornada do usuário", "dark mode")
- Lista até 5 skills mais relevantes no contexto
- Ordena por priority (high > medium > low) e section (required > recommended)
- Advisory only (não bloqueia)
- Habilitado via env var `GSD_SKILL_LOADER_ENABLED=1` (default: ativado)

Resolve gap fundamental: skill citada ≠ skill carregada. Agora o orquestrador VÊ no contexto quais skills aplicam.

**3. Permissões completas em settings.json**

Adicionadas ~50 entradas no allow list para evitar prompts no meio do trabalho:

- Tools: NotebookEdit, ExitPlanMode, BashOutput, KillBash
- Git: gh (GitHub CLI)
- TS/JS: tsc, tsx, ts-node, eslint, prettier, jest, vitest, playwright, cypress, stylelint, biome
- Python: uvx, basedpyright, pyright, flake8
- Outras langs: java, javac, mvn, gradle, php, composer, ruby, bundle, rails
- Mobile: expo, eas, react-native, flutter, dart
- Infra: kubectl, helm, terraform, ansible, podman
- DB: typeorm, drizzle-kit, mysql, psql, redis-cli, mongosh, sqlite3
- Utility: tar, unzip, zip, gzip, diff, patch, tree, stat, file, which, env, true/false
- Network: ssh, scp, ping, nslookup, dig, host, netstat, lsof
- Search: rg, ag, sed, awk, jq, yq, xargs, head, tail, sort, uniq, cut, tr, wc, tee
- Shell: zsh, fish
- Project: ./bin/*, ./scripts/*

`defaultMode: bypassPermissions` continua ativo. Lista `allow` é cinto-e-suspensórios para caso bypassPermissions seja revertido.

**Validação:**
- 5/5 testes verde (mantidos)
- Hook testado com 5 prompts diversos (positivos + negativos)
- Word boundary funciona com pt-BR (acentos preservados)
- JSON válido em settings.json

**Limitações ainda existentes:**
- 6 skills tier-2 não densificadas (decisão consciente, baixa frequência de uso)
- Field test ainda zero
- Triggers podem ter falsos negativos (humano pediu algo que skill cobre mas não tem keyword exata)
- Hook depende do orquestrador OBEDECER a sugestão (não força leitura, apenas exibe)

**Próximo passo crítico:**
Field test em projeto real ainda mais necessário. Com hook ativo, finalmente saberemos quais keywords estão calibradas e quais geram falsos positivos/negativos. Sem dado real de 3-5 phases, qualquer ajuste é palpite.

---


### 2026-04-29 — v0.9.0 — "Densificação de 6 skills críticas"

**Contexto:**
v0.6.0 entregou 18 skills externas integradas mas em densidade ~60% — cada skill tinha 200-400 linhas (essência preservada mas faltavam templates concretos, exemplos múltiplos, snippets prontos). User pediu densidade real "à altura do framework".

**Decisão:** densificar 6 skills mais críticas (mais usadas, base do fluxo) em vez de superficializar 18.

**Critério de seleção:**
- Mais usadas no fluxo (citadas em 5+ tipos de phase)
- Sem densidade adequada na v0.6.0
- Quando bem feitas, cobrem 70%+ das decisões de produto/UX

**6 skills densificadas:**

| Skill | v0.6.0 | v0.9.0 | Ganho |
|---|---|---|---|
| meta/jobs-to-be-done | 130 linhas | 801 linhas | 6.2x |
| meta/user-persona | 140 linhas | 846 linhas | 6.0x |
| quality/color-system | 280 linhas | 994 linhas | 3.5x |
| quality/heuristic-evaluation | 200 linhas | 940 linhas | 4.7x |
| ux-advanced/loading-states | 220 linhas | 798 linhas | 3.6x |
| meta/refactoring-ui | 250 linhas | 881 linhas | 3.5x |
| **TOTAL** | **1220** | **5260** | **4.3x** |

**Cada skill densificada inclui:**
- Templates copy-paste (3-4 por skill)
- Exemplos completos em 5+ domínios diferentes
- Snippets de código (React + Angular 19 + Ionic onde aplicável)
- Anti-patterns com correção lado a lado (5-8 por skill)
- Checklists de validação (15-20 itens)
- Cross-references explícitos com outras skills (input/output)
- Casos práticos brasileiros (Áugure)

**Limitações ainda existentes:**
- 12 skills do batch v0.6.0 ainda em densidade ~60% (densificar em v0.8/v0.9 conforme uso revelar prioridade)
- Triggers.yaml não calibrados com field data
- Sem teste real contra plan-checker em PLAN.md de produção
- Manual SKILLS-USAGE-MANUAL.md já reflete v0.9.0 mas alguns docs antigos não retraduzidos

**Próximo passo crítico:**
Field test em projeto real (Áugure ou novo). Sem isso, qualquer densificação adicional é palpite. As 6 skills densificadas precisam de 3-5 phases reais para revelar onde ainda há gap.

---


### 2026-04-28 — v0.9.0 — "Curadoria de 18 skills externas integradas"

**Contexto:**
User subiu 281 skills externas (designer-skills, skills-main/Bench, ui-ux-pro-max-skill, apple-skills,
agent-skills, bencium, refactoring-ui, interface-design) para análise de integração.

**Decisão:** integrar apenas as 18 que fecham lacunas reais e fazem sentido no fluxo gsd.
Descartar 263 que duplicam, são de stack errada (iOS/Swift) ou são conceituais demais.

**18 skills novas:**

Discovery e research (5):
- `meta/jobs-to-be-done` — JTBD framework para reframe de features
- `meta/user-persona` — personas acionáveis (não ornamentais)
- `meta/journey-map` — jornada end-to-end com curva emocional
- `meta/empathy-map` — síntese de pesquisa em 4 quadrantes
- `meta/competitive-analysis` — matriz comparativa estruturada

Estratégia de produto (3):
- `meta/opportunity-framework` — RICE/ICE/Impact-Effort
- `meta/north-star-vision` — visão norte + métrica única
- `quality/heuristic-evaluation` — Nielsen heuristics audit

Design system (5):
- `quality/design-token-architecture` — 3 camadas (primitive/semantic/component)
- `quality/spacing-system` — base unit + escala finita + tokens
- `quality/typography-scale` — modular ratio + line-height contextual
- `quality/color-system` — paleta + WCAG + daltonismo + dark mode
- `quality/layout-grid` — breakpoints + container + grid responsivo

UI patterns avançados (3):
- `ux-advanced/loading-states` — 4 níveis (spinner → optimistic)
- `ux-advanced/feedback-patterns` — toast/banner/modal/inline mapping
- `ux-advanced/data-visualization` — escolha de gráfico por intent + WCAG

Workflow design (2):
- `product/handoff-spec` — spec completo designer→dev
- `meta/refactoring-ui` — princípios anti-AI-slop

**Documento novo:**
- `docs/SKILLS-USAGE-MANUAL.md` (317 linhas) — mapa de quais skills consultar em cada
  momento do fluxo gsd. Organizado por momento (bootstrap, discuss-phase, ui-phase,
  research, plan, execute, verify, audit), não por categoria.

**Numericamente:**

| Componente | v0.5.0 | v0.9.0 |
|------------|--------|--------|
| Skills | 46 | **64 (+18)** |
| Triggers.yaml | 46 | **64** |

**O que foi descartado (263 skills) e por quê:**

- 141 skills Apple/iOS/Swift: stack errada
- 7 agent-skills (Vercel/React): você usa Angular + VPS
- ~30 skills filosóficas (clean-architecture, crossing-the-chasm, etc): vão como
  references canônicas em v0.6.1, não como skills enforced
- ~20 skills de marketing/vendas (predictable-revenue, scorecard-marketing, etc):
  fora do escopo de framework de execução
- ~10 skills bencium específicas (renaissance-architecture, negentropy-lens):
  filosóficas demais, não acionáveis
- ~50 skills duplicadas com o que já existe ou cobertas indiretamente

**Critério de inclusão:**
- Tem `triggers.yaml` calibrável (não filosófica)
- Fecha lacuna real do gsd v0.5.0
- Stack alinhada (Angular/Ionic/Python/MySQL)
- É operacional (passo a passo), não conceitual

**Limitações:**
- 18 skills foram criadas em pt-BR adaptadas, não copiadas literalmente — o conteúdo
  reflete a essência das skills externas mas com framing do gsd
- Triggers.yaml ainda não calibrados com field data — primeira execução real vai
  revelar falsos positivos/negativos
- Manual SKILLS-USAGE-MANUAL.md está em pt-BR; outros docs não foram retraduzidos
- Livros canônicos (clean-code, DDD, etc.) deveriam virar references em v0.6.1

---


### 2026-04-28 — v0.9.0 — "Maior construtor de códigos com Claude e GSD do planeta"

**Contexto que motivou:**
v0.4.1 nunca foi testada em projeto real fim a fim. Primeira execução real (Áugure MVP) revelou bugs críticos:
- Autopilot pulava auto-retro entre phases
- `--from N` ignorava artefatos faltantes em phases anteriores
- Output em inglês quando humano queria pt-BR
- Estrutura de pastas livre, sem padrão monorepo
- Permissões pediam confirmação a cada comando
- Identidade visual sendo gerada ao invés de aguardar humano

User reportou e demandou correção sistêmica para tornar framework "1000% melhor".

**O que mudou:**

1. **Autopilot v2.0 com retros bloqueantes**
   - `gsd-phase-completeness-checker` agente novo: audita artefatos esperados vs presentes
   - Hook `gsd-phase-transition-guard.sh`: bloqueia avanço de phase se anterior incompleta
   - Auto-retro do passo 4.10 agora é OBRIGATÓRIA (não opcional)
   - `--from N` agora detecta retros faltantes em phases anteriores e ALERTA

2. **`/gsd:recover-retros` — recuperação retroativa**
   - Workflow + command novos
   - Reconstrói retros perdidas a partir de PLAN.md, EXECUTION-LOG.md, VERIFICATION.md, METRICS.md, git log
   - Modo `--interactive` pergunta qualitativos durante reconstrução
   - Modo `--all` resolve todos as phases sem retro de uma vez
   - Resolve cenário Áugure (4 retros perdidas no MVP)

3. **Skill nova `meta/productivity-estimation`**
   - Calcula ganho de produtividade no fim do milestone
   - Compara `estimated_solo_dev_weeks` (campo novo em project.yaml) vs tempo real (sum de duration_hours em METRICS.md)
   - Default Áugure: 24-30 semanas × 40h = 960-1200h estimado vs 28h real = 34x mais rápido
   - `/gsd:milestone-summary` automaticamente inclui esta seção

4. **Estrutura monorepo padrão**
   - `specs/project.yaml > project.monorepo: true` é default
   - `apps[]` declara API/web/mobile (configurável)
   - `/gsd:bootstrap` cria `apps/api`, `apps/web`, `apps/mobile` automaticamente
   - Nova reference `monorepo-structure.md` documenta padrões por app
   - Skill da estrutura também referencia compartilhamento via `packages/`

5. **Permissões totais por default**
   - `.claude/settings.json` com `defaultMode: bypassPermissions`
   - Lista `allow` com 66 comandos (git, npm, python, docker, ng, ionic, powershell, etc.)
   - Nota explícita instruindo Claude a não pedir confirmação para nada dentro do projeto
   - Hook de transition-guard preserva segurança onde importa (artefatos faltantes)

6. **SAAS-BILLING-DOCS como referência canônica**
   - `docs/SAAS-BILLING-DOCS.md` integrado (1313 linhas, do projeto converzas)
   - Skill nova `domain/saas-billing-canonical` obrigatória para phases de billing
   - Triggers automáticos por feature (billing, subscription, payment, checkout) + integration safe2pay
   - Seção 18 nova no CLAUDE.md documenta a regra
   - Anti-pattern explícito: nunca inventar lógica de billing

7. **Identidade visual aguarda humano**
   - `tokens.json` resetado para placeholder `AGUARDANDO_INPUT_HUMANO`
   - `brand.md` resetado para template
   - `INDEX.md` deixa explícito que framework não inventa cores/voz
   - Gate 2 (Visual Contract) BLOQUEIA phase com `has_ui: true` se tokens ausentes
   - Documenta processo: humano fornece, framework valida

8. **4 wrapper commands faltantes**
   - `/gsd:metrics` — captura métricas + retro
   - `/gsd:sprint-plan` — quebra milestone em sprints
   - `/gsd:reconcile-state` — reconcile prometido vs entregue
   - `/gsd:verify-phase` — verifica success_criteria
   - Workflows já existiam, faltavam wrappers para slash commands

9. **Output 100% em pt-BR**
   - Banners do autopilot em pt-BR
   - Templates de retro em pt-BR
   - Workflows novos (recover-retros) em pt-BR
   - Mensagens de erro/sucesso em pt-BR

**Numericamente:**

| Componente | v0.4.1 | v0.9.0 |
|------------|--------|--------|
| Skills | 44 | 46 (+2: productivity-estimation, saas-billing-canonical) |
| Triggers.yaml | 44 | 46 |
| Agentes | 36 | 37 (+1: phase-completeness-checker) |
| Commands | 82 | 87 (+5: metrics, sprint-plan, reconcile-state, verify-phase, recover-retros) |
| Workflows | 80 | 81 (+1: recover-retros) |
| Hooks | 9 | 10 (+1: phase-transition-guard) |
| Permissões em allow list | 0 explícitas | 66 |
| Output em pt-BR | parcial | 100% (autopilot, retros, novos workflows) |

**Limitações que continuam:**
- ~~159 outros arquivos do framework ainda têm paths Windows. Não corrigidos por risco. Solução: fix cirúrgico quando arquivo específico falhar em campo.~~ **[RESOLVIDO em v0.9.5 — varredura completa: 733 paths corrigidos em 162 arquivos; zero ocorrências de `C:/` em `.claude/` desde então, verificado por teste automatizado em test_docs_consistency.sh]**
- Gate 3 valida citação, não aplicação (Regra 5 do CLAUDE.md mitiga).
- Field data ainda limitado (1 projeto: Áugure). v0.5.1 dependerá de telemetria de 3-5 projetos novos rodando v0.9.0.

**Mudanças que precisam ser validadas em campo:**
- Hook de phase-transition-guard pode ter falsos positivos (bloqueio injusto). Monitorar.
- Cálculo de productivity assume `duration_hours` em METRICS — se autopilot não popular esse campo, vai falhar.
- Bypass total + 66 permissões pode ser permissivo demais para alguns contextos. Re-avaliar baseado em uso.

---


### 2026-04-24 — v0.4.1 — Skills enforcement automático implementado

**Contexto que motivou:**
Em v0.4.0 a documentação prometia enforcement automático das 44 skills via matriz contextual (`sprint_ui_matrix` em `SKILLS_INDEX.md`). Verificação real revelou: as skills existiam fisicamente e o catálogo descrevia a matriz, mas (1) nenhuma skill tinha `triggers.yaml` ou `keywords.txt` (estrutura de detecção), (2) `gsd-plan-checker.md` não referenciava o documento `skills-enforcement.md` no `<required_reading>`, (3) plan-checker não tinha lógica explícita de "validar matriz de skills obrigatórias por contexto da fase", (4) o agente tinha 4 paths Windows hardcoded que falhavam fora do ambiente original.

Resultado prático em v0.4.0: enforcement dependia inteiramente de Claude inferir mentalmente quais skills aplicar, sem mecanismo formal. Skills "óbvias" (form-ux-mastery em fase de form) eram citadas; skills "menos óbvias" (empty-states-polish, trust-safety-ux, motion-design-patterns) eram esquecidas com frequência.

**O que mudou:**

1. **44 arquivos `triggers.yaml` criados** — um por skill, todos com regras estruturadas em YAML declarando `required_for` (clauses por flag, locale, stack, feature, context, keyword, path, integration) e `recommended_for`. Cobertura completa:
   - br/ — 3 skills (locale-driven)
   - domain/ — 6 skills (stack-driven)
   - meta/ — 4 skills (phase-type-driven)
   - mobile/ — 2 skills (flag-driven)
   - product/ — 4 skills (flag + feature-driven)
   - quality/ — 5 skills (flag + feature-driven)
   - ux-advanced/ — 14 skills (flag + feature + context-driven)
   - standalone — 6 skills (mix)

2. **`gsd-plan-checker.md` reforçado:**
   - 4 paths Windows hardcoded substituídos por relativos (`./.claude/...`)
   - `<required_reading>` agora aponta para `skills-enforcement.md` e `SKILLS_INDEX.md` (em path relativo)
   - **Dimension 6 nova: "Mandatory Skills Coverage"** com 9 sub-passos: construir vetor de contexto da fase, walk skills/, parsear triggers.yaml, matchear `required_for`, computar set de skills obrigatórias, ler `## Skills Consultadas` do PLAN.md, computar gap, reportar issues bloqueantes
   - Success criterion novo

3. **`skills-enforcement.md` atualizado** — cabeçalho documenta que infra agora está IMPLEMENTADA (era promessa, virou realidade). Mantém limitação honesta: gate 3 valida citação, não leitura. Para "skill foi de fato lida e aplicada", continua dependendo do prompt humano explícito (Regra 5 do CLAUDE.md).

**Numericamente:**

| Componente | v0.4.0 | v0.4.1 |
|------------|--------|--------|
| Skills | 44 | 44 (estável) |
| Triggers.yaml | 0 | **44** (+44) |
| Agentes | 36 | 36 (estável) |
| Commands | 82 | 82 (estável) |
| Workflows | 80 | 80 (estável) |
| Paths Windows no plan-checker | 4 | 0 |
| Gates explicitamente codificados em plan-checker | 5 | 6 (+ Mandatory Skills Coverage) |

**Limitações que continuam:**
- ~~159 outros arquivos do framework ainda têm paths `C:/Projetos/global/` hardcoded (corrigidos só no plan-checker e autopilot). Não corrigidos por risco de quebrar coisa funcional. Solução: fix cirúrgico quando arquivo específico falhar em campo.~~ **[RESOLVIDO em v0.9.5 — ver nota acima]**
- Gate 3 valida citação, não aplicação. "Skill citada mas não lida" continua resolvido apenas por prompt humano (Regra 5).
- Zero field data ainda. v0.4.1 não foi testada em projeto real.

**Quem se beneficia mais:**
- Projetos com UI complexa (UX skills agora viram blockers)
- Projetos pt-BR (br/ skills viram automáticas)
- Projetos cross-cutting (auth, payment, upload — features detectadas)

**Próximo passo natural:**
- Rodar em projeto real (Áugure) por 3-5 phases
- Coletar telemetria via `bin/export-telemetry.sh`
- Calibrar `triggers.yaml` baseado em falsos positivos / falsos negativos reais
- v0.5 viria com base em dado, não em palpite

---

### 2026-04-22 — v0.4.0 — Autossuficiência operacional completa

**Contexto que motivou:**
Após v0.3 integrar 44 skills + 1 agente + 9 hooks, ainda restava dependência de instalação externa para agentes GSD (gsd-planner, gsd-plan-checker, etc.), slash commands (`/gsd:bootstrap`, `/gsd:plan-phase`, etc.), workflows adicionais e o motor CLI `gsd-tools.cjs`. Usuário enviou `agents.tar`, `get-shit-done.tar` e `comands.tar` com todos esses artefatos. Esta versão integra tudo, fechando o ciclo.

**O que mudou (numericamente):**

| Componente | v0.3.0 | v0.4.0 |
|------------|--------|--------|
| Skills | 44 | 44 (estável) |
| Agentes | 1 | **36** (+35) |
| Commands | 0 | **81** (+81, dos quais 73 em gsd/ + 8 top-level) |
| Workflows | 8 | **76** (+68) |
| References | 6 | **46** (+40) |
| Templates | ~11 | **37** (+26) |
| Hooks | 9 | 9 (estável) |
| Bin | 2 scripts | **2 scripts + gsd-tools.cjs (1158 linhas) + 24 libs em lib/** |
| Tamanho total | ~2.5 MB | ~4.2 MB |

**Novos componentes integrados:**

- **35 agentes** em `.claude/agents/`: `gsd-planner`, `gsd-plan-checker`, `gsd-ui-checker`, `gsd-executor`, `gsd-integration-checker`, `gsd-verifier`, `gsd-roadmapper`, `gsd-phase-researcher`, `gsd-ui-researcher`, `gsd-domain-researcher`, `gsd-ai-researcher`, `gsd-advisor-researcher`, `gsd-framework-selector`, `gsd-research-synthesizer`, `gsd-codebase-mapper`, `gsd-pattern-mapper`, `gsd-code-reviewer`, `gsd-code-fixer`, `gsd-debugger`, `gsd-debug-session-manager`, `gsd-doc-writer`, `gsd-doc-verifier`, `gsd-security-auditor`, `gsd-ui-auditor`, `gsd-assumptions-analyzer`, `gsd-nyquist-auditor`, `gsd-eval-planner`, `gsd-eval-auditor`, `gsd-intel-updater`, `gsd-user-profiler`, `gsd-project-researcher` e genéricos `researcher`, `security-auditor`, `test-writer`, `api-builder`. Plus `gsd-orchestrator` em `meta-orchestration/` (já integrado em v0.3).

- **81 slash commands** em `.claude/commands/`:
  - 8 top-level: `component`, `deploy`, `endpoint`, `migrate`, `optimize`, `review`, `security`, `test`
  - 73 em `gsd/`: incluindo `plan-phase`, `execute-phase`, `ui-phase`, `new-project`, `new-milestone`, `autonomous`, `ship`, `next`, `quick`, `manager`, `validate-phase`, `audit-milestone`, `audit-fix`, `scan`, `secure-phase`, `forensics`, `health`, `import`, `insert-phase`, `cleanup`, `resume-work`, `session-report`, `stats`, `progress`, `thread`, etc.

- **68 workflows novos** em `.claude/get-shit-done/workflows/`: 71 arquivos upload - 3 conflitos com meus workflows (`execute-phase`, `plan-phase`, `ui-phase`) = 68 novos. Os 3 conflitos tiveram a versão upload arquivada em `workflows/_archive-gsd-base/` para referência; as versões do framework foram preservadas porque têm enforcement novo (Visual Contract, skills matrix v0.3, sprint DoD).

- **40 references novos** em `.claude/get-shit-done/references/`: `agent-contracts.md`, `ai-evals.md`, `ai-frameworks.md`, `artifact-types.md`, `checkpoints.md`, `common-bug-patterns.md`, `context-budget.md`, `continuation-format.md`, `decimal-phase-calculation.md`, `domain-probes.md`, `executor-examples.md`, `gate-prompts.md`, `gates.md`, `git-integration.md`, `git-planning-commit.md`, `ios-scaffold.md`, `model-profile-resolution.md`, `model-profiles.md`, `phase-argument-parsing.md`, `planner-antipatterns.md`, `planner-gap-closure.md`, `planner-reviews.md`, `planner-revision.md`, `planner-source-audit.md`, `planning-config.md`, `questioning.md`, `revision-loop.md`, `tdd.md`, `thinking-models-debug.md`, `thinking-models-execution.md`, `thinking-models-planning.md`, `thinking-models-research.md`, `thinking-models-verification.md`, `thinking-partner.md`, `ui-brand.md`, `universal-anti-patterns.md`, `user-profiling.md`, `verification-overrides.md`, `verification-patterns.md`, `workstream-flag.md` + pasta `few-shot-examples/`.

- **26 templates novos**: `AI-SPEC.md`, `DEBUG.md`, `SECURITY.md`, `UAT.md`, `UI-SPEC.md`, `VALIDATION.md`, `claude-md.md`, `config.json`, `context.md`, `continue-here.md`, `copilot-instructions.md`, `debug-subagent-prompt.md`, `dev-preferences.md`, `discovery.md`, `discussion-log.md`, `milestone-archive.md`, `phase-prompt.md`, `planner-subagent-prompt.md`, `project.md`, `requirements.md`, `research.md`, `retrospective.md`, `roadmap.md`, `state.md`, `summary-*.md`, `user-profile.md`, `user-setup.md`, `verification-report.md` + pastas `codebase/`, `research-project/`.

- **`bin/gsd-tools.cjs`** (1158 linhas) + **24 libs** em `bin/lib/`: `audit.cjs`, `commands.cjs`, `config.cjs`, `core.cjs`, `docs.cjs`, `frontmatter.cjs`, `graphify.cjs`, `gsd2-import.cjs`, `init.cjs`, `intel.cjs`, `learnings.cjs`, `milestone.cjs`, `model-profiles.cjs`, `phase.cjs`, `profile-output.cjs`, `profile-pipeline.cjs`, `roadmap.cjs`, `schema-detect.cjs`, `security.cjs`, `state.cjs`, `template.cjs`, `uat.cjs`, `verify.cjs`, `workstream.cjs`. Operações atômicas: carregar config, resolver model por agente, find-phase, commit planning docs, verify-summary, generate-slug, current-timestamp, list-todos, history-digest, state-snapshot, phase-plan-index, websearch.

- **3 contexts** em `contexts/`: `dev.md`, `research.md`, `review.md`.

**Duplicatas de skills — análise e decisão:**

Inicialmente planejei consolidar 14 pares de duplicatas (merge com preservação do melhor). Ao fazer scan real (`[ -d framework/ ] && [ -d upload/ ]`), **zero duplicatas reais detectadas** — a integração v0.3 tinha preservado as versões do framework e pulado as do upload que já existiam. As relações que eu pensei serem duplicatas são na verdade **sobreposições conceituais** (ex: `product/micro-animations-delight` e `ux-advanced/motion-design-patterns` cobrem motion com ângulos complementares — uma foca em taxonomia/propósito, outra em tokens de duration/easing). **Decisão:** manter ambas, documentar relação no SKILLS_INDEX como "complementares, invocar ambas apenas em sprints com motion não-trivial".

**Resposta definitiva à pergunta do usuário "gsd e agentes funcionarão em sincronia ou será um ou outro":**

**Funcionam em sincronia, agora completamente:**
- **Slash commands** (`/gsd:bootstrap`, `/gsd:plan-phase`, etc.) ativam workflows
- **Workflows** invocam agentes via Task tool
- **Agentes** executam tarefas consultando skills relevantes
- **Skills** são lidas para guiar decisões técnicas
- **Hooks** monitoram tudo (contexto, commits, boundaries)
- **`gsd-tools.cjs`** cuida de operações atômicas (config, state, commits planning)

Nada mais é referenciado sem existir no próprio framework. **Framework é autônomo.**

**Decisões tomadas:**

- **[DECISION-24] Sem merge manual de skills.** Risco de perder conteúdo ao fundir skills de autores diferentes supera benefício de ter menos arquivos. Relações complementares são documentadas no SKILLS_INDEX, não consolidadas fisicamente.

- **[DECISION-25] Workflows meus (plan-phase/execute-phase/ui-phase) preservados.** Upload tinha versões também mas meus adicionam enforcement de Visual Contract, skills matrix v0.3, sprint-checker. Upload versions arquivadas em `workflows/_archive-gsd-base/` para referência e para quem queira migrar.

- **[DECISION-26] `gsd-tools.cjs` integrado como motor.** Sem ele, vários workflows e agentes não funcionam (dependem de operações atômicas sobre STATE.md, ROADMAP.md, config.json). Obrigatório ter Node 18+ para o framework funcionar completo.

- **[DECISION-27] Commands top-level (`component`, `deploy`, etc.) integrados mesmo sem saber se serão usados.** São 8 arquivos pequenos, não pesam, e remover criaria risco de referência quebrada em algum workflow.

**O que esta versão NÃO resolve (honesto, v0.5+):**

- **Compatibilidade entre workflows do upload e meu enforcement.** Os 68 workflows novos do upload (`autonomous`, `new-project`, `ship`, etc.) não conhecem `sprint_ui_matrix`, `visual_tokens_mode`, `slicing_strategy` que adicionei em v0.2/0.3. Usar esses workflows bypassa meu enforcement. Não é quebra, é perda silenciosa.

- **Testes das adições massivas.** 5/5 suites verde só valida existência dos arquivos + estrutura. Validar semântica de 68 workflows + 36 agentes exigiria dias de leitura.

- **Ainda sem field data.** Apesar de agora ter TUDO instalado em um zip, nenhum sprint real ainda foi executado com essa configuração. Continua "framework teoricamente completo, praticamente não testado".

- **Risco de bloat.** 4.2 MB, 350+ arquivos, múltiplos caminhos para fazer a mesma coisa (`/gsd:execute-phase` via command vs. workflow direto vs. invocação manual do agente `gsd-executor`). Entender o que usar quando exige leitura extensa dos references. Primeiros projetos vão sofrer com "qual slash command uso para X?".

### 2026-04-22 — v0.3.0 — Integração do GSD base (framework auto-suficiente)

**Contexto que motivou:**
Usuário perguntou se precisaria instalar o GSD separado em cada projeto ou se já estaria no framework. A resposta honesta até v0.2.2 era "precisa instalar separado" — o framework carregava 20% do GSD base (797 KB vs 4 MB). O usuário enviou `.tar/.rar` com os artefatos do GSD (44 skills, 1 agente, 9 hooks). Decisão: integrar ao framework para torná-lo auto-suficiente.

**O que mudou (numericamente):**

| Componente | v0.2.2 | v0.3.0 |
|------------|--------|--------|
| Skills | 14 | **44** (+30) |
| Agentes | 0 | **1** (gsd-orchestrator) |
| Hooks operacionais | 0 | **9** |
| Categorias de skills | 4 (br, mobile, product, quality) | **9** (+ domain, meta, ux-advanced, standalone) |
| Tamanho total | ~271 KB | ~2.5 MB |
| Arquivos | 175 | ~260 |

**Skills novas por categoria:**

- **`ux-advanced/` (14)** — chat-ux-patterns, dark-mode-theming, design-tokens-system, empty-states-polish, file-upload-ux, form-ux-mastery, gesture-touch-patterns, motion-design-patterns, onboarding-patterns, payment-checkout-ux, responsive-breakpoint-strategy, saas-dashboard-patterns, trust-safety-ux, ui-input-rich-patterns. Cobre UX que `quality/` e `product/` não cobriam (especialmente: design tokens aprofundado, form UX, onboarding, payment, trust/safety, dashboard).
- **`domain/` (6)** — angular-material-patterns, docker-production-ready, ionic-patterns, llm-integration-patterns (869 linhas), mysql-schema-design, safe2pay-escrow-br (546 linhas, único mantido com nome específico).
- **`meta/` (4)** — design-to-code (renomeado de design-to-code-gbc), orchestration-decision-tree, project-kickoff-interview, stack-advisor.
- **Standalone (6)** — owasp-security, prompt-engineering, spartan-ai-toolkit, systematic-debugging, `ui-ux-pro-max` (SKILL.md de 377 linhas + **437 KB de data CSVs** com 99 UX guidelines, 67 styles, 96 paletas, 57 font pairings, 25 chart types, 13 stacks + **147 KB de scripts Python** para search), webapp-testing.

**Agente integrado:**

- `gsd-orchestrator` em `.claude/agents/meta-orchestration/` — agente mestre que roteia intent do usuário para o workflow/skills corretos. 12 KB de prompt. Antes era "assumido instalado separado", agora vem no framework.

**Hooks operacionais:**

9 hooks Node.js + Bash em `.claude/hooks/`:
- `gsd-statusline.js` — statusline custom mostrando fase, sprint, uso de contexto
- `gsd-context-monitor.js` — injeta warnings no agente quando contexto fica baixo (35% warning / 25% critical)
- `gsd-prompt-guard.js` — filtra prompts contra padrões destrutivos
- `gsd-read-guard.js` — previne leitura de arquivos fora do escopo
- `gsd-workflow-guard.js` — garante ordem dos workflows (bootstrap antes de plan, etc.)
- `gsd-check-update.js` — checagem periódica de updates
- `gsd-phase-boundary.sh` — bloqueia edição cruzada de fase
- `gsd-session-state.sh` — persiste estado da sessão
- `gsd-validate-commit.sh` — valida conventional commits

Documentação completa em `.claude/hooks/README.md` com instruções de instalação via `settings.json`.

**Sanitização de contaminação:**

As skills integradas vinham de um projeto real (GBC / Visol / Safe2Pay). Sanitização em massa via sed:
- `gbc/GBC` → `{PROJETO}` ou `app` (em CSS vars e unix users)
- `--gbc-token` → `--app-token`
- `Safe2Pay` → `{gateway-pagamento}` (exceto na skill `domain/safe2pay-escrow-br` que é específica por design)
- `Visol/Áugure/GetBestCat` → `{PROJETO}`
- Pasta `meta/design-to-code-gbc/` → `meta/design-to-code/`

Resultado: **zero contaminação remanescente** em 43 skills; 1 skill mantida intencionalmente específica (`safe2pay-escrow-br`, igual ao que seria uma skill `stripe-integration`).

**Matriz `sprint_ui_matrix` endurecida:**

Aproveitando skills novas, a matriz de obrigatórias em `SPRINT.md` com `has_ui: true` ficou mais rigorosa:

- **Sempre obrigatórias (5)**: component-library-governance, accessibility-pro, design-tokens-system, ui-ux-pro-max (evita AI slop), empty-states-polish
- **Obrigatórias por flag**: form-ux-mastery (se has_forms), motion-design-patterns (se has_non_trivial_motion)
- **Obrigatórias por feature**: onboarding-patterns + trust-safety-ux (auth/signup), payment-checkout-ux + trust-safety-ux (checkout), file-upload-ux (upload), chat-ux-patterns (chat), saas-dashboard-patterns (dashboard)
- **Obrigatórias por contexto**: gesture-touch-patterns (mobile), responsive-breakpoint-strategy (web), dark-mode-theming (se suporta dark)

Antes: 6 skills obrigatórias possíveis. Agora: até 15.

**Decisões tomadas:**

- **[DECISION-20] Framework vira auto-suficiente.** A decisão original (DECISION-04 na v0.1) de não redistribuir o GSD base foi revertida porque criava confusão operacional ("o que é framework? o que é GSD? onde instala cada um?"). v0.3 corrige integrando o essencial. Workflows/commands `gsd-*` ainda são herdados por instalação Claude Code (esses sim variam muito), mas skills/agentes/hooks que são estáveis vêm junto.

- **[DECISION-21] Duplicatas: preservar versão do framework atual.** Das 14 skills que existiam em ambos (framework + upload), em 13 casos a versão do framework era mais extensa ou mais recente. Mantidas. Apenas `accessibility-pro` do upload era mais extensa (411 vs 335 linhas) com referência à LBI (Lei Brasileira de Inclusão) que não existia na minha — pendente de merge seletivo em v0.3.1.

- **[DECISION-22] Sanitização em massa via sed + conferência manual de 4 casos.** Tentar preservar referências originais "por honestidade histórica" criaria ruído permanente. Sed substituiu 99% limpo; os 4 casos remanescentes (CSS user gbc em Dockerfile, logo.svg, nome de pasta, referência em índice) foram resolvidos manualmente. Scan final: zero contaminação fora da skill safe2pay-escrow-br (intencional).

- **[DECISION-23] `ui-ux-pro-max` como obrigatória universal (se `has_ui: true`).** A skill traz direção estética (evita AI slop) com data real — 99 guidelines, 67 styles, paletas, font pairings. Exatamente o que faltava no framework segundo a análise do próprio usuário. Adicionada como 5ª obrigatória sempre.

**O que esta versão NÃO resolve (honesto):**

- **Workflows e commands do GSD (gsd-planner, gsd-plan-checker, etc.)** ainda são herdados de instalação separada. Não estão no zip. Integrá-los seria dobrar o tamanho do framework e eles variam mais entre instalações.
- **Merge seletivo de conteúdo útil do upload** em 13 skills duplicadas — ex: pegar referência LBI de `accessibility-pro` do upload e incluir na versão do framework. Pendente para v0.3.1.
- **Testes das 30 skills novas**. Smoke tests só validam que os arquivos existem e têm conteúdo > 1KB. Validar que o conteúdo é coerente e sem regressões exigiria leitura humana de cada um.
- **Ainda sem field data.** Mesmo com 44 skills, sem uso real os números não significam "framework funciona" — apenas "framework tem muito conteúdo".

### 2026-04-22 — v0.2.2 — Orchestrator integration + docs multi-formato

**Contexto que motivou:**
Usuário questionou duas coisas após receber v0.2.1:
1. "Os agentes do orchestrator não podem ser usados junto com GSD?"
2. "Posso colocar HTML/PDF/JSX/XLSX/DOCX em `docs/` e em `identidade-visual/` para serem lidos?"

Ambas revelaram **gaps de design**: o framework assumia agentes ou como substitutos (erro) e só aceitava `.md`/`.yaml` na documentação (limitação não justificada).

**O que mudou:**

1. **Orchestrator + GSD como camadas complementares**
   - `references/agent-orchestration.md` — define explicitamente: GSD = processo/gates, agentes = execução paralela especializada
   - Matriz de agentes típicos (`backend-architect`, `frontend-developer`, `ui-ux-designer`, `mobile-developer`, `test-writer`, `security-reviewer`, `performance-analyst`) com skills carregadas automaticamente
   - Padrões de invocação: básico (1 agente), paralelo (múltiplos), delegação (workflow dentro de agente)
   - `config.json > orchestrator` — `enabled`, `available_agents`, `fallback_mode: inline|block`, `parallelization_when_possible`, `max_context_per_agent_tokens`
   - `config.json > agent_skills` expandido — 8 novos mapeamentos agent → skills carregadas
   - Gates **não são dispensáveis por uso de agente** — gate 3 valida skills no PLAN consolidado, gate 5 roda sobre código final, gate 6 reconcile compara afirmações vs código. Agente é braço, não cérebro do processo.

2. **Docs multi-formato**
   - `references/docs-organization.md` — estrutura canônica de `docs/` + convenções, formatos suportados, regras
   - Formatos lidos nativamente pelo Claude: `.md`, `.txt`, `.pdf`, `.html`, `.jsx`, `.tsx`, `.svg`, `.png`, `.jpg`, `.json`, `.yaml`, `.csv`
   - Formatos com conversão automática: `.xlsx`, `.docx`, `.pptx` — script gera espelho `.md` ao lado
   - `bin/convert-docs.sh` — escaneia `docs/`, gera espelhos `.md` de binários usando pandoc (docx/pptx) + openpyxl (xlsx). Só regenera quando fonte é mais nova ou com `--force`. Testado e funcional.
   - Estrutura recomendada: `docs/business/`, `docs/research/`, `docs/identidade-visual/wireframes/`, `docs/identidade-visual/mockups/`, `docs/identidade-visual/references/`, `docs/identidade-visual/assets/` — todas opcionais, todas com INDEX.md obrigatório se presentes.
   - `config.json > docs` — `require_index_md`, `auto_convert_binaries`, `supported_binary_formats`

3. **INDEX.md em cada pasta de docs/**
   - Obrigatório em `docs/` e em toda subpasta não-vazia
   - Cada arquivo listado com **relevância** (canônico / alta / referência / histórico) — permite Claude decidir quando ler, em vez de ler tudo toda vez
   - Templates gerados automaticamente: `templates/INDEX-subpasta.md`
   - Instanciados: `docs/INDEX.md`, `docs/identidade-visual/INDEX.md`, `docs/identidade-visual/wireframes/INDEX.md`, `docs/identidade-visual/mockups/INDEX.md`

4. **Novo workflow `/gsd:docs-index`**
   - Escaneia `docs/` detectando: arquivos novos sem descrição, INDEX ausente, referência quebrada (INDEX cita arquivo inexistente), binário sem espelho `.md`
   - Interativamente resolve cada pendência com o humano
   - Auto-invocado pelo `bootstrap` no passo 3.7

5. **Bootstrap estendido**
   - Passo 3.6 — detecta agentes orchestrator disponíveis e registra em `config.json`. Padrão: fallback_mode inline para começo seguro
   - Passo 3.7 — escaneia `docs/`, lista presença de canônicos + status dos INDEX.md, oferece invocar `/gsd:docs-index`

6. **Suporte explícito a wireframes HTML/JSX em `identidade-visual/wireframes/`**
   - Claude lê `.html` e `.jsx` como texto → vê a estrutura completa (hierarquia, copy, comportamento) — muito mais rico que screenshot
   - Workflow típico documentado: gera wireframe com IA externa (v0/Lovable/Bolt) → salva em `wireframes/` → referencia no `SPRINT.md > Visual Contract` → Claude implementa olhando o wireframe + tokens de `tokens.json`

**Decisões tomadas:**

- **[DECISION-15] Orchestrator = braços, GSD = cérebro do processo.** Agentes fazem trabalho paralelo rápido, mas não substituem gates. Mesmo com 10 agentes dizendo "tudo ok", gate 3 (skills), gate 5 (integration) e gate 6 (reconcile) rodam independente. Por quê: agentes alucinam, pulam regras, não leem skill completa. Gates são a rede.

- **[DECISION-16] Default de agentes é `fallback_mode: inline`.** Projeto novo começa com Claude principal fazendo tudo, para entender o fluxo GSD. Migração para agentes reais vem com confiança. Não forçar adoção de agentes desde dia 1 — alguns ambientes não têm, e a fricção de "instalar 8 agentes antes do primeiro commit" mata o framework.

- **[DECISION-17] Binários viram espelhos .md em vez de serem lidos diretamente.** `.xlsx` tem estrutura semântica perdida em extração crua; `.docx` idem. Gerar espelho explícito (onde o humano pode **auditar** o que o Claude vai ler) é mais honesto que decodificar silenciosamente em runtime. E preserva o original como evidência.

- **[DECISION-18] INDEX.md em cada pasta é custo justificado.** Sem INDEX, Claude lê 50 arquivos aleatórios ou ignora tudo. Com INDEX explicando relevância, Claude lê o que importa primeiro e consulta o resto sob demanda. Custa 5-10 minutos por pasta para criar; economiza horas de contexto desperdiçado depois.

- **[DECISION-19] Wireframes como HTML/JSX em `identidade-visual/wireframes/`.** Gerações de IA (v0, Lovable, Bolt) produzem código real. Jogar direto no framework é superior a converter para screenshot antes — Claude vê a estrutura. Ressalva: cores dos wireframes podem divergir de `tokens.json`; canônico vence sempre, wireframe é referência de layout/hierarquia.

**O que esta versão NÃO resolve (honesto):**

- **Auto-sync de wireframes ↔ código.** Mudou o wireframe depois de implementar — ninguém detecta automaticamente.
- **Detecção automática de agentes instalados.** Config depende do humano listar manualmente em `orchestrator.available_agents`. Detecção real exigiria protocolo compartilhado.
- **Resumo automático de PDFs grandes.** `/gsd:docs-index` oferece gerar, mas não implementado na v0.2.2 — fica para v0.3.

### 2026-04-22 — v0.2.1 — Sprints testáveis + fidelidade visual enforçada

**Contexto que motivou:**
O usuário do framework pediu, explicitamente, duas coisas ao implementar sprints curtos:
1. Sprints testáveis entre milestones (antes, só fase direta dentro de milestone)
2. Fidelidade à identidade visual passada em `docs/identidade-visual/` + aplicação das skills de UX nas telas

Proposta inicial do usuário: admin → negócio → regras. Proposta contra-argumentada: **vertical value slicing** como default para produtos com usuário externo, **admin-first** como exceção para backoffice/ERP. Decisão: oferecer **as duas ordens**, bootstrap pergunta, projeto registra escolha em `config.json`.

**O que mudou:**

1. **Estratégia de slicing configurável + documentada**
   - `references/sprint-slicing.md` — documento canônico com as duas ordens, critério de decisão ("quem é a pessoa cuja vida fica melhor no Sprint 1?"), exemplos concretos (marketplace vs ERP), invariantes universais, anti-patterns
   - `.planning/config.json > slicing_strategy` — `"vertical_value" | "admin_first"` gravado durante bootstrap
   - `.planning/config.json > sprint_planning` — min/max de dias/tasks/DoD items como parâmetros configuráveis

2. **Enforcement real de fidelidade visual**
   - `references/visual-fidelity.md` — regras de como `SPRINT.md` deve citar tokens de `docs/identidade-visual/tokens.json`, estrutura mínima esperada do tokens.json, validações automáticas do checker
   - Seção `## Visual Contract` obrigatória em todo SPRINT.md com `has_ui: true`
   - Plan-checker valida que cada token citado existe em tokens.json real (via lookup Python robusto — rejeita path incompleto, rejeita nós intermediários)
   - Se tokens.json estiver vazio/faltando categorias mínimas (`color` + `space`), sprints com UI são bloqueados
   - `visual_tokens_mode: final | provisional` em config.json — opção de começar com tokens provisórios em projetos sem design pronto, com revisão forçada antes do Sprint 3

3. **Template `SPRINT.md` completo**
   - Front-matter YAML com flags estruturadas (`has_ui`, `has_forms`, `has_error_states`, `has_non_trivial_motion`, `touches_shared_components`, `locale`)
   - Seções obrigatórias: Narrativa (1 parágrafo em linguagem de usuário), Definition of Done (3-6 verificações binárias testáveis em 30 min), Visual Contract (se UI), UX Skills Applied (output concreto por skill, não lista abstrata), Tasks, Skills Consultadas/Dispensadas com justificativa, Dependências, Riscos, Pós-sprint
   - Exemplo preenchido inline para um sprint de "criar anúncio" serve como referência

4. **Matriz de skills UX obrigatórias por flag de sprint**
   - Adicionado `sprint_ui_matrix` em `references/skills-enforcement.md`
   - `has_ui: true` → `product/component-library-governance` + `quality/accessibility-pro`
   - `has_ui: true` + `locale: pt-BR` → `br/ux-copywriting-ptbr`
   - `has_forms: true` ou `has_error_states: true` → `quality/error-ux-patterns`
   - `has_non_trivial_motion: true` → `product/micro-animations-delight`
   - `touches_shared_components: true` → `product/visual-regression-testing`

5. **Workflow `/gsd:sprint-plan`**
   - Novo workflow em `workflows/gsd:sprint-plan.md`
   - Input: milestone_id + strategy opcional de override
   - Output: N arquivos `SPRINT-NN.md` validados pelo checker + atualização de `.planning/SPRINTS.md`
   - Valida pré-condições (config.json, milestone existe, tokens.json preenchido, sprint anterior fechado)
   - Aplica estratégia diferente conforme `slicing_strategy` e alerta se escolha diverge do tipo de projeto detectado

6. **Bootstrap atualizado**
   - Novo passo 3.5 em `workflows/bootstrap.md` pergunta strategy ao humano, com sugestão automática baseada em `project-brief.md` (usuário-alvo consumidor → vertical_value; operador interno → admin_first)
   - Validação de tokens.json com opção de continuar provisional ou preencher antes

7. **Plan-phase sprint-aware**
   - `workflows/plan-phase.md` detecta se input é `sprint_id` (arquivo em `.planning/sprints/`) ou `phase_id` (bloco em `ROADMAP.md`)
   - Modo sprint: Gate 2 re-valida Visual Contract + tokens em vez de gerar UI-SPEC separado
   - Modo phase (legado): mantém lógica original
   - Mensagem acionável se input inválido aponta para rodar `/gsd:sprint-plan` primeiro

8. **`.planning/SPRINTS.md` — tabela append-only de sprints**
   - Visão geral com status (planejado, em andamento, fechado, bloqueado, deprecated)
   - Linhas inseridas por `/gsd:sprint-plan`, fechadas por `/gsd:metrics`
   - Métricas agregadas preenchidas por `/gsd:metrics-dashboard` (v0.4)

9. **Test harness expandido**
   - Novo `test_sprint_checker.sh` com 3 fixtures (good-sprint, bad-sprint-no-visual-contract, bad-sprint-unknown-token)
   - Good-sprint inclui tokens.json real que faz match com os tokens citados no SPRINT.md
   - Bad-sprint-unknown-token valida que tokens inventados (`color.unicorn.rainbow`, `space.galactic`) são detectados
   - Test_structure atualizado para verificar novos arquivos de v0.2.1 + schema mínimo de config.json
   - **Suite atual: 5/5 passando** (era 4/4 na v0.2.0)

**Decisões tomadas:**

- **[DECISION-11] Vertical value slicing como default, admin-first como exceção documentada.** A tentação de começar por admin ("fundamental, todo mundo precisa") é real mas mata testabilidade — CRUD de admin não é demonstrável a usuário externo. Vertical slicing força testabilidade desde Sprint 1. Exceção: quando admin É o produto (ERP/backoffice), aí sim admin-first é vertical.

- **[DECISION-12] Fidelidade visual vira contrato verificável, não aspiracional.** Três camadas: plan-checker valida que tokens citados existem (bloqueia antes de começar), ESLint `no-hardcoded-colors` bloqueia em build, Chromatic/visual regression pega o pixel final. As três em conjunto transformam "identidade visual" de PDF pendurado em regra mecânica.

- **[DECISION-13] Skills UX obrigatórias por flag do SPRINT.md, não por "achismo do planner".** Antes, era possível o planner ignorar skills relevantes porque "sprint simples não precisa". Agora, `has_ui: true` puxa 2 skills base; flags adicionais puxam outras 4. A ausência não é negociável — só com justificativa explícita em Skills Dispensadas.

- **[DECISION-14] Sprint testável em 30 min é cláusula pétrea do template.** Se DoD não pode ser verificada por humano em sessão única, sprint é grande demais ou abstrato demais — parte em dois, concretiza, ou reenquadra. Não é metáfora, é métrica: 3-6 itens binários, cada um em linguagem de usuário final.

**O que esta versão NÃO resolve (honesto):**

- **Plan-phase totalmente refatorado.** v0.2.1 adapta as partes críticas (detecção de modo, Gate 2 Visual Contract), mas gsd-planner e gsd-plan-checker ainda pensam em termos de "fase" internamente. Limpeza completa é v0.3.
- **Workflow `/gsd:metrics-dashboard`** — criar visualização que lê `.planning/METRICS.md` + `.planning/SPRINTS.md` e mostra tendências ("taxa de fix caiu"/"skill X sempre dispensada"). Ainda v0.4.
- **Validação de field data real.** Até rodar em 3-5 sprints reais e coletar telemetria, qualquer alegação sobre "sprints ajudam" é especulação. Exatamente como dito em v0.2.0.

### 2026-04-22 — v0.2.0 — Skills completas, enforcement real, captura de dados

**O que mudou em relação à v0.1.0:**

Três frentes executadas, respondendo à crítica auto-aplicada de que a v0.1 estava "6.5/10 — design bom mal implementado".

1. **9 skills esqueleto → production-ready** (14/14 agora ⭐, 0 restante 📝)
   - `product/api-design-contracts` — response shape, error codes enum, HTTP semantics, paginação offset/cursor, versioning, idempotency, rate limiting, OpenAPI discipline, webhooks, testing contracts
   - `mobile/offline-first` — detecção Capacitor Network + ping, queue persistente idempotente, retry exponencial com dead letter, cache stale-while-revalidate, banner persistente (não toast), otimismo UI, RequiresOnline guards, conflict resolution
   - `quality/i18n-ready-architecture` — ngx-translate/Transloco vs @angular/localize, estrutura pt-BR.json, ICU pluralização, DatePipe/CurrencyPipe locale-aware, backend babel + Accept-Language, locale routing, RTL, timezone vs locale
   - `product/visual-regression-testing` — Storybook + Chromatic/Percy/Playwright, 5 estados mínimos por componente, fixtures reutilizáveis, CI integration, cobertura 80% shared
   - `product/component-library-governance` — regra dos 3 para shared/, nomenclatura prefix, API mínima opinativa, tokens sem hex, semver estrito, deprecation path, ESLint rule no-hardcoded-colors
   - `product/micro-animations-delight` — taxonomia (micro-feedback/state-change/transition/celebration/ambient), easing tokens, duration tokens, prefers-reduced-motion obrigatório, apenas transform+opacity, FLIP/View Transitions, haptic feedback
   - `mobile/push-notifications-architecture` — APNs/FCM stack, token lifecycle idempotente, pré-prompt UI antes do nativo, categorias (transactional/actionable/informational/marketing), Notification Channels Android, deep linking, silent push, localização, timing timezone-aware
   - `br/ux-copywriting-ptbr` — tom direto não-corporativo, "você" sempre, tabela inglês→pt, verbo+substantivo em CTAs, vocabulário canônico, padrões por contexto
   - `br/lgpd-compliance` — bases legais, consent granular, endpoints obrigatórios de direitos do titular, exclusão vs anonimização, retenção, logs sem PII, criptografia, Argon2id/bcrypt, DPA, incidentes, DPO

2. **Artefatos de enforcement REAIS em `tooling/`** (antes eram só referências em docs)
   - `tooling/ci/quality.yml.template` — GitHub Actions com lint, test, bundlesize, a11y, lighthouse, i18n, security, chromatic (comentado)
   - `tooling/ci/bundlesize.config.json` — main.js 400KB, vendor.js 800KB, styles 100KB (gzip)
   - `tooling/ci/lighthouserc.json` — LCP<2500, INP<200, CLS<0.1, perf score 0.9, a11y 0.95
   - `tooling/ci/pa11yci.json` — WCAG 2AA em múltiplos viewports
   - `tooling/pre-commit/.pre-commit-config.yaml` — ruff, mypy, eslint, prettier, gitleaks, conventional-commits
   - `tooling/jest/jest.setup.a11y.js` — jest-axe com regras WCAG 2.1 AA
   - `tooling/eslint/no-hardcoded-colors.js` — custom rule que força tokens do design system
   - `tooling/README.md` — instruções de instalação em projeto existente

3. **Test harness do próprio framework em `tests/framework/`**
   - `run-all.sh` roda 4 suites e produz sumário colorido
   - `test_structure.sh` — valida estrutura essencial + skills não-vazias + artefatos de tooling
   - `test_plan_checker.sh` — valida que plan-checker bloqueia plano sem `## Skills Consultadas` + detecta skills obrigatórias ausentes (3 fixtures)
   - `test_reconcile.sh` — valida que reconcile detecta divergência entre PLAN.md `- [x]` e código real (2 cenários)
   - `test_gate_bypasses.sh` — valida que `--skip-gate-N` sem `--reason` é rejeitado (5 casos)
   - **Suite atualmente: 4/4 passando** (estado reproduzível via `cd tests/framework && bash run-all.sh`)

4. **Captura de dados de uso real** (novo, endereça TODO v0.3 adiantado)
   - `.planning/METRICS.md` — log append-only com schema explícito, uma entrada por fase fechada
   - `.planning/RETROSPECTIVE.md.template` — força humano a preencher 3 campos qualitativos (what_worked/hurt/missing) + 2 scores 1-5
   - `bin/collect-metrics.sh` — coleta automática do extraível (plan_revisions via git log, tasks_total via grep, etc.) e deixa `<FILL>` nos qualitativos
   - `bin/export-telemetry.sh` — exporta JSON anonimizado (hash do phase_id, remoção heurística de paths/URLs/emails em qualitativos) para compartilhar com autor do framework
   - `TELEMETRY-SCHEMA.json` — schema v1 canônico do formato de export
   - `.claude/get-shit-done/workflows/gsd:metrics.md` — workflow conversacional que orquestra close-of-phase (retro → collect → commit → decisão de export)

**Decisões tomadas nesta versão:**

- **[DECISION-07] Captura de dados é fricção deliberada, não automação silenciosa.** O workflow `/gsd:metrics` pausa em 2 pontos humanos (preenchimento da retro + campos qualitativos). Tentar fazer automático geraria telemetria vazia de significado. Dados que valem algo exigem reflexão de 15 min ao fim de cada fase.

- **[DECISION-08] Anonimização é lossy e manual.** `bin/export-telemetry.sh` faz passada heurística leve (paths, URLs, emails), mas usuário deve revisar antes de compartilhar. Não há promessa de que será perfeita — a promessa é que o formato é legível e o escopo do que vai junto é pequeno.

- **[DECISION-09] Test harness é smoke, não coverage completo.** 4 suites, ~15 assertions totais. Suficiente para detectar quebra grande do framework (skill desapareceu, regex do plan-checker regrediu), insuficiente para detectar bugs sutis. Coverage real pendente de v0.3+.

- **[DECISION-10] Artefatos de CI são opinativos com defaults sensatos.** Os números em `bundlesize.config.json` e `lighthouserc.json` são pontos de partida razoáveis para 80% dos projetos, não absolutos. Documentação em `tooling/README.md` orienta ajuste progressivo.

**O que esta versão NÃO resolve (honesto):**

- **Dogfooding** — o framework não gerencia a si mesmo com seus próprios gates. Aplicar GSD no GSD exige PLAN.md + STATE.md + ciclo de fases para o próprio framework. Pendente.
- **Integration-checker via AST** — v0.1 usa grep, v0.2 idem. Substituir por tree-sitter para TS/Python reduziria falsos positivos mas é esforço de dias.
- **Validação em campo** — nenhum dado real ainda. O mecanismo de captura existe (item 4 acima), mas até rodar em 3-5 fases reais, qualquer alegação de "framework funciona" é especulação.
- **Honestidade sobre a nota:** v0.1 era 6.5/10 autodeclarado. v0.2 está em algo entre 8 e 8.5. Para chegar a 9 faltam os 3 itens acima.

### 2026-04-22 — v0.1.0 — Release inicial utilizável

**Contexto que motivou:**
Três relatórios de diagnóstico do framework GSD anterior aplicado a um projeto real (GBC):
1. **Retrospectiva** — taxa de fix 28%, bugs de integração só no audit, service declarado "4/26 features" por semanas enquanto código tinha 26/26, localStorage JWT conhecido e ignorado, skills instaladas mas nunca consultadas.
2. **Relatório de 7 mudanças** — Gate UI-SPEC obrigatório, skills como checklist verificável, integration-checker obrigatório, security-probes no researcher, reconciliação artefato↔código, design-to-code, pipeline mobile.
3. **Relatório de nível internacional** — 10 skills propostas (performance, error-ux, observability, a11y em CI, i18n, api-design, visual-regression, offline-first, micro-animations, component-lib, push), 6 referências externas a adaptar, 4 mudanças de workflow, expansão de CI.

**Decisões arquiteturais tomadas:**

- **[DECISION-01] Separação estrita framework ↔ projeto**
  - `CLAUDE.md` + `.claude/` = framework idêntico em qualquer projeto
  - `docs/` (project-brief, adrs, identidade-visual) + `specs/` (project, stack, database, rules) = projeto, preenchido pelo usuário
  - `.planning/` = gerado pelo framework a partir dos anteriores
  - Razão: CLAUDE.md do framework antigo misturava regras universais com vocabulário GBC, impossibilitando reuso entre projetos.

- **[DECISION-02] 7 gates bloqueantes**
  - Gate 1 Bootstrap, Gate 2 UI-SPEC, Gate 3 Skills coverage, Gate 4 Security Baseline, Gate 5 Integration checkpoint, Gate 6 Reconciliation, Gate 7 Tests+Lint.
  - Razão: framework anterior tinha "recomendações" que eram sistematicamente ignoradas. Gate bloqueante é o único mecanismo que funciona.

- **[DECISION-03] Skills enforcement via `triggers.yaml` + plan-checker**
  - Cada skill declara `required_for` (path_pattern, task_type, keyword_any) e `dispensable_if`
  - Plan-checker: 2+ skills obrigatórias não citadas em `## Skills Consultadas` ou `## Skills Dispensadas` = BLOCK; 1 = FLAG
  - Override via seção "Skills Dispensadas (com justificativa técnica)"
  - Razão: "instalar skill" ≠ "consultar skill". Sem enforcement, skill vira documentação morta.

- **[DECISION-04] Herança do GSD base**
  - Os ~35 agentes `gsd-*` e ~65 workflows originais NÃO são redistribuídos neste framework.
  - Este framework MODIFICA cirurgicamente 3 workflows (`plan-phase`, `execute-phase`, `ui-phase`) + ADICIONA `bootstrap`, `reconcile-state`, gates-v3, skills-enforcement, templates novos, 10 skills novas.
  - Razão: reescrever os agentes do zero = perder ~40k linhas de contexto acumulado. O valor deste framework é a camada de enforcement + gaps cobertos.

- **[DECISION-05] Exemplos concretos em documentação didática**
  - Workflows e templates usam exemplos de um projeto real como ilustração pedagógica (Safe2Pay, accept_proposal, JWT em localStorage, etc.)
  - Cada arquivo com exemplos concretos tem caveat explícito marcando-os como hipotéticos
  - Razão: exemplo abstrato ("função X retorna Y") não ensina; exemplo concreto ensina MAS precisa ser explicitamente marcado como não-normativo.

- **[DECISION-06] Skills entregues em duas profundidades**
  - ⭐ Expandidas (conteúdo substantivo, production-ready): 4 quality + 1 br = 5 skills
  - 📝 Esqueletos (estrutura + triggers.yaml funcionais, conteúdo a expandir): 9 skills
  - Razão: expandir 14 skills de uma vez produziria 14 documentos medíocres. Melhor entregar 5 bem feitas como referência de qualidade + 9 esqueletos para o projeto expandir conforme uso real.

### [futuro] — próximas versões

- **v0.3.0** — Dogfooding (framework gerenciar a si mesmo com PLAN.md + ciclo de fases + reconcile). Adicionar dimensão 7 `Automated Accessibility` (axe-core) ao `gsd-ui-checker`. Endereçar §1.1 do Relatório 3 (performance budget como gate de CI integrado com config.json).
- **v0.4.0** — Integration-checker robusto com tree-sitter (AST parser) substituindo grep. Validação em campo com dados reais de 3-5 fases via `.planning/METRICS.md`. Endereçar as 6 referências externas do Relatório 3 §3 (Web.dev, MDN ARIA, Ionic, FastAPI, OWASP Mobile, Material Design 3).
- **v0.9.0** — Skills derivadas: `mobile/capacitor-patterns`, `frontend/angular-signals`, `backend/fastapi-patterns`, `mobile/owasp-mobile`.

---

## B. Inventário do que está completo

### B.1 Raiz

| Arquivo | Status | Notas |
|---------|--------|-------|
| `CLAUDE.md` | ✅ | Contrato mestre, ~200 linhas, genérico |
| `README.md` | ✅ | Guia de uso, arquitetura, plug-in em projeto existente |
| `FRAMEWORK-STATUS.md` | ✅ | (este arquivo) |

### B.2 Workflows críticos

| Workflow | Status | Função |
|----------|--------|--------|
| `bootstrap.md` | ✅ | Lê docs+specs, apresenta síntese, gera `.planning/` |
| `reconcile-state.md` | ✅ | Verifica afirmações contra código, 5 tipos de divergência |
| `plan-phase.md` | ✅ v3 | Aplica Gates 2, 3, 4 com enforcement |
| `execute-phase.md` | ✅ v3 | Gate 5 integration-checker detectando gaps G1-G8 |
| `ui-phase.md` | ✅ v3 | Flag `--mobile` ativa seções exclusivas |

### B.3 References normativos

| Arquivo | Status | Função |
|---------|--------|--------|
| `gates-v3.md` | ✅ | Spec dos 7 gates + matriz skills por tipo de task |
| `skills-enforcement.md` | ✅ | Como plan-checker usa triggers.yaml; matriz obrigatórias por área |

### B.4 Templates

| Arquivo | Status | Contaminação limpa |
|---------|--------|--------------------|
| `PLAN.md` | ✅ | Sim — integration contracts generalizadas |
| `UI-SPEC.md` | ✅ | Sim — tokens, copy, componentes usam `{placeholders}` |
| `SUGGESTIONS.md` | ✅ | Sim — exemplos genéricos |
| `RECONCILIATION.md` | ✅ | Caveat no topo — exemplos preservados como pedagógicos |
| `EXECUTION-LOG.md` | ✅ | Caveat no topo + exemplo generalizado |

### B.5 Skills

| Skill | Estado | Locale | Notas |
|-------|--------|--------|-------|
| `quality/performance-web-vitals` | ⭐ | universal | LCP/INP/CLS budgets, regras por métrica, CI enforcement |
| `quality/error-ux-patterns` | ⭐ | universal | Taxonomia, regras por categoria, retry patterns, copy-lib |
| `quality/observability-production` | ⭐ | universal | structlog, Sentry, OTel, middleware, PII filter |
| `quality/accessibility-pro` | ⭐ | universal | WCAG 2.1 AA, axe em CI, jest-axe em unit tests |
| `quality/i18n-ready-architecture` | ⭐ | universal | **v0.2** — Biblioteca, estrutura, ICU, DatePipe/CurrencyPipe, backend babel, locale routing, RTL |
| `product/api-design-contracts` | ⭐ | universal | **v0.2** — Response shape, error codes enum, HTTP semantics, paginação, versioning, idempotency, OpenAPI |
| `product/visual-regression-testing` | ⭐ | universal | **v0.2** — Storybook + Chromatic/Percy/Playwright, 5 estados mínimos, fixtures |
| `product/component-library-governance` | ⭐ | universal | **v0.2** — Regra dos 3, tokens, API opinativa, semver, deprecation path |
| `product/micro-animations-delight` | ⭐ | universal | **v0.2** — Taxonomia, easing/duration tokens, prefers-reduced-motion, FLIP, haptic |
| `mobile/offline-first` | ⭐ | universal | **v0.2** — Detecção via Capacitor+ping, queue idempotente, retry com dead letter, stale-while-revalidate |
| `mobile/push-notifications-architecture` | ⭐ | universal | **v0.2** — APNs/FCM, token lifecycle, pré-prompt, categorias, Notification Channels, deep linking |
| `br/brazilian-forms` | ⭐ | pt-BR | CPF/CNPJ/CEP/phone com DV, ViaCEP, mask progressiva, LGPD |
| `br/ux-copywriting-ptbr` | ⭐ | pt-BR | **v0.2** — Tom, tabela inglês→pt, CTAs verbo+substantivo, vocabulário canônico, padrões por contexto |
| `br/lgpd-compliance` | ⭐ | pt-BR | **v0.2** — Bases legais, consent granular, endpoints de direitos, anonimização, logs sem PII, DPA, incidentes |

Total: **14 skills** registradas · **14 ⭐ expandidas** · **0 📝 esqueletos**

### B.6 Docs (templates para preenchimento pelo usuário)

| Arquivo | Status |
|---------|--------|
| `docs/project-brief.md` | ✅ template 12 seções |
| `docs/adrs/README.md` + `ADR-template.md` | ✅ |
| `docs/identidade-visual/design-system.md` | ✅ template 11 seções |
| `docs/identidade-visual/tokens.json` | ✅ Style Dictionary |
| `docs/identidade-visual/brand.md` | ✅ |

### B.7 Specs

| Arquivo | Status |
|---------|--------|
| `specs/project.yaml` | ✅ |
| `specs/stack.yaml` | ✅ |
| `specs/database.yaml` | ✅ |
| `specs/rules.yaml` | ✅ (audit_trail com placeholder) |

### B.8 .planning (skeletons)

| Arquivo | Status |
|---------|--------|
| `PROJECT.md`, `STATE.md`, `ROADMAP.md` | ✅ templates iniciais |
| `REQUIREMENTS.md`, `MILESTONES.md`, `DECISIONS.md` | ✅ |
| `SUGGESTIONS.md`, `TECH-DEBT.md` | ✅ |
| `config.json` | ✅ gates ativos, perf budget, observability fields, ci_gates |
| `METRICS.md` | ✅ **v0.2** — log append-only de métricas por fase |
| `RETROSPECTIVE.md.template` | ✅ **v0.2** — template de retrospectiva ao fechar fase |

### B.9 Tooling (artefatos de enforcement reais) — novo em v0.2

| Arquivo | Função |
|---------|--------|
| `tooling/README.md` | Instruções de instalação em projeto existente |
| `tooling/ci/quality.yml.template` | GitHub Actions: lint, test, bundlesize, a11y, lighthouse, i18n, security |
| `tooling/ci/bundlesize.config.json` | Orçamentos de bundle JS/CSS (gzipped) |
| `tooling/ci/lighthouserc.json` | Thresholds Core Web Vitals + scores por categoria |
| `tooling/ci/pa11yci.json` | WCAG 2AA em múltiplos viewports |
| `tooling/pre-commit/.pre-commit-config.yaml` | ruff, mypy, eslint, prettier, gitleaks, conventional-commits |
| `tooling/jest/jest.setup.a11y.js` | jest-axe com regras WCAG 2.1 AA |
| `tooling/eslint/no-hardcoded-colors.js` | Custom rule proibindo hex/rgb/hsl hardcoded |

### B.10 Tests do framework — novo em v0.2

| Arquivo | Função |
|---------|--------|
| `tests/framework/run-all.sh` | Runner principal |
| `tests/framework/test_structure.sh` | Valida estrutura essencial + skills não-vazias |
| `tests/framework/test_plan_checker.sh` | Smoke do plan-checker (3 fixtures) |
| `tests/framework/test_reconcile.sh` | Smoke do reconcile (2 cenários) |
| `tests/framework/test_gate_bypasses.sh` | Smoke do gate bypass (5 casos) |
| `tests/framework/fixtures/` | 4 fixtures (good-plan, bad-plan-no-skills, bad-plan-bypass-no-reason, reconcile-divergence) |
| `tests/framework/README.md` | Como rodar + limitações (é smoke, não coverage) |

**Estado atual:** 4/4 suites passando. Rodar: `cd tests/framework && bash run-all.sh`.

### B.11 Bin (scripts de apoio) — novo em v0.2

| Arquivo | Função |
|---------|--------|
| `bin/collect-metrics.sh <phase_id>` | Coleta automática + gera rascunho em METRICS.md |
| `bin/export-telemetry.sh [phase_id]` | Exporta JSON anonimizado conforme TELEMETRY-SCHEMA.json |

### B.12 Schema de telemetria — novo em v0.2

| Arquivo | Função |
|---------|--------|
| `TELEMETRY-SCHEMA.json` | JSON Schema v1 do formato anonimizável de métricas por fase |

### B.13 Sprint infrastructure — novo em v0.2.1

| Arquivo | Função |
|---------|--------|
| `references/sprint-slicing.md` | Duas ordens canônicas (vertical_value + admin_first) com critério de decisão |
| `references/visual-fidelity.md` | Regras de enforcement de identidade visual em sprints |
| `templates/SPRINT.md` | Template completo com front-matter YAML + Visual Contract + UX Skills Applied |
| `workflows/gsd:sprint-plan.md` | Workflow que quebra milestone em sprints testáveis |
| `.planning/SPRINTS.md` | Tabela append-only de sprints (planejado/em andamento/fechado) |
| Campo `sprint_ui_matrix` em `references/skills-enforcement.md` | Matriz de skills UX obrigatórias por flag do sprint |
| Novos campos em `.planning/config.json` | `slicing_strategy`, `visual_tokens_mode`, `sprint_planning` |
| Novo passo 3.5 em `workflows/bootstrap.md` | Escolha de strategy + validação de tokens.json |
| Sprint-aware em `workflows/plan-phase.md` | Detecta sprint_id vs phase_id, Gate 2 valida Visual Contract |
| 3 fixtures em `tests/framework/fixtures/` + `test_sprint_checker.sh` | Smoke test do sprint-checker (5/5 passando) |

---

## C. Gap analysis vs. Relatório 3 (nível internacional)

### C.1 Dez skills propostas

| # | Skill | Relatório pede | Status neste framework | Gap |
|---|-------|----------------|------------------------|-----|
| 1 | `performance-web-vitals` | Grande (40-60 regras) | ⭐ expandida | Nenhum significativo |
| 2 | `error-ux-patterns` | Médio (25-35 regras) | ⭐ expandida | Nenhum significativo |
| 3 | `observability-production` | Médio (30 regras) | ⭐ expandida | Nenhum significativo |
| 4 | `api-design-contracts` | Grande (40-50 regras) | ⭐ expandida em v0.2 | Nenhum significativo |
| 5 | `visual-regression-testing` | Médio (25 regras) | ⭐ expandida em v0.2 | Nenhum significativo |
| 6 | `i18n-ready-architecture` | Médio (30 regras) | ⭐ expandida em v0.2 | Nenhum significativo |
| 7 | `offline-first-mobile` | Médio (30 regras) | ⭐ expandida em v0.2 (`mobile/offline-first`) | Nenhum significativo |
| 8 | `micro-animations-delight` | Médio (25 regras) | ⭐ expandida em v0.2 | Nenhum significativo |
| 9 | `component-library-governance` | Médio (25 regras) | ⭐ expandida em v0.2 | Nenhum significativo |
| 10 | `push-notifications-architecture` | Médio (30 regras) | ⭐ expandida em v0.2 | Nenhum significativo |

**Score: 10/10 ⭐ expandidas.** Plan-checker reconhece todas e pode bloquear planos que não as citem quando aplicáveis.

### C.2 Seis referências externas a adaptar

| Fonte | Prioridade (Rel. 3) | Status | Ação futura |
|-------|---------------------|--------|-------------|
| Web.dev / Google Core Web Vitals | Alta | ❌ não adaptada | Integrar via expansão de `performance-web-vitals` em v0.4 |
| MDN Accessibility Guide (ARIA patterns) | Alta | ❌ não adaptada | Integrar via expansão de `accessibility-pro` em v0.4 |
| Ionic Blog / Capacitor Docs | Média | ❌ não adaptada | Criar skill `mobile/capacitor-patterns` em v0.4 |
| Angular Signals RFC | Alta | ❌ não adaptada | Criar skill `frontend/angular-signals` em v0.4 |
| FastAPI Best Practices (tiangolo) | Média | ❌ não adaptada | Expandir em skill `backend/fastapi-patterns` em v0.4 |
| OWASP Mobile Top 10 | Alta | ❌ não adaptada | Complementar `owasp-security` (herdada) com `mobile/owasp-mobile` em v0.4 |

**Score: 0/6. Todas são ação futura — nenhuma é blocker para v0.1.**

### C.3 Quatro mudanças de workflow

| Mudança | Status | Nota |
|---------|--------|------|
| §1.1 Performance budget como gate de CI | ⚠️ parcial | Skill `performance-web-vitals` define budget + regras. **Falta** integrar com `.planning/config.json > ci_gates` e adicionar dimensão ao plan-checker que valida menção a lazy loading/image optimization/code splitting em fases frontend. |
| §1.2 Error observability como requisito de fase backend | ✅ | Resolvido via Gate 4 (Security Baseline) + skill `observability-production` required_for `new_endpoint` + seção `## Observability checklist` obrigatória em PLAN.md |
| §1.3 Accessibility audit como dimensão do `gsd-ui-review` | ⚠️ parcial | `ui-checker` tem 6 dimensões + 7ª se `--mobile`. **Falta** dimensão automated-a11y via axe-core no próprio checker (hoje a skill `accessibility-pro` cobre o tema mas não é executada pelo checker). |
| §1.4 OpenAPI spec como artefato obrigatório em verify-phase | ❌ não endereçado | Requer expansão de `api-design-contracts` + modificação em `verify-phase` (workflow herdado do GSD base, não redistribuído aqui). |

**Score: 1/4 ✅, 2/4 ⚠️ parcial, 1/4 ❌. v0.2 deve endereçar §1.1 e §1.3 completos.**

### C.4 Expansão de CI

Relatório §4.3 pede adições ao `ci.yml`:

| Etapa CI | Status em v0.2 |
|----------|-----------------|
| `@axe-core/cli` / pa11y em http://localhost:4200 | ✅ `tooling/ci/pa11yci.json` + job no `quality.yml.template` |
| `bundlesize` | ✅ `tooling/ci/bundlesize.config.json` + job no `quality.yml.template` |
| Chromatic (quando Storybook existir) | ✅ Job pronto no `quality.yml.template` (comentado; ativar quando projeto configurar Chromatic) |
| Lighthouse CI | ✅ `tooling/ci/lighthouserc.json` + job no `quality.yml.template` |

**Score: 4/4 ✅ em v0.2.** Os artefatos não são gerados automaticamente no bootstrap — usuário copia com `cp tooling/ci/*.json .` e `cp tooling/ci/quality.yml.template .github/workflows/quality.yml` (ver `tooling/README.md`). Decisão deliberada: alguns projetos não usam GitHub Actions; não forçar.

---

## D. Contaminações detectadas e limpeza

Auditoria realizada após feedback do usuário ("coisas como safe2pay não são do framework"). Contaminações vieram do projeto real GBC usado como referência durante o design do framework.

### D.1 Skills universais (⚠️ crítico — devem ser domain-agnostic)

| Skill | Contaminação | Correção aplicada |
|-------|--------------|---------------------|
| `quality/error-ux-patterns` | "Proposta já aceita por outro profissional" em taxonomia + copy-lib | ✅ Substituído por "Item reservado por outro usuário" + `business.resource.already_taken` |
| `quality/observability-production` | `"service.name": "gbc-backend"` hardcoded + exemplo `accept_proposal` | ✅ Substituído por `settings.SERVICE_NAME` + exemplo `confirm_order` |
| `quality/accessibility-pro` | `aria-label="Aceitar proposta"` + tabela "Suas propostas" | ✅ Substituído por `aria-label="Confirmar"` + tabela "Seus pedidos" |
| `br/ux-copywriting-ptbr` | "Enviar proposta", "Proposta enviada" em exemplos | ✅ Substituído por "Enviar mensagem", "Pedido enviado" |

### D.2 Templates (⚠️ médio — placeholders devem ser neutros)

| Template | Contaminação | Correção aplicada |
|----------|--------------|---------------------|
| `UI-SPEC.md` | `--gbc-proposal-accepted`, `gbc-proposal-card`, "Suas propostas" | ✅ Trocado por `{prefix}-{status-semantico}` e placeholders |
| `PLAN.md` | `service_request_id` em integration contracts | ✅ Trocado por `{resource_id}` com placeholder pattern |
| `RECONCILIATION.md` | Safe2Pay 4/26 como exemplo | ✅ Caveat explícito no topo marcando como ilustrativo |
| `SUGGESTIONS.md` | "chat/proposta/pagamento", "Safe2Pay service já completo" | ✅ Generalizado |
| `EXECUTION-LOG.md` | `fix(phase-5): INTEG-01 accept_proposal` | ✅ Caveat + substituído por `{endpoint}` |

### D.3 Workflows e references (ℹ️ didáticos — OK com caveat)

| Arquivo | Estratégia |
|---------|------------|
| `workflows/reconcile-state.md` | ✅ Caveat no topo — exemplos Safe2Pay preservados como pedagógicos |
| `workflows/execute-phase.md` | ✅ Caveat antes do Gate 5 — exemplos de gap preservados |
| `workflows/ui-phase.md` | ✅ `gbc-proposal-card` → `{prefix}-{recurso}-card` em exemplo de herança |
| `references/gates-v3.md` | ✅ Safe2Pay rotacionado entre Stripe/Asaas/Mercado Pago/PayPal |
| `references/skills-enforcement.md` | ✅ Exemplos generalizados (proposta/workspace → recurso/tenant) |

### D.4 Specs (⚠️ alto — projeto deve preencher)

| Spec | Contaminação | Correção aplicada |
|------|--------------|---------------------|
| `specs/rules.yaml > audit_trail` | `"service_requests"` hardcoded | ✅ Substituído por `{tabela_critica_1}`, `{tabela_critica_2}` com comentário de exemplos |

**Score da auditoria: 14/14 contaminações endereçadas.** Residuais intencionais: listas de gateways de pagamento (Stripe, Asaas, Mercado Pago, Safe2Pay, PayPal) em `references/` são exemplos de *categoria*, não contaminação.

---

## E. TODOs priorizados (ordem sugerida para próximas sessões)

### E.1 Prioridade ALTA (v0.3 — bloqueia evolução para 9/10)

1. **Dogfooding: framework gerenciar a si mesmo.** Criar `.planning/PLAN.md` para as próximas mudanças do framework, passar pelos próprios 7 gates, rodar `reconcile-state` sobre si mesmo, alimentar `.planning/METRICS.md` com dados reais. Sem isso, qualquer afirmação sobre valor do framework é especulação.

2. **Validação em campo (3-5 fases reais).** Rodar o framework em projeto de produção. Coletar métricas via `bin/collect-metrics.sh`. Exportar via `bin/export-telemetry.sh`. Revisar semanalmente quais skills são citadas, quais são dispensadas, onde `--skip-gate` aparece com que `--reason`. Essa iteração alimenta v0.4.

3. **Integration-checker robusto (grep → AST).** Trocar `grep -rqE` por `tree-sitter` para TS/Python, reduzindo falsos positivos (matches em comentários, strings, identificadores parciais). Reescreve `tests/framework/test_reconcile.sh` para usar o parser real.

4. **Dimensão 7 `Automated Accessibility` no `gsd-ui-checker`** — axe-core executado contra templates bloqueia se falhar. Flag `--with-axe` opt-in (exige ambiente que execute o app).

5. **§1.1 Relatório 3 completo** — plan-checker valida menção a lazy loading / image optimization / code splitting em fases frontend, integrando com `.planning/config.json > ci_gates`.

### E.2 Prioridade MÉDIA (v0.4)

6. **Adaptar Web.dev Core Web Vitals** e **MDN ARIA patterns** — aprofundar `performance-web-vitals` e `accessibility-pro` com referências externas consolidadas.

7. **Criar skills derivadas:** `mobile/capacitor-patterns`, `frontend/angular-signals`, `backend/fastapi-patterns`, `mobile/owasp-mobile`.

8. **Workflow `/gsd:metrics-dashboard`** — análise sobre `.planning/METRICS.md` mostrando tendências (ex: "taxa de fix_iterations caiu de 2.4 para 0.8 nas últimas 5 fases"; "skill X citada 80%, mas quando dispensada a taxa de bug sobe — indicador de que ela puxa peso real").

9. **Test harness: mutation testing.** Alterar 1 coisa no checker, confirmar que algum teste falha. Hoje os smoke tests apenas validam que o caminho feliz funciona — mutation testing valida que os testes têm dentes.

### E.3 Prioridade BAIXA (v0.5+)

10. **Test harness: property-based.** Gerar planos aleatórios, validar invariantes ("nunca existe PASS sem ## Skills Consultadas"). Requer Hypothesis ou similar.

11. **Interface web para `.planning/METRICS.md`** — hoje é markdown; se o log crescer para 50+ entradas, vale um viewer simples em HTML estático.

### E.4 Manutenção contínua

- **Auditoria periódica de contaminações:** rodar a cada 3 releases para detectar se vocabulário de projeto vazou para skills universais. Comando de scan:
  ```bash
  grep -rn -iE "safe2pay|gbc|getbestcat|visol|augure" .claude/ docs/ specs/ tooling/ --include="*.md" --include="*.yaml"
  ```
  (nenhum resultado = limpo; resultados apenas em listas de gateways e em caveats = OK)

- **Revisar métricas do plan-checker trimestralmente:** se em produção `plan_revisions` fica consistentemente > 3, triggers.yaml estão cobrando skills desnecessárias — ajustar.

- **Revisar gates bloqueantes semestralmente:** se um gate é sistematicamente overridden via `--skip-*`, ele não está agregando valor — repensar. Dados em `gates_bypassed[].reason` do METRICS.md informam.

- **Rodar `tests/framework/run-all.sh` antes de cada release** — 4/4 verde é pré-requisito para tag.

---

## F. Como atualizar este arquivo

Este arquivo é manual, não automático. Ao fazer mudança estrutural no framework:

1. Adicionar entrada em **A. Changelog** com data + decisões tomadas
2. Atualizar tabelas em **B. Inventário** se arquivos novos/removidos
3. Atualizar matriz em **C. Gap analysis** se skills mudaram de ⭐ ↔ 📝
4. Atualizar **D. Contaminações** se nova auditoria foi feita
5. Ajustar **E. TODOs** movendo itens entre prioridades ou marcando como feitos

Atualizar **"Última atualização"** e incrementar **"Versão semântica"** no topo.
