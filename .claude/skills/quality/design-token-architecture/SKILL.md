---
name: design-token-architecture
category: quality
description: Definir e organizar design tokens (cor, espaçamento, tipografia, elevação) com convenções de naming, hierarquia e usage guidance. Operacional, complementa ux-advanced/design-tokens-system.
---

# Design Token Architecture — Arquitetura de Tokens

> Tokens não são "lista de cores". É contrato entre design e código que se vc mudar o sistema sem quebrar UIs específicas.

## Quando esta skill é obrigatória

- `/gsd-bootstrap` quando humano fornece tokens.json
- `/gsd-ui-phase` em projeto novo (primeira phase com UI)
- Refactor de design system existente
- Adição de tema novo (dark mode, white-label)

## Hierarquia de tokens (3 camadas)

### Camada 1 — Tokens primitivos (foundation)

Valores brutos, sem semântica.

```json
{
  "color": {
    "blue": {
      "50":  "#eff6ff",
      "100": "#dbeafe",
      "500": "#3b82f6",
      "900": "#1e3a8a"
    }
  },
  "space": {
    "1": "4px",
    "2": "8px",
    "4": "16px",
    "8": "32px"
  }
}
```

**Regra:** componentes NÃO usam primitivos diretamente.

### Camada 2 — Tokens semânticos (alias)

Aponta primitivo + semântica.

```json
{
  "color": {
    "brand": {
      "primary": "{color.blue.500}",
      "primary-hover": "{color.blue.600}"
    },
    "text": {
      "primary": "{color.gray.900}",
      "secondary": "{color.gray.600}",
      "inverse": "{color.white}"
    },
    "surface": {
      "default": "{color.white}",
      "raised": "{color.white}",
      "sunken": "{color.gray.50}"
    },
    "feedback": {
      "success": "{color.green.500}",
      "warning": "{color.yellow.500}",
      "danger": "{color.red.500}",
      "info": "{color.blue.500}"
    }
  }
}
```

**Regra:** componentes USAM tokens semânticos.

### Camada 3 — Tokens de componente (opcional)

Específico de componente quando precisa override.

```json
{
  "button": {
    "primary": {
      "background": "{color.brand.primary}",
      "text": "{color.text.inverse}",
      "border-radius": "{radius.md}"
    }
  }
}
```

## Naming conventions

### Estrutura

```
{category}.{property}.{variant}.{state}
```

Exemplos:
- `color.brand.primary` (categoria: color, property: brand, variant: primary)
- `color.text.primary.disabled` (com estado)
- `space.layout.gutter` (categoria: space, property: layout, variant: gutter)

### Regras

✅ kebab-case ou camelCase, consistente em todo arquivo
✅ Singular: `color`, não `colors`
✅ Genérico→específico: `text-primary`, não `primary-text`
✅ Estado por último: `text-primary-disabled`

❌ Cores literais em nome: `azul-bonito`, `red-from-figma`
❌ Mistura de convenções: `colorPrimary` + `text_primary`
❌ Aninhamento profundo (>4): `theme.dark.color.text.primary.hover.disabled.icon`

## Tokens mínimos viáveis (gate 2 do gsd)

Para gate 2 (Visual Contract) passar, mínimo:

```json
{
  "_meta": { "mode": "provisional", "version": "1.0" },
  "color": {
    "brand": { "primary": "#0066cc" },
    "text": { "primary": "#111827", "secondary": "#6b7280" },
    "surface": { "default": "#ffffff", "sunken": "#f9fafb" },
    "border": { "default": "#e5e7eb" },
    "feedback": {
      "success": "#10b981",
      "warning": "#f59e0b",
      "danger": "#ef4444"
    }
  },
  "space": {
    "xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"
  }
}
```

## Anti-patterns

❌ Componentes usando cores hardcoded (`#3b82f6` no código)
❌ Componentes usando primitivos diretos (`{color.blue.500}` sem semântica)
❌ Hex em vez de referência (`background: "#fff"` em token semântico)
❌ Token semântico sem primitivo correspondente
❌ Dark mode adicionado depois — sempre projetar tokens para suportar tema desde o início

## Ferramentas

- **Style Dictionary**: gera CSS/SCSS/JS de tokens.json (Amazon)
- **Theo**: similar (Salesforce)
- **Tokens Studio**: plugin Figma para sincronizar
- **Figma Tokens**: alternativa

## Integração

- Implementa o que `ux-advanced/design-tokens-system` define em alto nível
- Usado por `quality/spacing-system`, `quality/typography-scale`, `quality/color-system`
- Output vai para `docs/identidade-visual/tokens.json`
