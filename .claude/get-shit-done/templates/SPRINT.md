---
# Front-matter YAML — consumido pelo plan-checker
sprint_id: sprint-NN-<slug>
milestone: M<N>-<slug>
slicing_strategy: vertical_value | admin_first  # deve bater com config.json
duration_days_planned: 5  # 3-10 úteis
has_ui: true | false
has_forms: true | false
has_error_states: true | false
has_non_trivial_motion: true | false
touches_shared_components: true | false
locale: pt-BR  # ou outro; alimenta skills br/
---

# SPRINT-NN — {Nome curto do sprint}

> **Instruções:** preencha todas as seções antes do kickoff. Plan-checker valida este arquivo antes de permitir execução. Não remova seções — se uma não aplica, preencha com "N/A — {motivo 1 linha}".

## Narrativa (1 parágrafo)

Quem é a pessoa cuja vida fica melhor ao fim deste sprint, e o que ela consegue fazer que não conseguia antes? Em prosa, sem jargão técnico. Exemplo:

> "Ao fim deste sprint, o prestador consegue criar um anúncio com título, descrição, categoria e preço, vê seu anúncio listado na busca do cliente, e pode editar ou remover o anúncio próprio. Cliente anônimo consegue buscar e ver detalhes. Nenhum outro prestador pode editar anúncio alheio."

## Definition of Done (testável por humano em 30 min)

Lista de 3-6 verificações que um humano executa abrindo o app/API. Cada uma binária (passa / não passa). Linguagem de usuário final, não de implementação.

- [ ] Prestador faz login, clica "Novo anúncio", preenche formulário, vê mensagem de confirmação e o anúncio aparece em "Meus anúncios"
- [ ] Cliente anônimo abre a home e vê a lista de anúncios ativos
- [ ] Cliente clica num anúncio e vê os detalhes, incluindo botão "Entrar em contato" (não precisa funcionar ainda — só aparecer)
- [ ] Prestador A não consegue editar anúncio do prestador B (tenta via URL direta, recebe 403 + mensagem em português)
- [ ] Anúncio em estado "rascunho" não aparece na busca pública
- [ ] Campos obrigatórios validam no front E no back (tentar pular valida com mensagem específica)

## Visual Contract

> Obrigatória se `has_ui: true`. Tokens citados devem existir em `docs/identidade-visual/tokens.json`.

### Cores
- `color.brand.500` — botão primário (Criar anúncio, Salvar)
- `color.text.primary` — títulos e corpo
- `color.text.secondary` — labels, metadados
- `color.surface.default` — fundo de card de anúncio
- `color.surface.elevated` — hover state de card
- `color.border.default` — border de card + input
- `color.semantic.danger` — mensagens de erro inline + borda de input inválido

### Espaçamentos
- `space.md` (16px) — padding interno de card, gap de form fields
- `space.lg` (24px) — gap entre seções da página
- `space.sm` (8px) — gap entre label e input

### Tipografia
- `typography.size.xl` + `typography.weight.semibold` — título da tela ("Meus anúncios", "Novo anúncio")
- `typography.size.lg` + `typography.weight.medium` — título de card
- `typography.size.md` — corpo
- `typography.size.sm` — metadados (categoria, data)

### Raios e sombras
- `radius.md` — cards e botões
- `radius.sm` — inputs

### Motion
- `motion.duration.fast` + `motion.easing.out` — hover de card
- `motion.duration.normal` + `motion.easing.out` — toast de sucesso (entrada)

### Componentes novos
- `app-listing-card` — feature-level, em `features/listings/components/` (uso único no momento; promove para `shared/` se Sprint 3 confirmar reuso)
- `app-empty-state` — em `shared/ui/` (vai ser usado em múltiplas listagens). Tem `.stories.ts` + `.a11y.spec.ts`.

### Componentes reusados
- `app-button` (shared) — variants primary, ghost
- `app-input` (shared) — com slot de error
- `app-card` (shared)

## UX Skills Applied

> Lista concreta do que cada skill obrigatória produz neste sprint. Não é declaração abstrata — é output específico.

### `product/component-library-governance`
- Decisão de `app-empty-state` em `shared/` justificada (2+ consumidores previstos: listagem vazia de anúncios + listagem vazia de mensagens)
- `app-listing-card` em `feature/` por ter apenas 1 consumidor — monitorar em sprint 3

### `quality/accessibility-pro`
- Todos os inputs têm `<label for>` associado (não placeholder-as-label)
- Mensagens de erro com `aria-describedby` apontando para o campo
- Botões só-ícone têm `aria-label` descritivo ("Remover anúncio #{title}")
- Contraste validado com axe: brand.500 em surface.default = 4.5:1 mínimo
- Teclado: Tab atravessa form na ordem lógica; Enter submete; Esc cancela modal
- `jest-axe` em testes de componente novo (`app-empty-state`)

### `br/ux-copywriting-ptbr`
- CTAs: "Criar anúncio" (não "Submeter"), "Salvar alterações" (não "OK"), "Remover anúncio" (não "Deletar")
- Erros: "Título é obrigatório" (não "Campo inválido"), "Preço deve ser maior que zero"
- Empty state: "Nenhum anúncio ainda. Crie o primeiro para aparecer na busca." + CTA [Criar anúncio]
- Confirmação destrutiva: "Remover anúncio '{title}'? Essa ação não pode ser desfeita." [Remover] [Cancelar]
- Sucesso: "Anúncio criado" (não "Anúncio criado com sucesso!")

### `quality/error-ux-patterns`
- Error codes novos: `VALIDATION_LISTING_TITLE_REQUIRED`, `VALIDATION_LISTING_PRICE_INVALID`, `RESOURCE_LISTING_NOT_OWNED`
- Toast vs modal: validation = inline nos campos; 403 = modal explicativo; offline = banner persistente
- Retry policy: POST /listings tem Idempotency-Key (previne double-create em retry de timeout)

### `product/micro-animations-delight`
- Toast de sucesso: fade+translateY(20px→0) com `motion.duration.normal` + easing out
- Hover de card: transform scale(1.02) + shadow aumenta com `motion.duration.fast`
- `prefers-reduced-motion` desabilita transform, mantém mudança de cor

### `product/visual-regression-testing`
- `app-empty-state.stories.ts` com 2 variants (padrão e com CTA custom)
- Chromatic captura baseline; próximo sprint compara diff

## Tasks

Lista ordenada. `- [ ]` pendente, `- [~]` em andamento, `- [x]` completa, `- [!]` bloqueada.

- [ ] T1: Migration `listings` (id, owner_id, title, description, price_cents, category_id, status, created_at, updated_at)
- [ ] T2: Schema Pydantic `CreateListingBody`, `UpdateListingBody`, `ListingResponse`
- [ ] T3: Endpoints `POST /api/v1/listings`, `GET /api/v1/listings`, `GET /api/v1/listings/{id}`, `PATCH /api/v1/listings/{id}`, `DELETE /api/v1/listings/{id}` com `response_model`
- [ ] T4: Regra de permissão: só owner edita/remove. Retorna 403 + code `RESOURCE_LISTING_NOT_OWNED`.
- [ ] T5: Componente `app-empty-state` (shared) + `.stories.ts` + teste a11y
- [ ] T6: Página `features/listings/pages/my-listings` (lista do prestador logado)
- [ ] T7: Página `features/listings/pages/listings-search` (busca pública)
- [ ] T8: Página `features/listings/pages/listing-detail` (detalhe público)
- [ ] T9: Página `features/listings/pages/listing-form` (criar/editar)
- [ ] T10: Logs estruturados nos endpoints (request_id, listing_id, action); zero PII
- [ ] T11: Testes: 5 contract tests (um por endpoint), 3 integration tests (criar/editar/permissão), 2 e2e (criar como prestador, buscar como cliente)

## Skills Consultadas

Skills obrigatórias marcadas (🔒) aplicáveis ao sprint:

- 🔒 `product/api-design-contracts` — endpoints novos
- 🔒 `product/component-library-governance` — componentes UI
- 🔒 `quality/accessibility-pro` — sprint com UI
- 🔒 `quality/error-ux-patterns` — forms + error states
- 🔒 `quality/observability-production` — endpoints novos
- 🔒 `br/ux-copywriting-ptbr` — UI em pt-BR
- 🔒 `product/visual-regression-testing` — toca componente shared (app-empty-state)
- 🔒 `product/micro-animations-delight` — transições em toast e hover de card
- `br/brazilian-forms` — validação CPF/CNPJ (não aplicável — sprint não tem campos BR)

## Skills Dispensadas

- `mobile/offline-first` — N/A, web-only neste sprint
- `mobile/push-notifications-architecture` — N/A
- `quality/i18n-ready-architecture` — locale único pt-BR; arquitetura i18n já estabelecida no Sprint 0
- `quality/performance-web-vitals` — aplicável mas coberto por budgets globais de CI, não precisa ação extra neste sprint
- `br/lgpd-compliance` — não introduz coleta de PII nova além do já mapeado

## Dependências

- Sprint 0 deve estar fechado (auth + design tokens + componentes primitivos)
- Tabela `users` já existe com `id` (owner_id fk)
- Tabela `categories` já existe (category_id fk) — senão, sprint fica bloqueado

## Riscos & Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Query de busca ficar lenta com muitos anúncios | Média | Médio | Índice em `(status, created_at desc)` desde a migration; paginação cursor-based |
| Designer indisponível para revisar `app-empty-state` | Baixa | Baixo | Usa tokens existentes; revisão visual via Chromatic PR |

## Gates aplicáveis

Gate 2 (UI-SPEC via este SPRINT.md), Gate 3 (skills citadas), Gate 4 (observability), Gate 5 (integration), Gate 6 (reconcile pós-execução), Gate 7 (tests/lint).

## Overrides

Nenhum previsto. Se surgir necessidade: `--skip-gate-N --reason "justificativa específica"`.

---

## Pós-sprint (preenchido ao fechar)

### Definition of Done cumprida?
- [ ] Todas as verificações da DoD executadas por humano
- [ ] Zero falhas em produção/staging nas 72h pós-merge

### Sprint fechou em prazo?
- Planejado: 5 dias
- Real: <FILL>

### O que mudou do plano original?
<FILL — 1 parágrafo; se nada mudou, "plano seguido integralmente">

### Retrospectiva
Após fechar: gerar retrospectiva via `bin/collect-metrics.sh sprint-NN-<slug>` e preencher `.planning/retros/sprint-NN-<slug>.md`.
