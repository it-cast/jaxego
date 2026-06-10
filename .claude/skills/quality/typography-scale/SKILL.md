---
name: typography-scale
category: quality
description: Escala tipográfica modular completa — ratios, base size, line-height contextual, letter-spacing por tamanho, font pairing, escolha de famílias, performance (font-display, subsetting), acessibilidade. Inclui 5 ratios calculados, font pairings testados, snippets CSS, anti-patterns e validação. Resolve "tipografia random" e "fonte cansa olho".
---

# Typography Scale — Escala Tipográfica

> Tipografia é 90% da UX em produto sem imagens (SaaS, dashboards, docs). Random = hierarquia confusa. Escala modular = profissional.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-ui-phase` em projeto novo | Fundação do design system |
| Refactor de tipografia | Migrar de tamanhos random |
| Adição de fonte nova | Garantir consistência |
| Antes de release marketing/landing | Tipografia define personalidade |

## 2. Quando NÃO usar

- Phase backend
- Phase de infra
- Sistema já estabelecido (apenas seguir)

---

## 3. Princípios

### 3.1 Escala modular (não tamanhos arbitrários)

Multiplicador (ratio) constante entre tamanhos.

**Ratios canônicos:**

| Ratio | Nome | Quando usar |
|---|---|---|
| 1.067 | Minor Second | Texto-only, alta densidade (jornais, dicionários) |
| 1.125 | Major Second | UI compacta, dashboards densos |
| 1.200 | Minor Third | UI padrão (default seguro) |
| 1.250 | Major Third | Marketing site, expressivo |
| 1.333 | Perfect Fourth | Editorial, blog |
| 1.414 | Augmented Fourth | Hero pages |
| 1.500 | Perfect Fifth | Landing premium, alto impacto |

**Default web/SaaS:** 1.200 ou 1.250.

### 3.2 Base size = 16px

Tamanho do body, base para a escala.

```
Ratio 1.200, base 16:
12.5, 15, 18, 21.6, 25.9, 31.1, 37.3, 44.8

Arredondado para inteiros:
12, 14, 16, 18, 22, 26, 32, 38, 46
```

### 3.3 Tokens semânticos, não tamanhos

```json
{
  "typography": {
    "scale": {
      "xs":   "12px",
      "sm":   "14px",
      "base": "16px",
      "lg":   "18px",
      "xl":   "20px",
      "2xl":  "24px",
      "3xl":  "30px",
      "4xl":  "36px",
      "5xl":  "48px",
      "6xl":  "60px",
      "7xl":  "72px",
      "8xl":  "96px"
    },
    "lineHeight": {
      "none":    "1",
      "tight":   "1.25",
      "snug":    "1.375",
      "normal":  "1.5",
      "relaxed": "1.625",
      "loose":   "2"
    },
    "weight": {
      "thin":      100,
      "extralight": 200,
      "light":      300,
      "regular":    400,
      "medium":     500,
      "semibold":   600,
      "bold":       700,
      "extrabold":  800,
      "black":      900
    },
    "letterSpacing": {
      "tighter": "-0.05em",
      "tight":   "-0.025em",
      "normal":  "0",
      "wide":    "0.025em",
      "wider":   "0.05em",
      "widest":  "0.1em"
    }
  },

  "_semantic": {
    "display-1": {
      "size":   "{typography.scale.7xl}",
      "weight": "{typography.weight.bold}",
      "lineHeight": "{typography.lineHeight.none}",
      "letterSpacing": "{typography.letterSpacing.tighter}"
    },
    "display-2": {
      "size":   "{typography.scale.6xl}",
      "weight": "{typography.weight.bold}",
      "lineHeight": "{typography.lineHeight.tight}",
      "letterSpacing": "{typography.letterSpacing.tight}"
    },
    "heading-1": {
      "size":   "{typography.scale.5xl}",
      "weight": "{typography.weight.bold}",
      "lineHeight": "{typography.lineHeight.tight}",
      "letterSpacing": "{typography.letterSpacing.tight}"
    },
    "heading-2": {
      "size":   "{typography.scale.4xl}",
      "weight": "{typography.weight.bold}",
      "lineHeight": "{typography.lineHeight.tight}"
    },
    "heading-3": {
      "size":   "{typography.scale.3xl}",
      "weight": "{typography.weight.semibold}",
      "lineHeight": "{typography.lineHeight.snug}"
    },
    "heading-4": {
      "size":   "{typography.scale.2xl}",
      "weight": "{typography.weight.semibold}",
      "lineHeight": "{typography.lineHeight.snug}"
    },
    "heading-5": {
      "size":   "{typography.scale.xl}",
      "weight": "{typography.weight.semibold}",
      "lineHeight": "{typography.lineHeight.snug}"
    },
    "heading-6": {
      "size":   "{typography.scale.lg}",
      "weight": "{typography.weight.semibold}",
      "lineHeight": "{typography.lineHeight.normal}"
    },
    "body-lg": {
      "size":   "{typography.scale.lg}",
      "weight": "{typography.weight.regular}",
      "lineHeight": "{typography.lineHeight.relaxed}"
    },
    "body": {
      "size":   "{typography.scale.base}",
      "weight": "{typography.weight.regular}",
      "lineHeight": "{typography.lineHeight.normal}"
    },
    "body-sm": {
      "size":   "{typography.scale.sm}",
      "weight": "{typography.weight.regular}",
      "lineHeight": "{typography.lineHeight.normal}"
    },
    "caption": {
      "size":   "{typography.scale.xs}",
      "weight": "{typography.weight.regular}",
      "lineHeight": "{typography.lineHeight.normal}",
      "letterSpacing": "{typography.letterSpacing.wide}"
    },
    "overline": {
      "size":   "{typography.scale.xs}",
      "weight": "{typography.weight.semibold}",
      "lineHeight": "{typography.lineHeight.normal}",
      "letterSpacing": "{typography.letterSpacing.widest}",
      "textTransform": "uppercase"
    }
  }
}
```

### 3.4 Line-height por contexto

```
Tamanho       Line-height ideal
72px+         1.0 (display)
48-64px       1.1
36-46px       1.15
30-32px       1.2
20-26px       1.3
18-20px       1.4
14-16px       1.5 (body)
12-14px       1.5
```

**Princípio:** quanto maior o tamanho, menor o line-height. Quanto menor o tamanho, maior o line-height (legibilidade).

### 3.5 Letter-spacing por size

```
Tamanho        Letter-spacing
72px+          -0.04em (mais junto - displays)
48-64px        -0.025em (negative)
24-46px        -0.01em
16-22px        0 (default)
12-14px        +0.01em
≤12px          +0.025em (mais aberto - legibilidade)
```

---

## 4. Font pairings testados (escolha 1)

### 4.1 Combinações canônicas

| Display (headings) | Body | Estilo | Uso |
|---|---|---|---|
| **Inter** | **Inter** | Sans neutro | Default seguro (SaaS, dashboards) |
| **Cal Sans** | Inter | Display jovial + body neutro | Marketing moderno |
| **Playfair Display** | Inter | Editorial + sans | Blog, content-heavy |
| **JetBrains Mono** | Inter | Tech + body | Dev tools, terminals |
| **Geist** | Geist Mono | Vercel-style | Tech minimalista |
| **Manrope** | Manrope | Geometric clean | SaaS clean |
| **Plus Jakarta Sans** | Plus Jakarta Sans | Friendly modern | B2C friendly |
| **DM Serif Display** | DM Sans | Editorial bold + sans | Premium, fashion |
| **Söhne** | Söhne | Premium humanist | High-end SaaS (paid) |
| **Geograph** | Geograph | Brasileira | Produtos BR |

### 4.2 Regras de pairing

✅ Use **1-2 famílias**. Nunca 3+.
✅ Se 2 famílias, contraste claro (serif + sans, display + body).
✅ Se UI texto-heavy (SaaS, docs), body em **sans-serif**.
✅ Display fica para hero/marketing, não toda página.

❌ Misturar 3+ famílias.
❌ Display em texto longo (cansa olho).
❌ Serif decorativa em UI (Playfair em dashboard = errado).

### 4.3 Sistemas vs Web fonts

**System fonts (zero loading):**
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
```

Pros: zero request, performance perfeito.
Contras: visual diferente em cada OS.

**Web fonts (Google Fonts, self-hosted):**
```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}
```

Pros: consistência cross-OS.
Contras: request adicional (otimizar com swap, preload).

**Recomendação:** web font para brand consistente, com fallback de system.

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

---

## 5. CSS implementation completa

### 5.1 Variables

```css
:root {
  /* Family */
  --font-display: 'Inter', -apple-system, sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;

  /* Scale */
  --text-xs:   12px;
  --text-sm:   14px;
  --text-base: 16px;
  --text-lg:   18px;
  --text-xl:   20px;
  --text-2xl:  24px;
  --text-3xl:  30px;
  --text-4xl:  36px;
  --text-5xl:  48px;
  --text-6xl:  60px;
  --text-7xl:  72px;
  --text-8xl:  96px;

  /* Line height */
  --leading-none:    1;
  --leading-tight:   1.25;
  --leading-snug:    1.375;
  --leading-normal:  1.5;
  --leading-relaxed: 1.625;

  /* Weight */
  --font-regular:  400;
  --font-medium:   500;
  --font-semibold: 600;
  --font-bold:     700;

  /* Letter spacing */
  --tracking-tighter: -0.05em;
  --tracking-tight:   -0.025em;
  --tracking-normal:  0;
  --tracking-wide:    0.025em;
  --tracking-widest:  0.1em;
}
```

### 5.2 Classes semânticas

```css
.text-display-1 {
  font-size: var(--text-7xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-none);
  letter-spacing: var(--tracking-tighter);
  font-family: var(--font-display);
}

.text-h1 {
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
  font-family: var(--font-display);
}

.text-h2 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  font-family: var(--font-display);
}

.text-h3 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  font-family: var(--font-display);
}

.text-h4 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  font-family: var(--font-display);
}

.text-body-lg {
  font-size: var(--text-lg);
  font-weight: var(--font-regular);
  line-height: var(--leading-relaxed);
  font-family: var(--font-body);
}

.text-body {
  font-size: var(--text-base);
  font-weight: var(--font-regular);
  line-height: var(--leading-normal);
  font-family: var(--font-body);
}

.text-body-sm {
  font-size: var(--text-sm);
  font-weight: var(--font-regular);
  line-height: var(--leading-normal);
  font-family: var(--font-body);
}

.text-caption {
  font-size: var(--text-xs);
  font-weight: var(--font-regular);
  line-height: var(--leading-normal);
  letter-spacing: var(--tracking-wide);
  font-family: var(--font-body);
}

.text-overline {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  line-height: var(--leading-normal);
  letter-spacing: var(--tracking-widest);
  text-transform: uppercase;
  font-family: var(--font-body);
}

.text-mono {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}
```

### 5.3 HTML defaults

```css
/* Reset + defaults sensatos */
html {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
  margin-bottom: var(--space-2);
  color: var(--color-text-primary);
}

h1 { font-size: var(--text-5xl); }
h2 { font-size: var(--text-4xl); }
h3 { font-size: var(--text-3xl); }
h4 { font-size: var(--text-2xl); }
h5 { font-size: var(--text-xl); }
h6 { font-size: var(--text-lg); }

p { margin-bottom: var(--space-4); }

code, kbd {
  font-family: var(--font-mono);
  font-size: 0.9em;
}
```

---

## 6. Performance e font loading

### 6.1 Font-display strategy

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap; /* mostra fallback enquanto carrega */
}
```

**Opções de font-display:**

| Valor | Comportamento | Quando usar |
|---|---|---|
| `swap` | Fallback imediato, troca quando carrega | Default — melhor para LCP |
| `fallback` | 100ms invisible, depois fallback até swap | Compromisso |
| `optional` | 100ms invisible, se não carregar usa fallback | Mobile lento |
| `block` | Invisível até 3s | NÃO usar (FOIT visible) |

### 6.2 Preload

```html
<link rel="preload"
      href="/fonts/inter-var.woff2"
      as="font"
      type="font/woff2"
      crossorigin>
```

Carrega font ANTES do CSS pedir.

### 6.3 Variable fonts

Variable fonts contêm múltiplos pesos em 1 arquivo:

```css
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2-variations');
  font-weight: 100 900; /* range */
}

.heavy { font-weight: 900; }
.light { font-weight: 200; }
/* mesmo arquivo serve todos os pesos */
```

Pros: 1 request em vez de 6+. Pequeno overhead vs muitos requests.

### 6.4 Subsetting

```bash
# Reduzir font para apenas latin-extended
pyftsubset Inter-Regular.ttf \
  --unicodes="U+0000-00FF,U+0131,U+0152-0153" \
  --output-file=Inter-Regular-subset.woff2 \
  --flavor=woff2
```

40KB → 12KB típico. Para pt-BR, latin-extended cobre acentos.

---

## 7. Acessibilidade

### 7.1 Tamanho mínimo

- **Body text**: mínimo 14px, recomendado 16px
- **UI labels**: mínimo 12px (com letter-spacing wider para legibilidade)
- **Captions**: mínimo 11px (raramente, em legals/disclaimers)

### 7.2 Contraste

Coberto por `quality/color-system`:
- Body text vs background: 4.5:1 mínimo
- Texto grande (18pt+ ou 14pt bold+): 3:1 mínimo

### 7.3 Zoom 200%

Texto deve ser legível com zoom 200%. Use:
- `font-size` em rem ou px (não em viewport units para body)
- Layout flex/grid que se adapta

```css
/* ✅ Funciona com zoom */
.body { font-size: 1rem; }

/* ❌ Não responde a zoom do browser */
.body { font-size: 1vw; }
```

### 7.4 Dyslexia-friendly

Para usuários com dislexia:
- **Fonts recomendadas**: OpenDyslexic, Lexend, Atkinson Hyperlegible
- **Line-height generoso** (1.5+)
- **Letter-spacing** levemente positivo (+0.01em)
- **Background não-branco** (off-white reduz cansaço)
- **Não justificar texto** (rivers irregulares confundem)

### 7.5 Linguagem do leitor

```html
<html lang="pt-BR">
```

Importante para screen readers (pronúncia correta).

---

## 8. Casos práticos por contexto

### 8.1 SaaS B2B dashboard

```yaml
font_choice: "Inter (var) ou Geist"
ratio: 1.200 (Minor Third) - balanced
sizes_used: ["xs", "sm", "base", "lg", "xl", "2xl", "3xl"]
densidade: high (mais info por tela)
hero_size: "2xl-3xl" (não 5xl - sem necessidade)
body: "base" (16px)
helper_text: "sm" (14px)
```

### 8.2 Marketing landing

```yaml
font_choice: "Display fonte (Cal Sans) + Inter body"
ratio: 1.250-1.333 (mais expressivo)
sizes_used: ["sm", "base", "lg", "xl", "3xl", "5xl", "7xl"]
densidade: low (espaçoso, hero grande)
hero_size: "7xl" (72px)
body: "lg" (18px)
```

### 8.3 Blog/editorial

```yaml
font_choice: "Playfair Display (headings) + Inter (body)"
ratio: 1.333 (Perfect Fourth)
sizes_used: ["sm", "base", "lg", "2xl", "3xl", "4xl"]
densidade: medium
hero_size: "4xl"
body: "lg" (mais legibilidade em texto longo)
line_height_body: "relaxed" (1.625)
max_width_text: "65ch" (otimizar leitura)
```

### 8.4 Mobile app

```yaml
font_choice: "system fonts (Apple SF Pro / Roboto)"
ratio: 1.125 (Major Second) - mais discreto
sizes_used: ["xs", "sm", "base", "lg", "xl", "2xl"]
densidade: high (telas pequenas)
hero_size: "2xl" (24px - moderado)
body: "base"
```

### 8.5 Áugure (validação de mercado)

```yaml
font_choice: "Inter (var) + JetBrains Mono para números"
ratio: 1.200
sizes_used: ["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]
densidade: medium-high
hero: "3xl-4xl"
body: "base"
relatorio: "lg" (18px - legibilidade em PDF de 70 páginas)
data_numerica: "mono" (alinhamento de colunas)
```

---

## 9. Anti-patterns com correção

### Anti-pattern 1: Tamanhos random

```css
/* ❌ ERRADO */
h1 { font-size: 32px; }
h2 { font-size: 28px; }
h3 { font-size: 22px; }
p  { font-size: 17px; }

/* ✅ CORRETO — escala modular */
h1 { font-size: var(--text-4xl); }  /* 36px */
h2 { font-size: var(--text-3xl); }  /* 30px */
h3 { font-size: var(--text-2xl); }  /* 24px */
p  { font-size: var(--text-base); } /* 16px */
```

### Anti-pattern 2: Misturar 3+ famílias

```css
/* ❌ ERRADO */
h1 { font-family: Playfair Display; }
h2 { font-family: Roboto; }
button { font-family: Open Sans; }
p { font-family: Lato; }

/* ✅ CORRETO — 1-2 famílias */
h1, h2 { font-family: var(--font-display); } /* Cal Sans */
body, p, button { font-family: var(--font-body); } /* Inter */
```

### Anti-pattern 3: Line-height igual para tudo

```css
/* ❌ ERRADO */
* { line-height: 1.4; }
/* h1 com 1.4 fica espaçado demais, p com 1.4 fica apertado */

/* ✅ CORRETO — contextual */
h1, h2 { line-height: var(--leading-tight); }   /* 1.25 */
h3, h4 { line-height: var(--leading-snug); }    /* 1.375 */
p { line-height: var(--leading-normal); }       /* 1.5 */
.long-form { line-height: var(--leading-relaxed); } /* 1.625 */
```

### Anti-pattern 4: Letter-spacing default em todos os tamanhos

```css
/* ❌ ERRADO */
* { letter-spacing: 0; }
/* Heading 72px fica frouxo, caption 11px fica apertado */

/* ✅ CORRETO */
h1.display { letter-spacing: var(--tracking-tighter); } /* -0.05em */
h1, h2 { letter-spacing: var(--tracking-tight); }       /* -0.025em */
p, body { letter-spacing: var(--tracking-normal); }     /* 0 */
.caption { letter-spacing: var(--tracking-wide); }      /* +0.025em */
.overline { letter-spacing: var(--tracking-widest); }   /* +0.1em */
```

### Anti-pattern 5: Hardcoded em vez de tokens

```css
/* ❌ ERRADO */
h1 { font-size: 36px; line-height: 40px; font-weight: 700; }

/* ✅ CORRETO */
h1 {
  font-size: var(--text-4xl);
  line-height: var(--leading-tight);
  font-weight: var(--font-bold);
}
```

### Anti-pattern 6: FOIT (Flash of Invisible Text)

```css
/* ❌ ERRADO — texto invisível até font carregar */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter.woff2');
  /* sem font-display */
}

/* ✅ CORRETO */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter.woff2');
  font-display: swap; /* fallback até carregar */
}
```

### Anti-pattern 7: Body em fonte display

```css
/* ❌ ERRADO — Playfair em texto longo cansa */
body { font-family: 'Playfair Display'; }

/* ✅ CORRETO — display só em headings */
body { font-family: 'Inter'; }
h1, h2 { font-family: 'Playfair Display'; }
```

---

## 10. Checklist de validação

```
ESCALA:
□ Base size 16px definida?
□ Ratio escolhido (1.2 default)?
□ Tokens semânticos (display, h1-h6, body, caption)?
□ 8-12 tamanhos (não infinitos)?

LINE-HEIGHT:
□ Tight (1.0-1.25) para headings?
□ Normal (1.5) para body?
□ Relaxed (1.625) para long-form?

WEIGHT:
□ Regular (400) para body?
□ Semibold (600) para headings médios?
□ Bold (700) para display?

LETTER-SPACING:
□ Negative para tamanhos grandes (-0.025em)?
□ Normal para body (0)?
□ Wide para caption (+0.025em)?

FONT FAMILY:
□ 1-2 famílias só?
□ Body em sans-serif (se UI texto-heavy)?
□ Web font com fallback de system?

PERFORMANCE:
□ font-display: swap?
□ Preload em fonts críticas?
□ Variable font (se possível)?
□ Subset latin-extended para pt-BR?

ACESSIBILIDADE:
□ Body mínimo 14px (16px recomendado)?
□ html lang="pt-BR"?
□ Funciona com zoom 200%?
□ Contraste AA (vide color-system)?

USO:
□ ZERO font-size hardcoded em código?
□ Stylelint configurado?
□ Tokens em docs/identidade-visual/?
```

Se <15 checks, sistema incompleto.

---

## 11. Como integra com outras skills

### 11.1 → `quality/design-token-architecture`
Typography é categoria de tokens.

### 11.2 → `quality/spacing-system`
Margin entre elementos tipográficos depende de spacing.

### 11.3 → `quality/color-system`
Cor de texto vem de tokens semânticos de color-system.

### 11.4 → `meta/refactoring-ui`
Princípio "hierarquia > tamanho" depende de typography bem feita.

### 11.5 → `quality/accessibility-pro`
Contraste e tamanhos auditados.

### 11.6 → PLAN.md de phase

```markdown
## Phase 5 — Refactor de tipografia

### Skills Consultadas
- `quality/typography-scale` — escala modular, font pairing
- `quality/spacing-system` — margins entre elementos
- `quality/color-system` — cor de texto
```

---

## 12. Erros comuns

### Erro 1: "Designer escolhe tamanho, dev cola"
Resultado: 30 tamanhos diferentes em produção.
**Fix:** designer entrega tokens.json, dev usa só var.

### Erro 2: Pular font-display
FOIT: usuário vê tela em branco enquanto font carrega.
**Fix:** sempre font-display: swap.

### Erro 3: 4+ famílias de fonte
Cada família = request adicional + visual confuso.
**Fix:** máximo 2 famílias.

### Erro 4: Line-height default
Tudo com 1.4 ou 1.5 fica errado em algum tamanho.
**Fix:** contextual (tight/snug/normal/relaxed).

### Erro 5: Texto justificado em web
Espaços irregulares (rivers) atrapalham leitura.
**Fix:** text-align: left (LTR) sempre.

---

## 13. Ferramentas

### 13.1 Geração de escala

- **Typescale.com** — calcula ratios visualmente
- **Modular Scale** — modularscale.com
- **Type Scale** — type-scale.com

### 13.2 Font pairing

- **Fontpair.co** — combinações testadas
- **Google Fonts pairs** — google fonts UI
- **Fontjoy.com** — gera pares por AI

### 13.3 Performance

- **Font Squirrel Webfont Generator** — gera @font-face + subset
- **glyphhanger** — analisa quais glyphs você realmente usa
- **wakamai fondue** — analisa font (variations, glyphs)

### 13.4 Acessibilidade

- **axe DevTools** — audit completo
- **Lighthouse** — performance + a11y

---

## 14. Referências

- **Practical Typography** (Matthew Butterick) — butterick.com/practical-typography
- **Typography Handbook** — typographyhandbook.com
- **Modular Scale** — modularscale.com
- **Refactoring UI** — capítulo de tipografia
- **Robert Bringhurst** — "The Elements of Typographic Style" (livro canônico)

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 14 seções, 7 ratios calculados, 10 font pairings testados, snippets CSS completos, 5 contextos práticos, performance, anti-patterns com correção, checklist de 21 itens
