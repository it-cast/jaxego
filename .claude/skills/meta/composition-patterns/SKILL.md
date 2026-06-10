---
name: meta:composition-patterns
description: "React/Vue/Svelte component composition patterns que escalam. Evita boolean prop proliferation (isCompact, showHeader, isRounded etc) usando compound components, context providers, state lifting e variant components. Use quando: refatorar component com 5+ boolean props; projetar API de componente reutilizável; criar component library; revisar arquitetura de design system. Não confundir com styling/visual — esta skill é sobre **API shape** e **composability**."
priority: high
tier: 2
phase_types:
  - design-system
  - component-library
  - refactor-ui
  - frontend-architecture
keywords:
  pt-BR:
    - composição de componentes
    - boolean props demais
    - props proliferation
    - compound components
    - design de componente
    - arquitetura de componente
    - reutilizar componente
    - state lifting
    - variant components
    - children vs render props
  en:
    - composition patterns
    - compound components
    - boolean prop proliferation
    - state lifting
    - context providers
    - explicit variants
    - render props vs children
    - component architecture
    - component library design
flags:
  has_ui: true
  has_design_system: true
references:
  - source: vercel-labs/agent-skills
    path: skills/composition-patterns
    license: MIT
    last_updated: 2026-01
---

# Composition Patterns — arquitetura de componentes que escala

Foco em **API shape** de componentes (props, children, context), não em estilo visual.

## Quando aplicar

- Componente tem 5+ booleans (`isCompact`, `showHeader`, `isRounded`, `hasBorder`, `isHighlighted`, `withFooter`...)
- API do componente está virando "switch statement gigante"
- Difícil testar variações sem matriz cartesiana de booleans
- Build de design system / component library reutilizável

## Anti-pattern principal: Boolean prop proliferation

```tsx
// ❌ ANTI-PATTERN — sintoma de design quebrado
<Card
  isCompact
  showHeader={false}
  isRounded
  hasBorder={false}
  isHighlighted
  withFooter
  variant="primary"
  size="md"
/>

// ✅ Composition
<Card variant="primary" size="md">
  <Card.Body>...</Card.Body>
  <Card.Footer>...</Card.Footer>
</Card>
```

## 4 categorias de regras (priority order)

### 1. Component architecture (CRITICAL)

- **architecture-avoid-boolean-props**: NÃO adicionar boolean prop pra customizar comportamento. Use composição.
- **architecture-compound-components**: Componentes complexos = parent + children que compartilham contexto. Padrão: `<Select>`, `<Select.Trigger>`, `<Select.Content>` (Radix UI).
- **architecture-explicit-variants**: Em vez de `<Button isPrimary isSecondary />`, criar `<PrimaryButton />` e `<SecondaryButton />` (ou `variant="primary" | "secondary"`).
- **architecture-children-over-render-props**: Preferir `children` para composição em vez de `renderHeader`, `renderFooter` etc.

### 2. State management (HIGH)

- **state-lift-state**: Move state para provider component quando dois siblings precisam compartilhar.
- **state-context-interface**: Define interface genérica `{ state, actions, meta }` para dependency injection.
- **state-controlled-uncontrolled**: Suportar AMBOS via prop opcional `value` + `defaultValue`. Não forçar.

### 3. Implementation patterns (HIGH)

- **patterns-compound-with-context**: Compound components compartilham state via React Context interno (não via prop drilling).
- **patterns-asChild-radix**: Para máxima flexibilidade, expor `asChild` prop (Radix pattern) que passa props para o child em vez de criar wrapper.
- **patterns-forward-ref**: Sempre `forwardRef` em componentes baixos (Button, Input) para que consumidores possam pegar ref.

### 4. React 19 APIs (MEDIUM, para projetos novos)

- **react19-use-hook**: Use `use()` para promises e contexts em casos onde hooks tradicionais geram boilerplate.
- **react19-actions**: Server actions + `useActionState` simplificam forms — não recriar manual.
- **react19-form-status**: `useFormStatus` em vez de prop drilling de `isSubmitting`.

## Quando NÃO aplicar

- Componente tem 1-2 booleans simples e não vai escalar — over-engineering. Composition vale a partir de 3-4 modos distintos.
- Component genuinamente atomic (Icon, Spinner) — booleans simples ok.
- Prototipação rápida — refatorar depois.

## Checklist de revisão

Antes de aprovar PR de novo componente / refactor:

- [ ] Boolean count < 3 ou justificado
- [ ] Variantes mutuamente exclusivas viraram `variant="..."` enum
- [ ] Composição via children/slots quando faz sentido
- [ ] Context interno em vez de prop drilling se compound
- [ ] forwardRef em componentes folha
- [ ] Storybook/test cobre principais combinações sem matriz N×M

## Integração com framework GSD

- **Use junto com**: `quality/component-library-governance` (regras de versionamento/changelog), `meta/refactoring-ui` (visual hierarchy)
- **NÃO use junto com**: `quality/color-system` ou `ux-advanced/loading-states` na mesma decisão — escopos disjuntos
- **Antes de citar no PLAN**: rodar `grep -r "boolean.*=.*true" --include="*.tsx"` no código existente para detectar candidatos a refactor

## Source

Adaptado de [vercel-labs/agent-skills/composition-patterns](https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns) (MIT, 19k stars, mantido por Vercel Engineering).

Decisão de adoção: skill foi **revisada manualmente** — sem prompt injection detectada, autoria vetted, padrão estável (Radix/Headless UI usam há 3+ anos), aplicabilidade direta a stack React/Angular/Vue/Svelte do framework.
