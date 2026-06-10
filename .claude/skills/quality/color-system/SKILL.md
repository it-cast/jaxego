---
name: color-system
category: quality
description: Sistema completo de cor para produto digital — paletas (brand/neutral/feedback), mapping semântico em 3 camadas, compliance WCAG AA/AAA com fórmulas, daltonismo, dark mode com swap automático, paletas pré-calculadas hex codes prontas, naming conventions, ferramentas e validação. Resolve cor inventada que reprova em audit ou exclui daltônicos.
---

# Color System — Sistema de Cor Completo

> Cor errada não é só feio. Reprova em audit de acessibilidade, exclui 8% dos homens daltônicos, e é a primeira coisa que distingue UI profissional de amadora.

Esta skill entrega: paletas hex prontas, regras WCAG concretas, dark mode funcional, naming canônico, e como validar tudo.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-ui-phase` em projeto novo | Fundação do design system |
| Adição de tema (dark mode, white-label) | Paleta precisa suportar swap |
| Refactor de cores | Migrar de hex hardcoded para tokens |
| Antes de audit WCAG | Validar contraste de texto e UI |
| Phase de marketing/landing | Brand color hero precisa funcionar |

## 2. Quando NÃO usar

- Phase backend/API sem UI
- Phase de infra
- Refactor que não toca em estilos visuais

---

## 3. Estrutura: 3 camadas

### 3.1 Camada 1 — Tokens primitivos (paleta foundation)

Valores brutos em hex. Não usar diretamente em componentes.

```json
{
  "color": {
    "blue": {
      "50":  "#eff6ff",
      "100": "#dbeafe",
      "200": "#bfdbfe",
      "300": "#93c5fd",
      "400": "#60a5fa",
      "500": "#3b82f6",
      "600": "#2563eb",
      "700": "#1d4ed8",
      "800": "#1e40af",
      "900": "#1e3a8a",
      "950": "#172554"
    }
  }
}
```

### 3.2 Camada 2 — Tokens semânticos (alias)

Componentes USAM esta camada.

```json
{
  "color": {
    "brand": {
      "primary":       "{color.blue.500}",
      "primary-hover": "{color.blue.600}",
      "primary-active": "{color.blue.700}",
      "primary-disabled": "{color.blue.200}"
    },
    "text": {
      "primary":   "{color.gray.900}",
      "secondary": "{color.gray.600}",
      "tertiary":  "{color.gray.500}",
      "disabled":  "{color.gray.400}",
      "inverse":   "{color.white}"
    },
    "surface": {
      "default": "{color.white}",
      "raised":  "{color.white}",
      "sunken":  "{color.gray.50}",
      "overlay": "rgba(0,0,0,0.5)"
    },
    "border": {
      "default": "{color.gray.200}",
      "strong":  "{color.gray.300}",
      "focus":   "{color.brand.primary}"
    },
    "feedback": {
      "success": "{color.green.500}",
      "warning": "{color.yellow.500}",
      "danger":  "{color.red.500}",
      "info":    "{color.blue.500}"
    }
  }
}
```

### 3.3 Camada 3 — Tokens de componente (opcional)

Quando componente precisa override.

```json
{
  "button": {
    "primary": {
      "background":      "{color.brand.primary}",
      "background-hover": "{color.brand.primary-hover}",
      "text":            "{color.text.inverse}",
      "border":          "transparent"
    },
    "secondary": {
      "background":      "transparent",
      "text":            "{color.brand.primary}",
      "border":          "{color.brand.primary}"
    }
  }
}
```

---

## 4. Paletas pré-calculadas (hex codes prontos)

### 4.1 Tailwind palette (default seguro, testado)

**Slate (cinza com leve tom azulado):**
```json
{
  "slate": {
    "50":  "#f8fafc",
    "100": "#f1f5f9",
    "200": "#e2e8f0",
    "300": "#cbd5e1",
    "400": "#94a3b8",
    "500": "#64748b",
    "600": "#475569",
    "700": "#334155",
    "800": "#1e293b",
    "900": "#0f172a",
    "950": "#020617"
  }
}
```

**Neutral (cinza puro):**
```json
{
  "neutral": {
    "50":  "#fafafa",
    "100": "#f5f5f5",
    "200": "#e5e5e5",
    "300": "#d4d4d4",
    "400": "#a3a3a3",
    "500": "#737373",
    "600": "#525252",
    "700": "#404040",
    "800": "#262626",
    "900": "#171717",
    "950": "#0a0a0a"
  }
}
```

**Stone (cinza com leve tom marrom):**
```json
{
  "stone": {
    "50":  "#fafaf9",
    "100": "#f5f5f4",
    "200": "#e7e5e4",
    "300": "#d6d3d1",
    "400": "#a8a29e",
    "500": "#78716c",
    "600": "#57534e",
    "700": "#44403c",
    "800": "#292524",
    "900": "#1c1917",
    "950": "#0c0a09"
  }
}
```

### 4.2 Brand colors (escolha 1 base, gere escala)

**Azul:**
```
50: #eff6ff   100: #dbeafe   200: #bfdbfe   300: #93c5fd
400: #60a5fa   500: #3b82f6   600: #2563eb   700: #1d4ed8
800: #1e40af   900: #1e3a8a   950: #172554
```

**Verde (saúde, fintech, sustentabilidade):**
```
50: #f0fdf4   100: #dcfce7   200: #bbf7d0   300: #86efac
400: #4ade80   500: #22c55e   600: #16a34a   700: #15803d
800: #166534   900: #14532d   950: #052e16
```

**Roxo (criativo, premium):**
```
50: #faf5ff   100: #f3e8ff   200: #e9d5ff   300: #d8b4fe
400: #c084fc   500: #a855f7   600: #9333ea   700: #7e22ce
800: #6b21a8   900: #581c87   950: #3b0764
```

**Vermelho (caution, food, energia):**
```
50: #fef2f2   100: #fee2e2   200: #fecaca   300: #fca5a5
400: #f87171   500: #ef4444   600: #dc2626   700: #b91c1c
800: #991b1b   900: #7f1d1d   950: #450a0a
```

**Laranja (energia, alerta amigável):**
```
50: #fff7ed   100: #ffedd5   200: #fed7aa   300: #fdba74
400: #fb923c   500: #f97316   600: #ea580c   700: #c2410c
800: #9a3412   900: #7c2d12   950: #431407
```

**Âmbar (warning, ouro, premium):**
```
50: #fffbeb   100: #fef3c7   200: #fde68a   300: #fcd34d
400: #fbbf24   500: #f59e0b   600: #d97706   700: #b45309
800: #92400e   900: #78350f   950: #451a03
```

### 4.3 Feedback palette canônica

```json
{
  "feedback": {
    "success": {
      "subtle":  "#d1fae5",
      "default": "#10b981",
      "strong":  "#047857",
      "background": "#f0fdf4"
    },
    "warning": {
      "subtle":  "#fef3c7",
      "default": "#f59e0b",
      "strong":  "#92400e",
      "background": "#fffbeb"
    },
    "danger": {
      "subtle":  "#fecaca",
      "default": "#ef4444",
      "strong":  "#991b1b",
      "background": "#fef2f2"
    },
    "info": {
      "subtle":  "#bfdbfe",
      "default": "#3b82f6",
      "strong":  "#1e40af",
      "background": "#eff6ff"
    }
  }
}
```

---

## 5. Acessibilidade WCAG

### 5.1 Tabela de requisitos

| Conteúdo | Mínimo (WCAG AA) | Recomendado (AAA) |
|---|---|---|
| Body text (<18pt regular) | **4.5:1** | 7:1 |
| Texto grande (18pt+ ou 14pt bold+) | **3:1** | 4.5:1 |
| UI components (border, ícones, controls) | **3:1** | — |
| Estados (focus, hover) vs não-estado | **3:1** | — |
| Decorativos (sem informação) | sem mínimo | — |

### 5.2 Como calcular contraste

Fórmula WCAG 2.1:

```
L1 = (R1 * 0.2126) + (G1 * 0.7152) + (B1 * 0.0722)  [cor mais clara]
L2 = (R2 * 0.2126) + (G2 * 0.7152) + (B2 * 0.0722)  [cor mais escura]

contrast = (L1 + 0.05) / (L2 + 0.05)
```

R, G, B são os componentes lineares (com correção gamma).

**Não calcule à mão.** Use ferramenta:

- WebAIM Contrast Checker (web)
- axe DevTools (browser extension)
- Stark plugin (Figma)
- Tailwind palette generator (web)

### 5.3 Combinações pré-validadas (Tailwind)

| Background | Text | Contrast | Status |
|---|---|---|---|
| `white` (#fff) | `slate-900` (#0f172a) | 19.4:1 | ✓ AAA |
| `white` (#fff) | `slate-700` (#334155) | 9.3:1 | ✓ AAA |
| `white` (#fff) | `slate-600` (#475569) | 7.0:1 | ✓ AAA body |
| `white` (#fff) | `slate-500` (#64748b) | 4.6:1 | ✓ AA body |
| `white` (#fff) | `slate-400` (#94a3b8) | 3.0:1 | ✗ AA body, ✓ large |
| `slate-50` (#f8fafc) | `slate-900` | 18.2:1 | ✓ AAA |
| `slate-100` (#f1f5f9) | `slate-900` | 16.6:1 | ✓ AAA |

| Background | Text | Contrast | Status |
|---|---|---|---|
| `slate-900` (dark) | `white` | 19.4:1 | ✓ AAA |
| `slate-900` | `slate-200` (#e2e8f0) | 13.2:1 | ✓ AAA |
| `slate-900` | `slate-400` (#94a3b8) | 5.0:1 | ✓ AA body |
| `slate-900` | `slate-500` | 3.6:1 | ✗ body, ✓ large |

### 5.4 Brand contrast (cores não-cinza)

| Brand | vs white | vs slate-900 | Recomendação |
|---|---|---|---|
| `blue-500` (#3b82f6) | 4.0:1 | 4.9:1 | OK em white para large/UI, dark mode usa blue-400 |
| `blue-600` (#2563eb) | 5.2:1 | 3.7:1 | ✓ body em white |
| `green-500` (#22c55e) | 2.8:1 | 7.0:1 | NÃO usar em white, ✓ dark |
| `green-600` (#16a34a) | 3.8:1 | 5.1:1 | ✓ large/UI em white |
| `red-500` (#ef4444) | 4.0:1 | 4.9:1 | ✓ large em white |
| `red-600` (#dc2626) | 5.0:1 | 3.9:1 | ✓ body em white |
| `yellow-500` (#eab308) | 1.9:1 | 10.4:1 | NÃO usar em white, ✓ dark |
| `amber-600` (#d97706) | 3.4:1 | 5.7:1 | ✓ large em white |

**Regra prática:** se for usar cor em texto body sobre branco, use tom **600 ou maior**.

---

## 6. Daltonismo

### 6.1 Estatísticas

- **8% dos homens** têm algum tipo de daltonismo
- **0.5% das mulheres**
- Tipos: deuteranopia (~5%), protanopia (~1%), tritanopia (raro)

### 6.2 Regra fundamental

**NUNCA codificar informação só por cor.**

```
❌ "Linhas em vermelho são pendentes, em verde estão pagas"
✅ "Pendentes: ⚠ vermelho. Pagas: ✓ verde."

❌ Status badges só com cor de fundo
✅ Status badges com cor + ícone + texto
```

### 6.3 Paletas safe para daltônicos

**Combinações que daltônicos distinguem:**

```
Azul + Laranja:
  Blue-600 (#2563eb) + Orange-600 (#ea580c)

Roxo + Amarelo:
  Purple-600 (#9333ea) + Amber-500 (#f59e0b)

Azul-claro + Vermelho-escuro:
  Sky-400 (#38bdf8) + Red-700 (#b91c1c)
```

**Combinações problemáticas (evitar):**

```
❌ Verde + Vermelho (deuteranopia confunde)
❌ Verde + Marrom
❌ Azul + Roxo (em tons próximos)
```

### 6.4 Validação

Ferramentas:
- Sim Daltonism (Mac, free)
- Stark plugin (Figma)
- Chrome DevTools > Rendering > Emulate vision deficiencies

**Teste prático:** dar print da UI, abrir em Photoshop, aplicar filtro de daltonismo (Image > Adjustments > Hue/Saturation > Saturation -100). Se ainda dá pra ler informação, tá ok.

---

## 7. Dark mode

### 7.1 Approach: token swap automático

Tokens semânticos têm valor `light` e `dark`. CSS variables trocam baseado em `prefers-color-scheme` ou `[data-theme="dark"]`.

```css
:root {
  /* light mode default */
  --color-text-primary: #0f172a;     /* slate-900 */
  --color-text-secondary: #475569;   /* slate-600 */
  --color-surface-default: #ffffff;
  --color-surface-raised: #ffffff;
  --color-surface-sunken: #f8fafc;   /* slate-50 */
  --color-border-default: #e2e8f0;   /* slate-200 */
  --color-brand-primary: #2563eb;    /* blue-600 */
}

[data-theme="dark"] {
  --color-text-primary: #f8fafc;     /* slate-50 */
  --color-text-secondary: #94a3b8;   /* slate-400 */
  --color-surface-default: #0f172a;  /* slate-900 */
  --color-surface-raised: #1e293b;   /* slate-800 */
  --color-surface-sunken: #020617;   /* slate-950 */
  --color-border-default: #334155;   /* slate-700 */
  --color-brand-primary: #60a5fa;    /* blue-400 (mais claro pra contraste) */
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    /* respeita preferência do sistema */
    --color-text-primary: #f8fafc;
    /* ... */
  }
}
```

### 7.2 Regras importantes

**1. Brand color muda escala em dark mode**

Cor brand-500 que funcionava em white pode não funcionar em slate-900.

```
Light: brand-primary = blue-600 (escuro contra fundo claro)
Dark:  brand-primary = blue-400 (claro contra fundo escuro)
```

**2. Surface "raised" não é mais branco em dark**

```
Light:
  surface-default = white
  surface-raised  = white (sombra cria elevação)
  surface-sunken  = slate-50

Dark:
  surface-default = slate-900
  surface-raised  = slate-800 (mais claro = elevado)
  surface-sunken  = slate-950 (mais escuro = afundado)
```

**3. Dark mode NÃO é só inverter cores**

```
❌ Inverter background = #fff → #000 e text = #000 → #fff
   Resultado: contraste 21:1 (cansa olho)

✅ Background = slate-900 (#0f172a, não preto puro)
   Text = slate-50 (#f8fafc, não branco puro)
   Contraste = 18.2:1 (forte mas não brutal)
```

**4. Imagens precisam de tratamento**

```css
[data-theme="dark"] img {
  /* Reduzir luminância de imagens claras */
  filter: brightness(0.85);
}
```

### 7.3 Toggle de tema

Sempre oferecer 3 opções (não só 2):

```
○ Light
○ Dark
● System (default — segue OS)
```

Persistir em localStorage. Aplicar via JS no boot:

```javascript
const theme = localStorage.getItem('theme') || 'system';
if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.setAttribute('data-theme', 'dark');
}
```

---

## 8. Naming conventions

### 8.1 Estrutura

```
{category}.{property}.{variant}.{state}
```

Exemplos:
- `color.brand.primary` (categoria: color, property: brand, variant: primary)
- `color.text.primary.disabled` (com estado)
- `color.feedback.success.background`
- `color.surface.raised.dark` (com tema)

### 8.2 Regras

✅ **Singular** sempre: `color`, não `colors`
✅ **Genérico → específico:** `text-primary`, não `primary-text`
✅ **Estado por último:** `text-primary-disabled`
✅ **kebab-case** consistente em todo arquivo
✅ **Semântica antes de cor:** `feedback-danger` em vez de `red`

❌ **Cores literais em nome:** `azul-bonito`, `red-from-figma`
❌ **Aninhamento profundo (>4):** `theme.dark.color.text.primary.hover.disabled.icon`
❌ **Mistura de convenções:** `colorPrimary` + `text_primary` no mesmo arquivo
❌ **Numerais arbitrários:** `color1`, `color2` (use semântico)

### 8.3 Exemplo completo de nomeação

```
color.brand.primary             ✅
color.brand.primary-hover       ✅
color.brand.primary-active      ✅

color.text.primary              ✅
color.text.secondary            ✅
color.text.disabled             ✅

color.surface.default           ✅
color.surface.raised            ✅
color.surface.sunken            ✅
color.surface.overlay           ✅

color.border.default            ✅
color.border.strong             ✅
color.border.focus              ✅

color.feedback.success          ✅
color.feedback.success.subtle   ✅
color.feedback.success.background ✅

color.azul-claro                ❌ (usar tom semântico)
color.brandColor                ❌ (camelCase inconsistente)
color1                          ❌ (numérico arbitrário)
```

---

## 9. Implementação completa (CSS + tokens.json)

### 9.1 tokens.json (mínimo viável)

```json
{
  "_meta": {
    "version": "1.0.0",
    "mode": "final",
    "last_updated": "2026-04-29"
  },
  "color": {
    "blue": {
      "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe",
      "300": "#93c5fd", "400": "#60a5fa", "500": "#3b82f6",
      "600": "#2563eb", "700": "#1d4ed8", "800": "#1e40af",
      "900": "#1e3a8a", "950": "#172554"
    },
    "slate": {
      "50": "#f8fafc", "100": "#f1f5f9", "200": "#e2e8f0",
      "300": "#cbd5e1", "400": "#94a3b8", "500": "#64748b",
      "600": "#475569", "700": "#334155", "800": "#1e293b",
      "900": "#0f172a", "950": "#020617"
    }
  },
  "_semantic": {
    "color": {
      "brand": {
        "primary": { "light": "{color.blue.600}", "dark": "{color.blue.400}" },
        "primary-hover": { "light": "{color.blue.700}", "dark": "{color.blue.300}" }
      },
      "text": {
        "primary":   { "light": "{color.slate.900}", "dark": "{color.slate.50}" },
        "secondary": { "light": "{color.slate.600}", "dark": "{color.slate.400}" },
        "disabled":  { "light": "{color.slate.400}", "dark": "{color.slate.600}" }
      },
      "surface": {
        "default": { "light": "{color.white}",      "dark": "{color.slate.900}" },
        "raised":  { "light": "{color.white}",      "dark": "{color.slate.800}" },
        "sunken":  { "light": "{color.slate.50}",   "dark": "{color.slate.950}" }
      },
      "border": {
        "default": { "light": "{color.slate.200}",  "dark": "{color.slate.700}" },
        "focus":   { "light": "{color.blue.600}",   "dark": "{color.blue.400}" }
      }
    }
  }
}
```

### 9.2 CSS (gerado de tokens)

```css
:root {
  /* Primitives */
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --slate-50: #f8fafc;
  --slate-200: #e2e8f0;
  --slate-600: #475569;
  --slate-900: #0f172a;
  /* ... */

  /* Semantic light */
  --color-brand-primary: var(--blue-600);
  --color-brand-primary-hover: #1d4ed8;
  --color-text-primary: var(--slate-900);
  --color-text-secondary: var(--slate-600);
  --color-text-disabled: #94a3b8;
  --color-surface-default: #ffffff;
  --color-surface-raised: #ffffff;
  --color-surface-sunken: var(--slate-50);
  --color-border-default: var(--slate-200);
  --color-border-focus: var(--blue-600);
}

[data-theme="dark"] {
  --color-brand-primary: #60a5fa;
  --color-brand-primary-hover: #93c5fd;
  --color-text-primary: var(--slate-50);
  --color-text-secondary: #94a3b8;
  --color-text-disabled: #475569;
  --color-surface-default: var(--slate-900);
  --color-surface-raised: #1e293b;
  --color-surface-sunken: #020617;
  --color-border-default: #334155;
  --color-border-focus: #60a5fa;
}
```

### 9.3 Uso em componente

```css
.button-primary {
  background: var(--color-brand-primary);
  color: white;
  border: none;
}

.button-primary:hover {
  background: var(--color-brand-primary-hover);
}

.card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-default);
  color: var(--color-text-primary);
}

.card-title {
  color: var(--color-text-primary);
}

.card-description {
  color: var(--color-text-secondary);
}
```

---

## 10. Anti-patterns com correção

### Anti-pattern 1: Cores hardcoded em código

```css
/* ❌ ERRADO */
.button { background: #3b82f6; color: white; }

/* ✅ CORRETO */
.button {
  background: var(--color-brand-primary);
  color: var(--color-text-inverse);
}
```

### Anti-pattern 2: Componentes usando primitivos diretos

```css
/* ❌ ERRADO (primitivo direto) */
.card-title { color: var(--slate-900); }

/* ✅ CORRETO (semântico) */
.card-title { color: var(--color-text-primary); }
```

Por quê: se precisar mudar cor de texto primário em todo o app, muda só 1 linha (semântico). Se hardcoded, busca-e-substitui em 200 lugares.

### Anti-pattern 3: Status só por cor

```html
<!-- ❌ ERRADO -->
<span class="badge bg-red">Pendente</span>
<span class="badge bg-green">Pago</span>

<!-- ✅ CORRETO -->
<span class="badge bg-red">⏱ Pendente</span>
<span class="badge bg-green">✓ Pago</span>
```

### Anti-pattern 4: Dark mode adicionado depois

```css
/* ❌ ERRADO — escreve light, depois "ah, dark mode também" */
.card { background: white; }
[data-theme="dark"] .card { background: black; }
[data-theme="dark"] .card .title { /* mais 50 overrides */ }

/* ✅ CORRETO — sempre via token semântico */
.card { background: var(--color-surface-raised); }
.card .title { color: var(--color-text-primary); }
/* dark mode "funciona automaticamente" via tokens */
```

### Anti-pattern 5: Brand muito vibrante em texto body

```css
/* ❌ ERRADO — brand-500 puro em texto longo cansa olho */
.help-text { color: #3b82f6; font-size: 14px; }

/* ✅ CORRETO — texto de apoio em cinza, brand só em links/ações */
.help-text { color: var(--color-text-secondary); }
.help-text a { color: var(--color-brand-primary); }
```

### Anti-pattern 6: Verde + vermelho próximos sem ícone

```html
<!-- ❌ ERRADO (daltônicos não distinguem) -->
<span class="text-green-500">✓ Concluído</span>
<span class="text-red-500">✗ Erro</span>

<!-- ✅ CORRETO -->
<span class="text-green-700"><CheckIcon /> Concluído</span>
<span class="text-red-700"><XIcon /> Erro</span>
```

(Tons mais escuros + ícones diferentes.)

### Anti-pattern 7: Branco puro como background dark mode

```css
/* ❌ ERRADO */
[data-theme="dark"] body {
  background: #000;     /* preto puro = brutal */
  color: #fff;          /* branco puro = brutal */
}
/* Contraste 21:1 — cansa olho */

/* ✅ CORRETO */
[data-theme="dark"] body {
  background: #0f172a;  /* slate-900 */
  color: #f8fafc;       /* slate-50 */
}
/* Contraste 18.2:1 — confortável */
```

---

## 11. Casos práticos por contexto

### 11.1 SaaS B2B (admin dashboard)

```
Brand: blue-600 (autoridade, confiança)
Neutral: slate (cinza levemente azulado, sofisticado)
Feedback: green/yellow/red padrão
Background light: white
Background dark: slate-900
Density: alta (muita info, espaço apertado)
```

### 11.2 B2C app (consumer)

```
Brand: cor mais saturada (purple, orange, pink)
Neutral: stone (cinza warm)
Feedback: cores mais vibrantes (success em emerald-500)
Background light: white ou off-white (#fafafa)
Background dark: slate-950 (mais profundo)
Density: baixa (espaço generoso)
```

### 11.3 Fintech (banco, payments)

```
Brand: azul ou verde-escuro (confiança institucional)
Neutral: slate-700 a slate-900 (conservador)
Feedback: vermelho restrito (só para danger real)
Tom: contido, não vibrante
Não usar: amarelo (impressão de aviso/dívida)
```

### 11.4 Health/medical

```
Brand: teal-500 ou green-500 (saúde, calma)
Neutral: stone (warm, humano)
Feedback: cores mais suaves (success-subtle como background)
Não usar: red-500 puro (paciente em estado de saúde lê como "morte")
Use: red-700 ou orange-600 quando precisar de alerta
```

### 11.5 Áugure (validação de mercado)

```
Brand: indigo-600 (#4f46e5) (decisão racional, calibrado)
Neutral: slate (cinza azulado, profissional)
Feedback:
  - success (decisão favorável): emerald-600
  - danger (não recomendado investir): red-700 (não 500, muito alarmante)
  - warning (cenário misto): amber-600
  - info (dado adicional): blue-600
Background light: white
Background dark: slate-950 (premium look)
```

---

## 12. Ferramentas

### 12.1 Geração de paleta

- **Tailwind palette generator** (uicolors.app) — gera escala 50-950
- **Radix Colors** (radix-ui.com/colors) — escalas com semântica
- **Realtime Colors** (realtimecolors.com) — testa em UI live
- **Color Hunt** (colorhunt.co) — paletas curadas

### 12.2 Validação

- **WebAIM Contrast Checker** — texto vs background
- **Stark plugin (Figma)** — contraste + daltonismo
- **axe DevTools** (browser extension) — audit completo
- **Chrome DevTools > Rendering > Emulate vision** — daltonismo

### 12.3 Conversão

- **Coolors** — gera paletas, converte hex/rgb/hsl
- **Color Designer** (colordesigner.io) — ferramenta avançada

### 12.4 Ferramentas de tokens

- **Style Dictionary** (Amazon) — gera CSS/SCSS/iOS/Android de JSON
- **Theo** (Salesforce) — similar
- **Tokens Studio** — plugin Figma → tokens.json
- **Specify** — design tokens platform

---

## 13. Checklist de validação

```
□ tokens.json existe em docs/identidade-visual/
□ 3 camadas implementadas (primitive, semantic, component)?
□ Naming conventions seguidas (kebab-case, semântico)?
□ Brand color tem escala 50-950?
□ Neutral color tem escala 50-950?
□ Feedback colors (success, warning, danger, info) definidas?
□ Surface tokens (default, raised, sunken)?
□ Border tokens (default, focus, strong)?
□ Text tokens (primary, secondary, disabled)?

□ Contraste validado WCAG AA?
  - Body text vs background ≥ 4.5:1
  - Large text vs background ≥ 3:1
  - UI components ≥ 3:1
  - Focus states ≥ 3:1

□ Daltonismo testado?
  - Status NÃO depende só de cor
  - Combinação azul/laranja preferida sobre verde/vermelho

□ Dark mode implementado?
  - Token semântico tem light + dark
  - Surface raised vs default visualmente distinguível
  - Brand color ajustado para dark mode

□ Componentes usam tokens semânticos (não primitivos)?
□ Zero cores hardcoded em código (audit grep "#")?
□ Toggle de tema oferece 3 opções (light/dark/system)?
□ tokens.json tem _meta com version e last_updated?
```

Se <15 checks, sistema é incompleto. Volte para a seção correspondente.

---

## 14. Como aplicar em projeto existente (migração)

### 14.1 Auditar estado atual

```bash
# Quantas cores hardcoded existem?
grep -rE "#[0-9a-fA-F]{3,6}" src/ --include="*.css" --include="*.scss" | wc -l

# Quantas variáveis CSS já existem?
grep -rE "var\(--" src/ | wc -l
```

Resultado típico de projeto sem sistema: 200-500 cores hardcoded.

### 14.2 Plano de migração (3 passos)

**Passo 1 (1 dia):** criar tokens.json + CSS variables (camadas 1 e 2). Não altera UI.

**Passo 2 (3-5 dias):** migrar componente por componente do hardcoded para token. Começar pelos mais usados (Button, Input, Card).

**Passo 3 (2 dias):** adicionar dark mode. Por usar tokens semânticos, "funciona automaticamente".

### 14.3 Como evitar regressão

```css
/* ESLint rule (stylelint) */
{
  "rules": {
    "color-no-hex": true,         /* proíbe #fff em CSS novo */
    "declaration-property-value-allowed-list": {
      "color": [/^var\(--/],     /* só var(--) é permitido */
      "background": [/^var\(--/, "transparent", "none"]
    }
  }
}
```

---

## 15. Como integra com outras skills

### 15.1 → `quality/design-token-architecture`

Color é UMA das categorias de tokens. Architecture define hierarquia geral, color-system define cores especificamente.

### 15.2 → `quality/accessibility-pro`

Color é input para audit WCAG. Accessibility audit checa contrastes definidos aqui.

### 15.3 → `ux-advanced/dark-mode-theming`

Color-system define os 2 conjuntos de tokens (light + dark). Dark-mode-theming implementa o toggle e persistência.

### 15.4 → `ui-ux-pro-max`

Skill matriz cita color-system para decisões estéticas (cinza com tom vs cinza puro, brand vibrante vs sutil).

### 15.5 → PLAN.md de phase com UI

```markdown
## Phase 4 — Refactor de header

### Skills Consultadas
- `quality/color-system` — usar tokens semânticos (não hardcoded)
- `quality/accessibility-pro` — validar contraste no header (logo + nav links)
```

---

## 16. Erros comuns

### Erro 1: "Vamos definir cor depois"
Resultado: 6 meses depois, 300 hex codes diferentes em produção. Migração custa 1 mês.
**Fix:** definir tokens no /gsd-bootstrap, antes da primeira phase com UI.

### Erro 2: "Designer escolhe, dev implementa"
Designer envia hex no Figma, dev cola hex no CSS. Sem sistema.
**Fix:** designer entrega tokens.json (via Tokens Studio plugin Figma).

### Erro 3: Dark mode tardio
Adicionar dark mode em projeto de 2 anos sem tokens = 1-3 meses de trabalho.
**Fix:** desde o dia 1, tokens com light + dark, mesmo se dark for "futuro".

### Erro 4: Sem audit WCAG
Lançar produto que reprova em audit (caso comum: branco em amarelo, brand vibrante em texto).
**Fix:** rodar axe ou Stark antes do release. Bloqueia merge se reprovar.

---

## 17. Referências

- **WCAG 2.1 Color Contrast** — w3.org/TR/WCAG21
- **Refactoring UI** (Adam Wathan, Steve Schoger) — capítulo de cor
- **Material Design Color System** — material.io/design/color
- **Radix Colors documentation** — radix-ui.com/colors
- **Tailwind CSS palette** — tailwindcss.com/docs/customizing-colors
- **A11y Project** — color contrast guides

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 17 seções, 6 paletas hex prontas, dark mode completo, anti-patterns com correção, 5 contextos de uso, ferramentas, checklist de 18 itens
