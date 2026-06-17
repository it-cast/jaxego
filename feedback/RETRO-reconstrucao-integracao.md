---
escopo: Milestone de reconstrução + integração (MR-0..MR-5, MG-1/MG-2, merge TOTP, CI/deploy)
data: 2026-06-17
auto_generated: false
pending_review: false
---

# Retrospectiva — Reconstrução & Integração do Jaxegô v1.0

> Não é retro de uma phase do autopilot — é a retro do **trabalho de salvamento** que
> veio depois da auditoria: reconstruir o produto navegável, integrar o trabalho paralelo
> de outro dev (TOTP), e levar CI+deploy ao verde. É a parte mais rica de field data.

## Contexto

- **Escopo:** MR-0..MR-5 (esqueleto navegável + auth/me + telas reais) + MG-1/MG-2
  (pacote peso/dimensões; data-tables admin) + merge com branch paralelo + CI/deploy.
- **Duração real:** ~1 sessão longa (multi-dia).
- **Origem:** auditoria `docs/AUDITORIA-FRONTEND-v1.md` mostrou que 14 phases "verdes"
  não navegavam. Esta retro fecha o ciclo.

---

## Planning

### O plano mudou durante a execução?
- [x] Ajustes significativos (tarefas adicionadas/removidas)

**Maior desvio:** o "plano" original (as 14 phases do autopilot) estava **estruturalmente
errado** — otimizou backend em profundidade sem esqueleto navegável. A reconstrução teve
que **inverter o slicing**: primeiro login→cada superfície→tela base (walking skeleton),
depois profundidade. Isso confirma a recomendação M9.

### plan-checker ajudou ou atrapalhou?
- Não rodou nesta fase (trabalho corretivo fora do fluxo de phase). **Esse é o ponto:**
  o GSD não tem um modo "reconstrução/brownfield-fix" — o plan-checker só existe dentro de
  `plan-phase`. Trabalho de salvamento fica sem rede.

---

## Skills

### Skills que puxaram peso real
- [x] `ux-advanced/data-tables-ux` — virou `jx-data-table` com sort/paginação/estados nas
  listas do admin (commit `a4de718`). **Antes citada 10×, aplicada 0×** — só pegou peso aqui.
- [x] `quality/accessibility-pro` + `error-ux-patterns` — login com foco no alerta, estados
  de erro reais (não `alert()`).
- [x] `ui-ux-pro-max` — direção estética ancorada no `prototipo.html` (paleta brand-500,
  payment badge), evitando AI-slop.

### Skills citadas mas que não ajudaram (no autopilot original)
- [x] `senior-quality-bar` — citada em 31 planos; mesmo assim login-loop e componentes
  órfãos passaram. Citação sem checker de produto não pega integração.

### Skills que faltaram
- **`ci-parity` / "rodar o pipeline real local"** — não existe skill que diga "antes de
  push, rode os jobs do `.github/workflows`". Teria evitado os 9 round-trips.
- **`reachability` / "endpoint precisa de UI"** — não existe.
- **`multi-dev-integration`** — branch/PR/rebase; o GSD assume single-stream.

---

## Gates

### Qual gate mais atritou?
- [x] Gate 7 (tests/reconcile) — **por ser fraco, não por atritar.** "lint verde" não
  incluía `ruff format --check`, `ng test`, nem o gate customizado zero-hex do repo.
  Resultado: verde local, vermelho remoto.

### Bypasses aplicados
| Gate | Motivo | Foi certo? |
|------|--------|-----------|
| (nenhum formal) | trabalho corretivo fora do fluxo de phase | n/a |

### Reconcile encontrou divergência?
- A **auditoria manual** (não o reconcile automático) encontrou as 8 divergências do
  postmortem. O reconcile automático tinha fechado todas as phases sem gap — porque é
  grep de existência, não de alcançabilidade.

---

## Qualidade após close

- Fixes de CI/deploy necessários: **9** (ver `METRICS-jaxego-v1.md §3`) — todos de
  paridade-com-pipeline, não de lógica.
- Rollback? Não. 1º deploy quebrou (cd/dir + .env vazio) mas foi guard funcionando.
- **Os fixes deveriam ter sido pegos pelo framework?** Sim — todos. B1/B2 (CI real local).

---

## Três perguntas curtas

**O que funcionou?** Ancorar a reconstrução no `prototipo.html` como contrato e inverter
para walking-skeleton-first deu produto navegável rápido. Merge cuidadoso preservou TOTP do
outro dev + roteamento /me meu.

**O que atrapalhou?** GSD não roda o CI real do projeto → 9 push→vermelho→fix. E não tem
modo "fix/brownfield" com rede (plan-checker só dentro de phase).

**O que faltou?** Gate de alcançabilidade, paridade de CI local, checkpoint UAT por
milestone, e orientação de concorrência multi-dev.

---

## Scores

**Framework effort** (1=invisível, 5=muito overhead): **3** — disciplina boa, mas a rede
estava no lugar errado (validou artefato, não produto/pipeline).
**Framework value** (1=inútil, 5=salvou muito): **4** no planejamento/rastro, **2** na
garantia de produto integrado. Média honesta: **3**.

---

## Ações concretas (máx 3)

1. Implementar **B1/B2** (GSD detecta e roda o CI real do projeto na definition-of-done) — maior ROI.
2. Adicionar **Gate 9 de alcançabilidade** + **checkpoint UAT por milestone** no autopilot.
3. Criar modo **`gsd:fix`/brownfield** com plan-checker e reconcile aplicáveis fora do fluxo de phase.
