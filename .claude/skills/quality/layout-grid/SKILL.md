---
name: layout-grid
category: quality
description: Grid responsivo com colunas, gutters e margins. Define comportamento por breakpoint.
---

# Layout Grid — Grid de Layout

> Grid não é "Bootstrap 12 cols". É contrato sobre como conteúdo se comporta em qualquer largura.

## Quando esta skill é obrigatória

- `/gsd-ui-phase` em projeto web (não-mobile-only)
- Adição de breakpoint novo
- Refactor de layout

## Estrutura

### 1. Breakpoints

```json
{
  "breakpoints": {
    "xs": "0",       /* mobile portrait */
    "sm": "640px",   /* mobile landscape, small tablets */
    "md": "768px",   /* tablet portrait */
    "lg": "1024px",  /* tablet landscape, small desktop */
    "xl": "1280px",  /* desktop */
    "2xl": "1536px"  /* large desktop */
  }
}
```

**Regra:** mobile-first sempre. Estilos default = mobile, media queries adicionam para telas maiores.

### 2. Container max-width

```json
{
  "container": {
    "sm":  "640px",
    "md":  "768px",
    "lg":  "1024px",
    "xl":  "1280px",
    "2xl": "1536px"
  }
}
```

Container nunca cresce além de 1536px (legibilidade caí).

### 3. Grid columns

```
Mobile  (xs, sm): 4 cols
Tablet  (md, lg): 8 cols
Desktop (xl, 2xl): 12 cols
```

### 4. Gutters (espaço entre colunas)

```json
{
  "grid": {
    "gutter": {
      "xs": "16px",   /* mobile */
      "md": "24px",   /* tablet */
      "lg": "32px"    /* desktop */
    }
  }
}
```

### 5. Container padding (margin lateral)

```json
{
  "container": {
    "padding": {
      "xs": "16px",
      "md": "32px",
      "lg": "64px"
    }
  }
}
```

## CSS Implementation

### Container

```css
.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--container-padding-xs);
  padding-right: var(--container-padding-xs);
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
    padding-left: var(--container-padding-md);
    padding-right: var(--container-padding-md);
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
    padding-left: var(--container-padding-lg);
    padding-right: var(--container-padding-lg);
  }
}
```

### Grid (CSS Grid moderno)

```css
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--grid-gutter-xs);
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(8, 1fr);
    gap: var(--grid-gutter-md);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(12, 1fr);
    gap: var(--grid-gutter-lg);
  }
}
```

## Padrões de layout comuns

### Stack vertical (mobile, lista)

```css
.stack { display: flex; flex-direction: column; gap: var(--space-md); }
```

### Sidebar + content (admin)

```css
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
}

@media (max-width: 1024px) {
  .layout { grid-template-columns: 1fr; } /* sidebar vira drawer */
}
```

### Hero (landing page)

```css
.hero {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: var(--space-xl);
}
```

### Cards grid

```css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-lg);
}
```

(`auto-fill` é mágico — sem media queries.)

## Anti-patterns

❌ 12 cols em mobile (espremem)
❌ Container sem max-width (linhas com 200+ caracteres)
❌ Gutter igual em todos breakpoints
❌ Floats e clearfix (legacy, use Grid)
❌ Bootstrap genérico em vez de tokens próprios

## Integração

- Depende de: `quality/spacing-system`, `quality/design-token-architecture`
- Complementa: `ux-advanced/responsive-breakpoint-strategy`
