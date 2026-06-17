# Métricas de campo — Jaxegô v1.0 (números reais)

> Field data quantitativo extraído do repo real (não estimativa). Serve de baseline
> para o framework: "o GSD ajudou?" deixa de ser opinião. Toda métrica aqui é
> reproduzível com `git log` / `find` no repo na data de corte.
>
> **Data de corte:** 2026-06-17 · **Commits totais:** 281

---

## 1. Volume de entrega

| Métrica | Valor | Fonte |
|---|---:|---|
| Commits totais | 281 | `git rev-list --count HEAD` |
| `feat:` | 138 (49%) | `git log` |
| `docs:` | 85 (30%) | `git log` |
| `test:` | 21 (7%) | `git log` |
| `fix:` | 15 (5,3%) | `git log` |
| `chore:` | 13 | `git log` |
| `ci:` | 3 | `git log` |
| Migrations Alembic | 14 | `alembic/versions/` |
| Arquivos de teste backend | 417 | `find test_*.py` |
| Specs frontend | 41 | `find *.spec.ts` |
| Phases fechadas "verdes" | 14 | `STATE.md` |

**Leitura:** volume altíssimo, taxa de `fix` baixa (5,3%, target do CLAUDE.md §14 é
<15%). Pelo painel de métricas do próprio framework, **o projeto parece saudável.**
Esse é exatamente o problema: as métricas que o GSD coleta **não viram vermelhas**
quando o produto não navega.

---

## 2. A métrica que o GSD NÃO tem (e deveria)

A taxa de `fix` ficou ótima porque **a dívida foi de integração, não de bug pontual**.
Bug de integração não vira `fix:` — vira "feature inteira que nunca foi fiada". Métricas
propostas que teriam acendido vermelho:

| Métrica proposta | Valor real medido (pós-auditoria) | Teria acendido? |
|---|---:|:--:|
| Endpoints CRUD sem UI consumidora | ≥ 3 (areas, kyc-queue, admin lists) | 🔴 |
| Componentes com `.stories.ts` órfãos (sem rota) | 2 (offer-sheet, queue-table) | 🔴 |
| Páginas só-empty-state contadas como tela | ≥ 4 (admin/início, entregador/{entregas,ganhos,perfil}) | 🔴 |
| Fluxos E2E fechados (login→superfície→ação) | 0 de ~5 | 🔴 |
| Itens "Pendente ao vivo" no STATE × no UAT-BACKLOG | dezenas × **0** | 🔴 |
| ADRs referenciados × ADRs existentes em `docs/adrs/` | 6+ × **0** | 🔴 |

> **Conclusão:** o painel de saúde do GSD (fix-rate, plan-revisions, gates verdes) é
> **insensível** ao tipo de dívida que matou o v1.0. Ver `GAPS-MATRIX.md` → métricas novas.

---

## 3. Custo da cascata de CI/deploy (sessão de integração)

Falhas que só apareceram **depois do push** porque nada rodou o CI real localmente:

| # | Vermelho no pipeline | Commit de correção | Categoria |
|---|---|---|---|
| 1 | `cd` em dir inexistente (1º deploy) | `351516b` | deploy |
| 2 | `.env` gerado de secrets (errado) | `0e70bc2` | deploy |
| 3 | `gen_secrets` unicode no print | `f9bbd20` | deploy |
| 4 | I001 import sort | `beba245` | ci/lint |
| 5 | `ruff format --check` (7 arquivos) | `4e631b3` | ci/format |
| 6 | Karma (mock + URL `/catalog`) | `fdae5cf` | ci/test |
| 7 | Zero-hex gate (2 hex TOTP) | `3e4eaa0` | ci/gate |
| 8 | DATABASE_URL aspas/vazio | `1644dff` | deploy |
| 9 | Deploy em paralelo ao CI (ordem) | `5ad9271` | deploy |

**9 round-trips push→vermelho→fix** que um `gsd verify pre-push` rodando o CI real teria
colapsado em ~1-2 locais. Custo: tempo de CI desperdiçado + ruído + 1º deploy quebrado.

- **fix(deploy):** 4 · **fix(ci):** 3 · **style(ci):** 1 · **ci(deploy):** 1
- Cada um teria sido pego **antes** do push se o GSD conhecesse e rodasse os jobs do
  `.github/workflows/ci.yml`. Ver `FIELD-REPORT-02` → B1/B2.

---

## 4. Skills: citadas vs aplicadas (do telemetry do framework)

Snapshot final (`FRAMEWORK-TELEMETRY.md`, 2026-06-11):

| Skill | Citada em N planos | Aplicada de fato? (evidência no código) |
|---|---:|---|
| `fastapi-production-patterns` | 31 | ✅ parcial (endpoints existem, sem N+1 óbvio) |
| `senior-quality-bar` | 31 | ⚠️ citada, mas login-loop/órfãos passaram |
| `data-tables-ux` | 10 | ❌ até a reconstrução (listas eram texto cru) |
| `github-actions-ci` | 3 | ⚠️ CI existe, mas deploy não-gated passou |
| `parallel-orchestration` | 0 | — |

**Padrão confirmado (limitação #6 do FRAMEWORK-STATUS):** citação ≠ aplicação. `data-tables-ux`
citada 10× e só virou `jx-data-table` real **na reconstrução manual** (commit `a4de718`),
não no autopilot original.

---

## 5. Targets do CLAUDE.md §14 — placar honesto

| Target | Meta | Real | Status |
|---|---|---|---|
| Taxa de fix commits | < 15% | 5,3% | ✅ (mas ver §2 — métrica cega) |
| Bug→detecção | < 1 dia | **semanas** (só na auditoria) | 🔴 |
| Divergência artefato↔código pós-reconcile | zero | ≥ 8 falhas (postmortem) | 🔴 |
| Skills citadas por phase com código | ≥ 3 | 25-31 | ✅ (citação) / 🔴 (aplicação) |
| Gates bypassados/sprint | 0-1 | 0 | ✅ |

**O placar "verde" em 3 de 5 é o retrato do problema:** os targets que o framework
mede são os que ele acerta; os que importavam para o produto (bug→detecção,
divergência real) não eram medidos antes desta auditoria.
