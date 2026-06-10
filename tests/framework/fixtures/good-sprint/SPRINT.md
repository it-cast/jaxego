---
sprint_id: sprint-01-create-listing
milestone: M2-listings
slicing_strategy: vertical_value
duration_days_planned: 5
has_ui: true
has_forms: true
has_error_states: true
has_non_trivial_motion: false
touches_shared_components: true
locale: pt-BR
---

# SPRINT-01 — Prestador cria anúncio

## Narrativa

Ao fim deste sprint, o prestador consegue criar um anúncio e vê-lo na sua lista pessoal. Cliente anônimo consegue buscar e ver anúncios ativos.

## Definition of Done

- [ ] Prestador faz login e cria anúncio
- [ ] Anúncio aparece na lista do próprio prestador
- [ ] Cliente anônimo busca e vê anúncio
- [ ] Prestador A não edita anúncio do prestador B

## Visual Contract

### Cores
- `color.brand.500` — botão primário
- `color.text.primary` — títulos
- `color.surface.default` — fundo de card
- `color.border.default` — border de input
- `color.semantic.danger` — erro inline

### Espaçamentos
- `space.md` — padding de card
- `space.lg` — gap entre seções
- `space.sm` — gap label/input

### Tipografia
- `typography.size.lg` + `typography.weight.semibold` — título
- `typography.size.md` — corpo

### Raios
- `radius.md` — card e botão

### Componentes novos
- `app-empty-state` em `shared/` (2+ consumidores previstos)

## UX Skills Applied

### `product/component-library-governance`
- `app-empty-state` em `shared/` por regra dos 3 (listagem de anúncios + mensagens)

### `quality/accessibility-pro`
- Labels associados via `for`; aria-describedby em erros; contraste validado

### `br/ux-copywriting-ptbr`
- CTAs: "Criar anúncio", "Salvar"; empty state: "Nenhum anúncio ainda..."

### `quality/error-ux-patterns`
- Codes: VALIDATION_LISTING_TITLE_REQUIRED; inline errors nos campos

## Tasks

- [ ] T1: Migration listings
- [ ] T2: Endpoints POST/GET listings
- [ ] T3: Página criar anúncio
- [ ] T4: Componente shared/app-empty-state
- [ ] T5: Testes de contract + e2e

## Skills Consultadas

- 🔒 `product/api-design-contracts`
- 🔒 `product/component-library-governance`
- 🔒 `quality/accessibility-pro`
- 🔒 `quality/error-ux-patterns`
- 🔒 `quality/observability-production`
- 🔒 `br/ux-copywriting-ptbr`
- 🔒 `product/visual-regression-testing`

## Skills Dispensadas

- `mobile/offline-first` — N/A web-only
- `mobile/push-notifications-architecture` — N/A
- `product/micro-animations-delight` — sprint sem transições não-triviais
- `br/brazilian-forms` — sprint sem campos CPF/CNPJ/CEP
- `br/lgpd-compliance` — sem coleta de PII nova

## Dependências

- Sprint 0 (auth + design tokens) fechado
