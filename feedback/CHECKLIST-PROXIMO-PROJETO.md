# Checklist do próximo projeto — o que incluir para não repetir o Jaxegô

> Acionável. Cada item nasce de uma falha real (F1-F8 / A1-A7). Use como pré-flight
> antes do `/gsd:bootstrap`, durante a execução, e no fechamento de milestone.
> Marque `[ ]` → `[x]` no projeto novo.

---

## 0. Antes do bootstrap (setup que faltou)

- [ ] **`prototipo.html` / wireframes em `projeto/`** registrados como **contrato de UI
      obrigatório** — cada tela do protótipo mapeada para uma phase no roadmap. Tela
      não-mapeada = gap explícito, não some. *(fecha F4, F6-doc)*
- [ ] **Enumerar o CI real do repo** (`.github/workflows/*.yml`): listar todos os jobs e
      seus comandos num `docs/CI-CONTRACT.md`. Esse é o conjunto que "pronto" exige rodar. *(fecha A1/A2/A3)*
- [ ] **ADRs como arquivos** desde o início: toda decisão com ID `ADR-NNN` existe em
      `docs/adrs/ADR-NNN-*.md`, não só linha no `DECISIONS.md`. *(fecha F8)*
- [ ] **Estratégia de branch definida** se houver >1 dev: branch por phase + PR, rebase
      frequente, não acumular dezenas de commits em master local. *(fecha A6)*

## 1. No slicing / roadmap

- [ ] **1ª phase = walking skeleton**: auth → cada superfície → 1 tela base real por
      superfície, antes de qualquer profundidade. *(M9, fecha a raiz)*
- [ ] **`integration_check: true` forçado** em toda phase que toca rota, auth→superfície,
      ou conecta duas superfícies. Roadmapper não baixa para `false` sem ADR. *(fecha F7)*
- [ ] Phases com endpoint+frontend declaram quais **fluxos E2E** fecham (login→ação).

## 2. Durante a execução (definition-of-done por phase)

- [ ] **Rodar o CI real local antes de cada push** (o conjunto de `CI-CONTRACT.md`):
      build · lint · **format --check** · typecheck · **unit tests (karma/jest + pytest)** ·
      **gates customizados** (ex.: zero-hex). Nada de "subconjunto". *(fecha A1/A2/A3)*
- [ ] **Sem forward-reference solta**: "será ligado em T-XX / Phase N", `@Input()` sem
      produtor, "wired later" → vira **task** na phase-alvo ou **TD com urgency_class**.
      Comentário no código não conta. *(fecha F5)*
- [ ] **"Tela pronta" = renderiza dado real OU estados (carga/erro/vazio) de um fluxo
      real** — não placeholder "em breve". Página só-empty-state onde o protótipo pede
      conteúdo = gap. *(fecha F2)*
- [ ] **Sem componente órfão**: todo componente com `.stories.ts` é importado por ao menos
      uma página roteada. *(fecha F3)*
- [ ] **Todo endpoint CRUD tem UI que o consome** (ou tag `api_only: true` justificada). *(fecha F1)*
- [ ] **Spec acompanha código**: mudou assinatura/URL de serviço → atualiza os specs/mocks
      que o referenciam, no mesmo commit. *(fecha A2)*

## 3. Deploy / release-safety

- [ ] **Deploy dispara só após CI verde** (`workflow_run` + `if: conclusion==success`),
      nunca em paralelo com o push. *(fecha A4)*
- [ ] **Pré-flight de env** no deploy: variáveis obrigatórias não-vazias e **sem aspas**
      (o `env_file` do Docker mantém aspas literais → quebra `make_url`). *(fecha A5)*
- [ ] **Robustez de config no app**: normalizar valores vindos de env (strip aspas/espaço)
      + erro claro se ausente. *(fecha A5)*
- [ ] `.env` de produção **gerenciado no servidor** (gitignored, persistente); deploy
      **nunca** o gera nem sobrescreve; só a conexão SSH em GitHub Secrets.

## 4. Fechamento de milestone

- [ ] **Checkpoint UAT humano** sobre o **produto integrado** — não fechar milestone com
      autopilot puro sem alguém navegar o fluxo real. *(M8, fecha a raiz)*
- [ ] **`HUMAN-UAT-BACKLOG.md` reconciliado**: cada item "Pendente ao vivo" / `human_needed`
      do STATE/VERIFICATION está espelhado no backlog. Divergência = não fecha. *(fecha F6)*
- [ ] **Reconcile de alcançabilidade**, não só de existência: rodar o checker endpoint↔UI↔rota.
- [ ] **Métricas de produto** (não só fix-rate): endpoints sem UI, componentes órfãos,
      páginas-stub, fluxos E2E fechados. Ver `METRICS-jaxego-v1.md §2`. *(fecha a cegueira de métrica)*

---

## TL;DR — 5 itens que, sozinhos, teriam salvado o v1.0

1. **Rodar o CI real local antes de push** (§2.1).
2. **Walking skeleton primeiro** (§1.1).
3. **"Tela pronta" ≠ placeholder** + sem órfão + endpoint precisa de UI (§2.3-2.5).
4. **Deploy gated por CI + pré-flight de env** (§3).
5. **UAT humano por milestone** (§4.1).
