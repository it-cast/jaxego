---
name: spacing-system
category: quality
description: Sistema completo de espaçamento — base unit, escala finita, t-shirt sizes, padding por componente, gutters por breakpoint, regras contextuais para hierarquia visual. Inclui snippets prontos CSS, Tailwind config, validação via stylelint, anti-patterns frequentes e como usar em forms, listas, cards. Resolve "espaços random" e cria ritmo visual sólido.
---

# Spacing System — Sistema de Espaçamento

> Espaçamento ad-hoc é a #1 causa de UI parecer "amadora". Sistema = todo espaço derivado de uma base unit, criando ritmo visual.

Esta skill define escala canônica, regras contextuais, e como aplicar em formulários, cards, listas e layouts.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-ui-phase` em projeto novo (primeira phase com UI) | Fundação do design system |
| Refactor de design system existente | Migrar de margens random |
| Adição de componente novo | Garantir consistência |
| Antes de definir typography-scale | Espaçamento e tipografia se relacionam |

## 2. Quando NÃO usar

- Phase backend
- Phase de infra
- Phase já com sistema estabelecido (apenas seguir)

---

## 3. Princípios fundamentais

### 3.1 Base unit = 4px ou 8px

Todos os espaçamentos são múltiplos da base.

```
Base 4px:
4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128

Base 8px (mais simples, recomendado para web):
8, 16, 24, 32, 48, 64, 96
```

**Por quê base unit?**
- Telas Retina/HiDPI rendem múltiplos de 4 sem fractional pixels
- Reduz decisões mentais (não precisa pensar "12 ou 13?")
- Cria ritmo visual previsível
- Facilita manutenção (1 mudança altera todo o sistema)

**Qual escolher?**
- **Base 4px** — mais granular, recomendado para apps complexos
- **Base 8px** — mais simples, recomendado para landing pages e SaaS comum

### 3.2 Escala finita (não use qualquer valor)

```json
{
  "space": {
    "0":   "0",
    "px":  "1px",
    "0.5": "2px",
    "1":   "4px",
    "2":   "8px",
    "3":   "12px",
    "4":   "16px",
    "5":   "20px",
    "6":   "24px",
    "8":   "32px",
    "10":  "40px",
    "12":  "48px",
    "16":  "64px",
    "20":  "80px",
    "24":  "96px",
    "32":  "128px"
  }
}
```

10-15 tokens. Mais que isso = inflação (qual a diferença entre 18px e 19px?).

### 3.3 T-shirt sizes para semântica

Para componentes, t-shirt sizes facilitam:

```json
{
  "space": {
    "xs":  "4px",
    "sm":  "8px",
    "md":  "16px",
    "lg":  "24px",
    "xl":  "32px",
    "2xl": "48px",
    "3xl": "64px",
    "4xl": "96px"
  }
}
```

**Quando usar t-shirt vs numérico:**
- **T-shirt** para componentes (`button-padding: md`)
- **Numérico** para layout específico (`gap: 6`)

---

## 4. Regras contextuais (onde aplicar qual valor)

### 4.1 Espaçamento entre elementos relacionados

**Princípio (Lei de Proximidade):** elementos próximos = relacionados, distantes = separados.

```css
/* ✅ Label e input pertencem juntos */
.field {
  margin-bottom: var(--space-4); /* 16px entre fields */
}
.field label {
  margin-bottom: var(--space-2); /* 8px entre label e input */
}

/* ❌ ERRADO — espaços iguais não comunicam relação */
.field, .field label {
  margin: 16px 0;
}
```

### 4.2 Espaçamento entre seções

Maior que entre elementos.

```css
.section {
  padding: var(--space-12) 0; /* 48px top/bottom */
}

.subsection {
  margin-bottom: var(--space-6); /* 24px entre subseções */
}

.subsection-item {
  margin-bottom: var(--space-2); /* 8px entre items */
}
```

### 4.3 Container padding por breakpoint

```css
.container {
  padding-left: var(--space-4);   /* 16px mobile */
  padding-right: var(--space-4);
}

@media (min-width: 768px) {
  .container {
    padding-left: var(--space-6); /* 24px tablet */
    padding-right: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .container {
    padding-left: var(--space-8); /* 32px desktop */
    padding-right: var(--space-8);
  }
}
```

### 4.4 Inset para componentes (padding interno)

```json
{
  "button-padding": {
    "small":  "{space.2} {space.3}",   // 8px 12px
    "medium": "{space.3} {space.4}",   // 12px 16px
    "large":  "{space.4} {space.6}"    // 16px 24px
  },
  "card-padding": {
    "compact": "{space.4}",            // 16px
    "default": "{space.6}",            // 24px
    "spacious": "{space.8}"            // 32px
  },
  "input-padding": {
    "small":  "{space.2} {space.3}",   // 8px 12px
    "medium": "{space.3} {space.4}",   // 12px 16px
    "large":  "{space.4} {space.5}"    // 16px 20px
  }
}
```

### 4.5 Gap entre items em listas/grids

```css
.card-list {
  display: grid;
  gap: var(--space-4); /* 16px entre cards */
}

.button-group {
  display: flex;
  gap: var(--space-2); /* 8px entre botões */
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-8); /* 32px entre features */
}
```

### 4.6 Padding por densidade

```yaml
density:
  compact:    # dashboards, tabelas densas
    container_padding: "{space.4}"  # 16px
    card_padding:      "{space.4}"  # 16px
    section_gap:       "{space.6}"  # 24px

  balanced:   # SaaS típico (default)
    container_padding: "{space.6}"  # 24px
    card_padding:      "{space.6}"  # 24px
    section_gap:       "{space.12}" # 48px

  generous:   # landing pages, premium
    container_padding: "{space.8}"  # 32px
    card_padding:      "{space.8}"  # 32px
    section_gap:       "{space.20}" # 80px
```

---

## 5. Implementação completa

### 5.1 tokens.json

```json
{
  "_meta": { "version": "1.0", "category": "spacing" },
  "space": {
    "0":   "0",
    "px":  "1px",
    "0.5": "2px",
    "1":   "4px",
    "2":   "8px",
    "3":   "12px",
    "4":   "16px",
    "5":   "20px",
    "6":   "24px",
    "8":   "32px",
    "10":  "40px",
    "12":  "48px",
    "16":  "64px",
    "20":  "80px",
    "24":  "96px",
    "32":  "128px"
  },
  "_semantic": {
    "space": {
      "xs":  "{space.1}",
      "sm":  "{space.2}",
      "md":  "{space.4}",
      "lg":  "{space.6}",
      "xl":  "{space.8}",
      "2xl": "{space.12}",
      "3xl": "{space.16}",
      "4xl": "{space.24}"
    }
  }
}
```

### 5.2 CSS variables

```css
:root {
  /* Primitivos */
  --space-0:   0;
  --space-px:  1px;
  --space-0-5: 2px;
  --space-1:   4px;
  --space-2:   8px;
  --space-3:   12px;
  --space-4:   16px;
  --space-5:   20px;
  --space-6:   24px;
  --space-8:   32px;
  --space-10:  40px;
  --space-12:  48px;
  --space-16:  64px;
  --space-20:  80px;
  --space-24:  96px;
  --space-32:  128px;

  /* Semânticos t-shirt */
  --space-xs:  var(--space-1);
  --space-sm:  var(--space-2);
  --space-md:  var(--space-4);
  --space-lg:  var(--space-6);
  --space-xl:  var(--space-8);
  --space-2xl: var(--space-12);
  --space-3xl: var(--space-16);
  --space-4xl: var(--space-24);
}
```

### 5.3 Tailwind config

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    spacing: {
      0: '0',
      px: '1px',
      0.5: '2px',
      1: '4px',
      2: '8px',
      3: '12px',
      4: '16px',
      5: '20px',
      6: '24px',
      8: '32px',
      10: '40px',
      12: '48px',
      16: '64px',
      20: '80px',
      24: '96px',
      32: '128px'
    }
  }
};
```

### 5.4 Stylelint para validação

```json
{
  "rules": {
    "declaration-property-value-allowed-list": {
      "/^(margin|padding|gap|top|right|bottom|left)/": [
        "/^var\\(--space-/",
        "0",
        "auto",
        "inherit",
        "unset"
      ]
    }
  }
}
```

Bloqueia `margin: 23px` (random) e força `margin: var(--space-6)`.

---

## 6. Casos práticos por contexto

### 6.1 Form completo

```css
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4); /* 16px entre fields */
}

.form-section {
  margin-bottom: var(--space-8); /* 32px entre seções de form */
}

.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2); /* 8px label-input-helper */
}

.field-label {
  font-size: 14px;
  font-weight: 500;
}

.field-input {
  padding: var(--space-3) var(--space-4); /* 12px 16px */
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
}

.field-helper {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: var(--space-1); /* 4px - mais próximo */
}

.field-error {
  font-size: 13px;
  color: var(--color-feedback-danger);
  margin-top: var(--space-1);
}

.form-actions {
  display: flex;
  gap: var(--space-3); /* 12px entre botões */
  margin-top: var(--space-8); /* 32px do form */
}
```

### 6.2 Card padrão

```css
.card {
  padding: var(--space-6); /* 24px - balanced */
  border: 1px solid var(--color-border-default);
  border-radius: 12px;
  background: var(--color-surface-default);
}

.card-header {
  margin-bottom: var(--space-4); /* 16px */
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: var(--space-1); /* 4px - próximo do subtitle */
}

.card-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.card-body {
  margin-bottom: var(--space-4);
}

.card-footer {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-default);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
```

### 6.3 Lista de items

```css
.list {
  display: flex;
  flex-direction: column;
  gap: 0; /* sem gap - separar com border */
}

.list-item {
  padding: var(--space-4) var(--space-6); /* 16px 24px */
  border-bottom: 1px solid var(--color-border-default);
}

.list-item:last-child {
  border-bottom: none;
}

.list-item-icon {
  margin-right: var(--space-3); /* 12px */
}

.list-item-content {
  flex: 1;
  min-width: 0;
}

.list-item-actions {
  margin-left: var(--space-3);
  display: flex;
  gap: var(--space-1); /* 4px - botões pequenos juntos */
}
```

### 6.4 Hero section (landing)

```css
.hero {
  padding: var(--space-24) var(--space-6); /* 96px vertical, 24px horizontal */
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.hero-eyebrow {
  margin-bottom: var(--space-4);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.hero-title {
  margin-bottom: var(--space-4);
  font-size: 48px;
  font-weight: 700;
}

.hero-subtitle {
  margin-bottom: var(--space-8); /* 32px - separar do CTA */
  font-size: 20px;
  color: var(--color-text-secondary);
  max-width: 640px;
}

.hero-cta {
  display: flex;
  gap: var(--space-3);
}
```

### 6.5 Dashboard layout (densidade compact)

```css
.dashboard {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 0;
  height: 100vh;
}

.dashboard-sidebar {
  padding: var(--space-4); /* 16px - compact */
  border-right: 1px solid var(--color-border-default);
}

.dashboard-main {
  padding: var(--space-6); /* 24px */
  overflow-y: auto;
}

.dashboard-section {
  margin-bottom: var(--space-8); /* 32px - menos que SaaS marketing */
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4); /* 16px - cards mais juntos em dashboard */
}

.dashboard-kpi {
  padding: var(--space-4); /* compact */
}
```

---

## 7. Anti-patterns com correção

### Anti-pattern 1: Espaçamentos arbitrários

```css
/* ❌ ERRADO */
margin: 7px;
padding: 13px;
gap: 17px;

/* ✅ CORRETO */
margin: var(--space-2);   /* 8px */
padding: var(--space-3);  /* 12px */
gap: var(--space-4);      /* 16px */
```

### Anti-pattern 2: Margin-top + margin-bottom em vez de gap

```css
/* ❌ ERRADO — colapsa, problemas */
.item { margin-top: 16px; margin-bottom: 16px; }

/* ✅ CORRETO — usar gap em flex/grid */
.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.item { /* sem margin */ }
```

### Anti-pattern 3: Mistura de unidades

```css
/* ❌ ERRADO */
margin: 16px 1rem 0.5em 8px;

/* ✅ CORRETO — uma unidade só */
margin: var(--space-4) var(--space-4) var(--space-2) var(--space-2);
```

### Anti-pattern 4: Espaços iguais entre tudo

```css
/* ❌ ERRADO — não comunica hierarquia */
.section, .subsection, .item { margin-bottom: 16px; }

/* ✅ CORRETO — hierarquia */
.section    { margin-bottom: var(--space-12); } /* 48px - maior */
.subsection { margin-bottom: var(--space-6); }  /* 24px - médio */
.item       { margin-bottom: var(--space-2); }  /* 8px - pequeno */
```

### Anti-pattern 5: Inflação de tokens

```json
// ❌ ERRADO
{
  "space-1": "1px",
  "space-2": "2px",
  "space-3": "3px",
  "space-4": "4px",
  "space-5": "5px",
  // ... 50 valores
}

// ✅ CORRETO — escala finita
{
  "space-1": "4px",
  "space-2": "8px",
  "space-3": "12px",
  // ... 12-15 valores
}
```

### Anti-pattern 6: Hardcoded em vez de var

```css
/* ❌ ERRADO */
padding: 16px;

/* ✅ CORRETO */
padding: var(--space-4);
```

### Anti-pattern 7: Gutter igual em todos breakpoints

```css
/* ❌ ERRADO — mobile aperta, desktop tem espaço sobrando */
.container { padding: 16px; }

/* ✅ CORRETO — gutter cresce com tela */
.container { padding: var(--space-4); } /* mobile */
@media (min-width: 768px) { .container { padding: var(--space-6); } }
@media (min-width: 1024px) { .container { padding: var(--space-8); } }
```

---

## 8. Checklist de validação

```
ESTRUTURA:
□ Base unit definida (4px ou 8px)?
□ Escala finita (10-15 tokens, não 50)?
□ T-shirt sizes para componentes (xs/sm/md/lg/xl)?

IMPLEMENTAÇÃO:
□ tokens.json em docs/identidade-visual/?
□ CSS variables geradas?
□ Tailwind config customizado (se usa Tailwind)?
□ Stylelint configurado para validar?

USO:
□ ZERO espaçamentos hardcoded em código (grep -rE "margin:|padding:|gap:" src/ | grep -v "var(--")?
□ Hierarquia visual usa espaços diferentes (não tudo 16px)?
□ Container padding adapta por breakpoint?
□ Gap em vez de margin-top/bottom em listas?

DENSIDADE:
□ Densidade definida (compact/balanced/generous)?
□ Componentes seguem densidade?

CONTEXTO:
□ Forms têm espaçamento label-input-helper consistente?
□ Cards têm padding por densidade?
□ Listas usam gap para items?
□ Hero/marketing usa generous?
```

Se <12 checks, sistema incompleto.

---

## 9. Como integra com outras skills

### 9.1 → `quality/design-token-architecture`
Spacing é UMA das categorias de tokens (junto com color, typography, etc.).

### 9.2 → `quality/typography-scale`
Spacing e typography se relacionam (line-height, margin entre headings).

### 9.3 → `quality/layout-grid`
Container padding e gutters definidos aqui são input para grid system.

### 9.4 → `meta/refactoring-ui`
Princípio "branco é estrutura" depende de spacing system bem definido.

### 9.5 → PLAN.md de phase

```markdown
## Phase 4 — Refactor de cards

### Skills Consultadas
- `quality/spacing-system` — usar tokens, não hardcoded
- `quality/design-token-architecture` — alinhar com sistema
```

---

## 10. Erros comuns

### Erro 1: "Vamos usar o que parecer bom"
Resultado: 100 valores diferentes em produção. Migração custa semanas.
**Fix:** definir tokens no /gsd-bootstrap.

### Erro 2: "Designer escolhe, dev implementa"
Designer manda Figma com 16px aqui, 18px ali. Dev cola hex.
**Fix:** designer entrega tokens.json (Tokens Studio plugin).

### Erro 3: Token sem stylelint
Sem validação, devs voltam a hardcodar.
**Fix:** stylelint bloqueia merge.

### Erro 4: Densidade não decidida
Mesma app tem partes apertadas e partes generosas.
**Fix:** decidir 1 densidade default.

---

## 11. Ferramentas

- **Style Dictionary** — gera CSS/SCSS de tokens.json
- **Tokens Studio** (Figma plugin) — sincroniza Figma ↔ tokens.json
- **Stylelint** — valida uso de tokens
- **Tailwind** — config customizado

---

## 12. Referências

- **Refactoring UI** (Wathan, Schoger) — capítulo de espaçamento
- **8-Point Grid System** (Bryn Jackson) — base unit 8px
- **Material Design — Spacing**
- **Atlassian Design System — Spacing scale**

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 12 seções, snippets para 5 contextos (form, card, lista, hero, dashboard), anti-patterns com correção, checklist de 13 itens
