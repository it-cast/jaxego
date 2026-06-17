# Field Report 02 — o que o GSD não pegou (sessão de reconstrução + integração)

> Field data real de uma sessão longa: reconstrução (MR-0..MR-5 + gaps MG-1/2),
> merge com trabalho paralelo de outro dev, e a cascata de falhas de CI/deploy que
> só apareceram **depois** do push. Complementa `POSTMORTEM-jaxego-v1.md` e
> `GSD-IMPROVEMENTS.md` com evidência nova.
>
> Tese-raiz (confirmada de novo): **o GSD valida os artefatos DELE (gates internos),
> mas não conhece nem roda o CI REAL do projeto** — então "verde no GSD" ≠ "verde no
> pipeline". Cada gate do repo (ruff format, karma, zero-hex, deploy-order) falhou
> **serialmente em produção** porque nada os rodou antes do push.

---

## Parte A — Falhas observadas NESTA sessão (com evidência)

### A1 — `ruff format --check` vermelho (job `lint (ruff)`) · **[PROC/EXEC]**
Rodei `ruff check` (regras) a cada incremento, mas **nunca `ruff format --check`**. O CI
roda os dois. 7 arquivos precisavam de format. Só descobri pelo run vermelho.
- **Gap GSD:** não há "rode o conjunto COMPLETO de checks do repo antes de declarar pronto".
  O Gate 7 do GSD diz "tests + lint verde" genérico — não enumera os checks reais do projeto.

### A2 — Karma (`web`) vermelho: specs desatualizados vs código · **[PROC]**
2 causas: (a) `login.page.spec` mockava `AuthService` sem `loadMe`/`surfaceHome` — métodos
que EU adicionei ao fluxo; (b) `nova-entrega.spec` esperava `/v1/neighborhoods` mas o
código chama `/v1/neighborhoods/catalog`. Rodei build+lint+pytest antes do push, mas
**não `ng test`**.
- **Gap GSD:** mudar a API de um serviço não dispara "atualize os specs que mockam esse
  serviço". Reconcile/tests do GSD são de existência, não pegam **drift spec↔código**.

### A3 — `Zero hex hardcoded` vermelho · **[PROC]**
2 hex cravados (`#ffffff`, `#22c55e`) na tela TOTP vinda do merge. O projeto tem um
**gate customizado** (`grep` por hex em `.scss` fora de `src/styles/`) que o GSD
desconhece totalmente.
- **Gap GSD:** o GSD tem a noção "zero hex / tokens only" como *regra de skill*, mas não
  sabe que o **repo** materializou isso como um **job de CI** — e não o roda.

### A4 — Deploy rodava em PARALELO com o CI (ordem errada) · **[DOC/PROC]**
`deploy.yml` disparava em `push:[master]`, então deployava **junto** com o CI (podia
deployar código que o CI reprovaria). O comentário dizia "após o CI" — mentira.
- **Gap GSD:** as skills `monorepo-deploy-safety` e `github-actions-ci` não têm um
  **invariante**: "deploy SÓ após CI verde" (workflow_run + `if: success`). Release-safety
  não checa a *ordem* entre pipelines.

### A5 — `DATABASE_URL` quebrou só no deploy ao vivo · **[DOC]**
`env_file` do Docker mantém **aspas literais**; um `.env` com `DATABASE_URL="..."` ou vazio
quebrava o `make_url` com traceback críptico. Só apareceu no 1º deploy real.
- **Gap GSD:** a skill de deploy não inclui **robustez de config** (normalizar aspas,
  erro claro se vazio) nem **pré-flight de env** antes de migrar.

### A6 — Divergência de 2 desenvolvedores / merge · **[DOC]**
Acumulei **39 commits locais** numa linha; outro dev empurrou TOTP+correções em paralelo.
Resultado: 9 conflitos (auth, shells, config, rotas). O GSD é **single-stream** — não tem
estratégia de branch/PR nem "integre cedo, não acumule".
- **Gap GSD:** zero orientação sobre concorrência: branch por phase, PR, rebase frequente,
  não empilhar commits em master local.

### A7 — Reafirmação do Field Report 01 (continuam válidos)
Alcançabilidade (endpoint↔UI), stub-como-pronto, componente órfão, fiação diferida
("T-XX"), HUMAN-UAT vazio, `integration_check` off. Tudo apareceu de novo nesta sessão
(ex.: login não roteava; admin sem nav; fila KYC sem tela; `/me` ausente).

---

## Parte B — O que INCLUIR no GSD para o próximo dar certo

### B1 — Gate "CI real do projeto" (o mais importante)
No bootstrap/scan, **detectar os workflows de CI** do repo (`.github/workflows/`) e
**extrair os comandos** de cada job. A *definition of done* passa a exigir rodar o
**equivalente local de TODOS** antes de declarar pronto/push:
- build, lint, **format --check**, typecheck, **unit tests (karma/jest)**, e **gates
  customizados** (ex.: o `grep` de zero-hex). 
- Se um comando não roda local, marcar como "só-CI" explicitamente (não silenciar).
> Isto sozinho teria evitado A1, A2, A3.

### B2 — Pré-push/pré-PR obrigatório
Um passo `gsd verify pre-push` que roda o pacote do B1 e **bloqueia** o push se algo
falhar. Hoje o GSD "fecha phase" sem nunca rodar o CI do repo.

### B3 — Release-safety: ordem e robustez (skill `monorepo-deploy-safety` v2)
- Invariante: **deploy só após CI verde** (`workflow_run` + `if: conclusion==success`).
  Um checker que lê os workflows e falha se o deploy dispara em `push` paralelo.
- **Pré-flight de env** no deploy (variáveis obrigatórias não-vazias, sem aspas) + erro
  claro. **Robustez de config** no app (normalizar valores vindos de `env_file`).
> Evitaria A4 e A5.

### B4 — Detector de drift spec↔código
Quando um serviço/endpoint muda de assinatura/URL, sinalizar os **specs/mocks que o
referenciam** como candidatos a atualizar (grep por nome do método/URL nos `*.spec.*`).
Parte do reconcile.
> Evitaria A2.

### B5 — Estratégia de concorrência (novo guia)
Guia curto: branch por phase + PR; rebase/merge cedo e frequente; **não acumular** dezenas
de commits em master local; o `gsd:pr-branch` já existe — torná-lo o caminho padrão, não
opcional. Avisar quando `git status` mostra "ahead N" com N grande vs origin.
> Reduziria o custo de A6.

### B6 — Gate de alcançabilidade + stub (do Field Report 01 — ainda não implementado)
Endpoint de CRUD sem UI = FLAG; componente com story sem uso em rota = FLAG; página só
empty-state onde o protótipo pede conteúdo = STUB-GAP. Reafirmado: continua sendo o maior
buraco entre "passa nos gates" e "produto usável".

---

## Parte C — Honestidade sobre a culpa (executor + framework)

- **Executor (eu):** declarei incrementos "verdes" rodando um SUBconjunto dos checks
  (build+lint+pytest) e empurrei sem rodar **format/karma/zero-hex** — exatamente o
  anti-pattern do Field Report 01 em escala menor. Ajuste de comportamento já adotado:
  rodar o pacote completo do B1 antes de cada push.
- **Framework:** não dá ao executor a *lista* do que rodar (não conhece o CI do repo),
  então o "subconjunto" foi adivinhado. B1/B2 transformam isso de disciplina-frágil em
  gate-enforced.

## Resumo: 1 mudança que resolve 80%
**Fazer o GSD conhecer e rodar o CI real do projeto como parte da definition-of-done
(B1+B2).** Quase toda falha desta sessão (A1, A2, A3) é "o pipeline pegou o que o GSD não
rodou". O resto (A4/A5 release-safety, A6 concorrência, B6 alcançabilidade) são camadas
de maturidade por cima dessa base.
