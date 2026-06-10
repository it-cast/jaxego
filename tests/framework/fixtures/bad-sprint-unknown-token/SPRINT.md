---
sprint_id: sprint-03-unknown-token
milestone: M2-listings
slicing_strategy: vertical_value
duration_days_planned: 4
has_ui: true
has_forms: false
has_error_states: false
has_non_trivial_motion: false
touches_shared_components: false
locale: pt-BR
---

# SPRINT-03 — Cita tokens que não existem no tokens.json

## Narrativa

Tela de detalhe do anúncio.

## Definition of Done

- [ ] Cliente abre detalhe de anúncio e vê informações
- [ ] Botão "Entrar em contato" aparece (não precisa funcionar)

## Visual Contract

### Cores
- `color.brand.500` — botão primário (este EXISTE no tokens.json)
- `color.unicorn.rainbow` — cor inventada que NÃO existe
- `color.accent.999` — outra inventada

### Espaçamentos
- `space.galactic` — espaçamento inventado

### Tipografia
- `typography.size.md` — corpo (existe)

## UX Skills Applied

### `product/component-library-governance`
- Nada novo

### `quality/accessibility-pro`
- Contraste validado

### `br/ux-copywriting-ptbr`
- "Entrar em contato" como CTA

## Tasks

- [ ] T1: Página detalhe
- [ ] T2: Rota
- [ ] T3: Testes

## Skills Consultadas

- 🔒 `product/component-library-governance`
- 🔒 `quality/accessibility-pro`
- 🔒 `br/ux-copywriting-ptbr`

## Skills Dispensadas

- `quality/error-ux-patterns` — sprint sem forms nem error states
- `product/micro-animations-delight` — sem motion não-trivial
