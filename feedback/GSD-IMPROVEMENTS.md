# Melhorias propostas ao GSD Framework

> Cada item traduz uma falha do `POSTMORTEM-jaxego-v1.md` em uma **mudança de
> mecanismo** concreta. Priorizado por impacto/custo. Formato: o que muda, onde,
> e o critério objetivo que passa a ser exigido.

---

## P0 — Fecham o buraco "artefato verde ≠ produto usável"

### M1 — Gate de Alcançabilidade (novo Gate 9) — fecha F1, F3

Antes de fechar phase com backend+frontend, rodar um checker que valida:

- **Todo endpoint de CRUD tem rota de UI que o consome.** Grep dos paths dos
  routers × chamadas nos `*.service.ts` × rotas em `app.routes.ts`. Endpoint sem
  consumidor de UI = FLAG (não BLOCK se for API pública intencional; exige tag
  `api_only: true` no plano para passar).
- **Todo componente com `.stories.ts` é importado em ao menos uma página
  roteada.** Componente órfão = FLAG.
- **Toda rota resolve para página não-stub** (ver M2).

Implementação: novo agente `gsd-reachability-checker` + comando no execute-phase.
Saída: `REACHABILITY.md` por phase. Barato (grep + AST leve).

### M2 — Detector de stub no reconcile — fecha F2

`gsd:reconcile-state` passa a marcar como **gap** qualquer página cujo template
seja só placeholder. Heurística objetiva:

- Página `.page.ts` cujo template contém **apenas** `<jx-empty-state>` /
  `EmptyStateComponent` e < N linhas, **e** cuja phase prometeu uma tela
  funcional (entry no PLAN com critério de aceite de conteúdo) → `STUB-GAP`.
- Stub legítimo (empty state de "lista vazia" dentro de uma página com lógica)
  não dispara — o gatilho é "a página inteira é o placeholder".

Adicionar à definição canônica: **"tela pronta" = renderiza dado real OU estados
de carga/erro/vazio de um fluxo real, não um placeholder "em breve".**

### M3 — Rastreio de fiação diferida — fecha F5

Proibir forward-reference solta no código/plano. Regra nova (Regra 13):

> Qualquer adiamento de fiação ("será ligado em T-XX / Phase N", `@Input()` sem
> produtor, comentário "wired later") **deve** virar:
> (a) uma task explícita no PLAN da phase-alvo com critério de aceite, OU
> (b) uma TD com `urgency_class`.
> Comentário no código não é rastreamento.

Enforcement: hook/grep no execute-phase procurando padrões (`wired in`,
`surface routing in`, `TODO.*Phase`, `@Input()` sem binding em pai) → exige
back-reference registrada. É a Regra 12 estendida para fiação.

### M4 — Promoção de UAT verificada, não confiada — fecha F6

O autopilot **falha** o fechamento da phase se houver itens "Pendente ao vivo" /
`human_needed` no VERIFICATION que não foram espelhados em `HUMAN-UAT-BACKLOG.md`.
Checagem objetiva: contar itens `human_needed` nos `*-VERIFICATION.md` da phase ×
entries no backlog. Divergência = BLOCK.

Além disso: `complete-milestone` e `ship` recusam rodar com backlog de UAT não-zerado
(ou exigem `--skip-gate` com motivo, registrado em METRICS).

---

## P1 — Corrigem decisões de planejamento que o framework aceitou

### M5 — `integration_check` deixa de ser opt-in puro — fecha F7

Regra de derivação automática no roadmapper/plan-phase:

> Se a phase toca **rotas, navegação, autenticação→superfície, ou conecta duas
> superfícies** (loja↔entregador↔admin), `integration_check` é forçado para
> `true`. O roadmapper não pode marcar `false` nesses casos sem ADR.

Adicionar "navegabilidade pós-login" como E2E flow obrigatório no
`gsd-integration-checker` para qualquer projeto com auth + múltiplas superfícies.

### M6 — Protótipo/wireframe como contrato bloqueante — fecha F4, F8(parcial)

Quando existe `prototipo.html` / wireframes no `projeto/`:

- O `gsd-ui-researcher` **deve** enumerar cada tela do protótipo e mapear para uma
  phase. Telas não-mapeadas = gap explícito no roadmap (não somem).
- Gate 2 (UI-SPEC / wireframe fidelity) passa a **BLOCK** quando uma tela do
  protótipo prometida na phase não tem página correspondente não-stub (usa M2).

### M7 — Validador de existência de ADR — fecha F8

Hook/checker: todo `ADR-NNN` referenciado em planning/código deve existir como
`docs/adrs/ADR-NNN-*.md`. Referência órfã = FLAG no health/reconcile. E o
`bootstrap`/`ingest` passa a materializar as decisões de `DECISIONS.md` que têm
ID `ADR-*` como arquivos-stub de ADR (com status), não só linha em tabela.

---

## P2 — Mudanças de processo (autopilot)

### M8 — Checkpoint de UAT humano por milestone — fecha a falha-raiz

O `autopilot` **para obrigatoriamente** no fim de cada milestone (não só em
gate-block/verification-fail) e exige um passe de UAT humano sobre o **produto
integrado** antes de seguir. Em greenfield, autopilot puro através de N milestones
sem UAT é proibido por default (exige flag explícita `--no-milestone-uat` com
aviso de risco).

### M9 — "Walking skeleton" antes de profundidade — recomendação de slicing

Adicionar ao guia de slicing: a **primeira** phase de qualquer projeto com auth +
superfícies entrega o esqueleto navegável (login→cada superfície→tela base real,
ainda que magra) **antes** de aprofundar qualquer feature. Evita o padrão Jaxegô
(backend fundo, navegação inexistente).

---

## Resumo: mapa falha → mecanismo

| Falha (postmortem) | Classe | Mecanismo novo/alterado |
|---|---|---|
| F1 endpoint sem UI conta como entregue | PROC | M1 |
| F2 stub conta como tela | PROC/COD | M2 |
| F3 componente órfão | COD/PROC | M1 |
| F4 tela de fluxo central ausente | DOC/COD | M2, M6 |
| F5 fiação diferida abandonada | PROC | M3 |
| F6 UAT ao vivo evaporou | PROC | M4 |
| F7 integration_check off onde importava | DOC | M5 |
| F8 ADRs inexistentes | DOC | M7 |
| falha-raiz (artefato ≠ produto) | — | M8, M9 |

## Nota de honestidade

O framework **já documenta** as limitações que causaram isto (FRAMEWORK-STATUS.md
§v0.4.0: testes de existência ≠ semântica; skill citada ≠ aplicada; zero field
data). O que faltava era **field data** que mostrasse o custo real dessas
limitações quando somadas ao autopilot. Este caso é esse dado. As mudanças acima
atacam a causa (validar produto, não só artefato), não os sintomas.
