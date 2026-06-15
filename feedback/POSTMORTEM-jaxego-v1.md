# Postmortem — Jaxegô v1.0 (o que o GSD deixou passar)

> Classificação de cada falha: **[DOC]** falha de documentação/planejamento
> (o framework gerou ou aceitou um artefato fraco) · **[COD]** falha de
> codificação (executor entregou código quebrado mesmo com plano adequado) ·
> **[PROC]** falha de processo do framework (mecanismo previsto não rodou ou
> validou a coisa errada).
>
> Toda falha tem evidência verificável no repo.

---

## Resumo executivo

14 phases fecharam "verdes". O `STATE.md` declara 100% dev/test. Na prática:

- Login não roteia para superfície nenhuma (loop login→login).
- O núcleo do app do entregador (oferta→aceite→entrega ativa) não tem tela.
- Fila de KYC e "criar área" não têm UI (backend existe).
- Homes de entregador e admin são placeholders.
- Nada foi validado ao vivo (`HUMAN-UAT-BACKLOG.md` vazio).

Nenhum gate pegou nada disso, porque **nenhum gate exige produto usável**.

---

## Falhas — uma a uma

### F1 — Reconcile conta endpoint como entrega, ignorando UI inalcançável · **[PROC]**

`areas/router.py:56` tem `create_area` (POST/PATCH/archive completos). Não existe
nenhuma tela para criar/editar área (`admin-plataforma/` só tem visão-geral,
pessoas, disputas). O reconcile da Phase 13 fechou sem gap porque comparou
"prometido × código presente" e o código (endpoint) estava lá.

- **Causa GSD:** Gate 6 / Regra 8 (reconcile) é **grep de existência**, não de
  alcançabilidade. "Entreguei o CRUD de área" passou com 0% de UI.
- **Classe:** PROC (reconcile validou a coisa errada).

### F2 — "REAL" verde em cima de stub · **[PROC]**

`admin/inicio.page.ts` (17 linhas) e `entregador/{entregas,ganhos,perfil}.page.ts`
(20-41 linhas) são `<jx-empty-state>` puros ("aparecem aqui em breve"). Têm
testes que passam, têm rota, têm o arquivo. Contam como "tela existe".

- **Causa GSD:** limitação #3 (testes de existência ≠ semântica) sem mitigação.
  Nenhum gate distingue empty-state-placeholder de tela funcional.
- **Classe:** PROC + COD (executor entregou stub onde o protótipo especificava
  tela rica — `tpl-c-home`, `tpl-a-dash`, `tpl-c-profile`).

### F3 — Componente construído e nunca montado (UI órfã) · **[COD]**

`entregador/oferta/offer-sheet.component.ts` e `admin/kyc/queue-table.component.ts`
existem, com `.stories.ts` (Storybook dá falso sinal de "pronto"), mas **nenhuma
página os usa** e **nenhuma rota leva a eles**. A fila de KYC é inalcançável; a
oferta nunca sobe.

- **Causa GSD:** reconcile não detecta componente sem import/uso em página
  roteada. Storybook stories inflam a sensação de cobertura.
- **Classe:** COD (não-fiação) + PROC (reconcile cego a órfãos).

### F4 — Página de entrega ativa: só service, sem tela · **[COD/DOC]**

`entregador/entrega-ativa/` tem **apenas** `location-polling.service.ts`. A
máquina de 7 estados do entregador (`tpl-c-active` no protótipo, o centro do
produto) **não tem página**. Backend (`dispatch`, `deliveries`, `proofs`) pronto.

- **Causa GSD:** o protótipo rico não virou contrato de UI obrigatório; o plano
  da phase deixou a tela fora e o reconcile não tinha como cobrar (não há "tela
  X prometida"). 
- **Classe:** DOC (UI-SPEC não ancorou no protótipo) + COD (entregou meio fluxo).

### F5 — Forward-reference para tarefa futura, abandonada em silêncio · **[PROC]**

`login.page.ts:87` navega para `/`; `app.routes.ts:13` redireciona `/` → `/entrar`.
Comentário no código: *"surface routing in T-06"*. `inicio.page.ts:72`:
*"offer-sheet wired in T-11"*. `inicio.page.ts` inteiro é dirigido por `@Input()`
que nenhum pai preenche (*"execution is Phase 9"*). **Essas T-06/T-11/Phase 9
nunca voltaram para fechar a referência.**

- **Causa GSD:** referências a tarefas/phases futuras ("T-XX", "Phase N") não são
  rastreadas. Quando a phase referenciada fecha, ninguém checa se a back-reference
  foi cumprida. É a Regra 12 (LOW confidence vira task) **não aplicada a fiação
  diferida**.
- **Classe:** PROC. Resultado visível: produto não navega.

### F6 — `HUMAN-UAT-BACKLOG.md` vazio apesar de dezenas de "pendente ao vivo" · **[PROC]**

`STATE.md` lista, phase a phase, itens "Pendente ao vivo": migration reversível,
trigger append-only (errno 1644), geofence `ST_Distance_Sphere`, concorrência
`FOR UPDATE`, integration check B2. O `HUMAN-UAT-BACKLOG.md` tem **0 pendentes**.
A promoção automática que o próprio arquivo descreve (autopilot promove
`human_needed` → backlog) **não rodou**.

- **Causa GSD:** o mecanismo de promoção de UAT é documentado mas não é
  enforced/verificado. "Pendente ao vivo" evaporou entre sessões.
- **Classe:** PROC. Consequência: nada foi validado contra MySQL/B2 reais.

### F7 — Gate de integração desligado justo onde era crítico · **[DOC]**

No `ROADMAP.md`, phases nitidamente cross-layer vieram com
`integration_check: false` (ex.: Phase 3 "shell frontend 3 superfícies", Phase 7
"criação de entrega"). O login→superfície, fila→detalhe, oferta→aceite nunca
foram exercidos como contrato.

- **Causa GSD:** `integration_check` é flag manual no roadmap; o roadmapper marcou
  `false` em phases que tocam navegação/cross-surface. Não há regra que force
  `true` quando a phase mexe em rotas/superfícies.
- **Classe:** DOC (decisão de planejamento errada, aceita pelo framework).

### F8 — ADRs citados em todo lugar, inexistentes no lugar canônico · **[DOC]**

`docs/adrs/` só tem `ADR-template.md` e `README.md`. Mas planning e código citam
ADR-003, ADR-008, ADR-013, ADR-101, ADR-104, ADR-005… Todas vivem (no máximo) no
`DECISIONS.md`. O CLAUDE.md §3 declara `docs/adrs/ADR-*.md` como **lei** — e a lei
não existe como arquivo.

- **Causa GSD:** nada valida que um `ADR-NNN` referenciado exista como arquivo.
  Decisões arquiteturais ficaram sem o registro que o próprio contrato exige.
- **Classe:** DOC/PROC.

---

## Onde a documentação foi fraca/frágil (resumo)

1. **UI-SPEC não ancorou no `prototipo.html`.** O protótipo é rico e concreto
   (home do entregador, dashboard admin, máquina de 7 estados, perfil com score).
   As phases trataram essas telas como opcionais/diferidas → viraram stubs. O
   protótipo deveria ser **wireframe-contract obrigatório** (Gate 2 cita
   "wireframe fidelity" mas não bloqueou ausência de tela).
2. **`integration_check` e fronteiras cross-surface ficaram a critério manual**
   do roadmapper, que errou para `false` em phases de navegação.
3. **Fiação diferida ("T-06", "Phase 9") não tem artefato de rastreio.** Vira
   comentário no código e some.
4. **A noção de "tela pronta" não foi definida.** Sem critério, empty-state conta.

## Onde foi falha de codificação (resumo)

1. **Login navega para um redirect que volta pra ele mesmo** — bug observável
   sem precisar de spec (`login.page.ts:87`). O executor deveria ter visto o loop.
2. **Stubs entregues como tela** onde o protótipo especificava conteúdo rico.
3. **Componentes órfãos** (offer-sheet, queue-table) construídos e não fiados.
4. **Página de entrega ativa ausente**, só o service.
5. **Rota morta/duplicada** (`/entregador/ganhos` stub vs `/saldo` real).

## A falha-raiz comum

O GSD otimiza para **gates de artefato verdes**. Nenhum gate exige
**alcançabilidade, fiação e fluxo fechado**. Rodar 14 phases em autopilot sem um
checkpoint de UAT humano por milestone fez a dívida de integração crescer
invisível até o produto inteiro parecer quebrado — apesar de cada peça, isolada,
"passar".
