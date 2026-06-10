# Design System — {nome do projeto}

> Fonte de verdade visual. Consumido pelo `gsd-ui-researcher` ao gerar `UI-SPEC.md`.
> Preencha antes de rodar `/gsd-ui-phase` em qualquer fase de UI.

---

## 1. Personalidade de marca

3-5 adjetivos que descrevem como o produto deve "sentir".

> Ex: confiável, rápido, técnico-humano, premium sem ser frio.

## 2. Tom de voz

Como o produto fala com o usuário. Inclua exemplos.

> Ex:
> - **Direto, não corporativo.** "Proposta aceita" em vez de "Sua proposta foi aceita com sucesso".
> - **Sem jargão técnico salvo quando necessário.** "Sessão expirada" em vez de "JWT_EXPIRED".
> - **Assume que o usuário é inteligente.** Não explica o óbvio.
> - **Celebra pequenas vitórias.** Micro-copy após ação concluída ("Seu jeito.").

Anti-patterns de copy:
- "Ops!"
- "Algo deu errado"
- "Você é um vencedor!"
- Exclamação em excesso.

## 3. Paleta

Tokens semânticos (não nomes de cor). Todos em CSS custom properties.

```css
:root {
  /* Brand */
  --color-brand-50:   #{valor};
  --color-brand-100:  #{valor};
  --color-brand-500:  #{valor};  /* cor principal */
  --color-brand-700:  #{valor};
  --color-brand-900:  #{valor};

  /* Semânticas */
  --color-success-500: #{valor};
  --color-warning-500: #{valor};
  --color-danger-500:  #{valor};
  --color-info-500:    #{valor};

  /* Neutras */
  --color-gray-50:   #{valor};
  --color-gray-100:  #{valor};
  --color-gray-500:  #{valor};
  --color-gray-900:  #{valor};

  /* Superfícies */
  --color-surface-primary:   var(--color-gray-50);
  --color-surface-secondary: var(--color-gray-100);
  --color-surface-elevated:  #ffffff;

  /* Texto */
  --color-text-primary:   var(--color-gray-900);
  --color-text-secondary: var(--color-gray-500);
  --color-text-inverse:   #ffffff;
}

/* Dark mode (se aplicável) */
:root[data-theme="dark"] {
  --color-surface-primary:   var(--color-gray-900);
  /* ... */
}
```

**Regra:** nenhum `#hex` direto em componente. Sempre `var(--color-*)`.

## 4. Tipografia

```css
:root {
  --font-sans:   "Inter", system-ui, sans-serif;
  --font-serif:  "Source Serif", Georgia, serif;
  --font-mono:   "JetBrains Mono", Consolas, monospace;

  /* Scale */
  --font-size-xs:   0.75rem;   /* 12px */
  --font-size-sm:   0.875rem;  /* 14px */
  --font-size-base: 1rem;      /* 16px */
  --font-size-lg:   1.125rem;  /* 18px */
  --font-size-xl:   1.25rem;   /* 20px */
  --font-size-2xl:  1.5rem;    /* 24px */
  --font-size-3xl:  2rem;      /* 32px */
  --font-size-4xl:  2.5rem;    /* 40px */

  /* Pesos */
  --font-weight-regular:  400;
  --font-weight-medium:   500;
  --font-weight-semibold: 600;
  --font-weight-bold:     700;

  /* Line height */
  --leading-tight:  1.25;
  --leading-normal: 1.5;
  --leading-loose:  1.75;
}
```

Hierarquia:
- `h1`: `--font-size-3xl`, `--font-weight-bold`, `--leading-tight`
- `h2`: `--font-size-2xl`, `--font-weight-semibold`
- `h3`: `--font-size-xl`, `--font-weight-semibold`
- `body`: `--font-size-base`, `--font-weight-regular`, `--leading-normal`
- `caption`: `--font-size-sm`, `--color-text-secondary`

## 5. Espaçamento

Base 4px, scale exponencial.

```css
:root {
  --space-xs:   4px;
  --space-sm:   8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  32px;
  --space-2xl: 48px;
  --space-3xl: 64px;
}
```

## 6. Raios, sombras, bordas

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;  /* pill */

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

  --border-width: 1px;
  --border-color: var(--color-gray-200);
}
```

## 7. Motion

```css
:root {
  --duration-fast:   100ms;  /* feedback de clique */
  --duration-normal: 200ms;  /* transição entre estados */
  --duration-slow:   400ms;  /* transição entre telas */

  --easing-out:    cubic-bezier(0.0, 0.0, 0.2, 1);
  --easing-spring: cubic-bezier(0.5, 1.25, 0.75, 1.25);
}
```

**Anti-patterns:**
- Duração > 500ms em ação crítica
- Animação de propriedades que não sejam `transform`/`opacity`
- Ignorar `prefers-reduced-motion`

## 8. Ícones

- **Biblioteca:** {ex: Lucide, Material Symbols, Heroicons}
- **Tamanhos padronizados:** 16, 20, 24, 32
- **Peso:** {regular | outlined | filled}
- **Regra:** ícone isolado = precisa de `aria-label` ou texto invisível

## 9. Componentes canônicos

Este projeto usa os componentes abaixo. Variações têm UI-SPEC específico.

| Componente | Uso | Regras |
|------------|-----|--------|
| **Button** | Ação primária ou secundária | `btn-primary` / `btn-secondary` / `btn-ghost`. Sempre 44×44 touch target mínimo. |
| **Card** | Agrupar informação relacionada | Padding `--space-md`, radius `--radius-md`, shadow `--shadow-sm`. |
| **Input** | Entrada de dados | Label SEMPRE visível (não apenas placeholder). Erro inline abaixo. |
| **Modal** | Ação destrutiva ou info crítica | Focus trap + esc + role="dialog" + overlay click fecha. |
| **Toast** | Feedback efêmero | 3-5s default, pausa em hover. `aria-live="polite"`. |
| **Empty State** | Listagem vazia | Ilustração + copy + CTA. Nunca "nenhum dado". |
| **Skeleton** | Loading | Reflete o layout real. Nunca spinner em listagem. |

Cada componente tem story no Storybook (quando `component-library-governance` ativa).

## 10. Grid e breakpoints

```css
:root {
  --breakpoint-sm:   480px;
  --breakpoint-md:   768px;
  --breakpoint-lg:  1024px;
  --breakpoint-xl:  1440px;

  --container-max: 1200px;
}
```

Layout:
- Mobile (< 480): stack vertical, padding `--space-md`
- Tablet (768): 2 colunas
- Desktop (1024+): 3 colunas + sidebar opcional

## 11. Inspirações / benchmarks

Produtos de referência para este projeto:

- **Dashboard:** {ex: Linear, Stripe Dashboard}
- **Checkout/pagamento:** {ex: Stripe Checkout, Mercado Pago}
- **Chat:** {ex: WhatsApp Web, Telegram}
- **Mobile onboarding:** {ex: Urban Company}

---

## Acesso ao `tokens.json`

Tokens exportáveis em `docs/identidade-visual/tokens.json` (mesmo conteúdo, formato machine-readable para ferramentas).

## Quando atualizar este documento

- Nova fase introduz componente novo? Adicionar à seção 9.
- Tokens precisam de variação? Propor ADR em `docs/adrs/`.
- Rebrand? Atualizar tudo + gerar regressão visual em todos componentes.
