---
name: refactoring-ui
category: meta
description: Princípios práticos de Refactoring UI (Wathan & Schoger) condensados em regras operacionais para devs sem designer. Cobre personalidade, hierarquia visual, cores, tipografia, espaço, sombras, formas. Inclui anti-patterns AI-slop com correção lado a lado, antes/depois de UIs reais, e checklist de validação para audit anti-amador.
---

# Refactoring UI — Princípios Práticos

> Adaptado de Adam Wathan e Steve Schoger. UI que parece feita por designer, não por dev.

Esta skill é para projetos sem designer dedicado. Substitui "intuição estética" por regras concretas.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-ui-phase` em projeto sem designer | Dev é o designer, precisa de guia |
| Refactor de UI "amadora" | Migrar de Bootstrap genérico para algo profissional |
| Após `quality/heuristic-evaluation` indicar problemas estéticos | Aplicar correções |
| `/gsd-verify-work` quando UI parece "AI slop" (genérica, plana) | Audit anti-amador |
| Antes de release com público externo | Última polida estética |

## 2. Quando NÃO usar

- Projeto com designer dedicado (designer manda)
- Phase backend
- Refactor técnico interno

---

## 3. Os 7 princípios essenciais

### Princípio 1 — Comece com personalidade

UI sem personalidade = invisível. Personalidade vem de:

| Elemento | Decisão concreta |
|---|---|
| **Cor brand** | 1 cor saturada (não pastel), específica do produto |
| **Tipografia** | 1 fonte com personalidade (não Arial/Helvetica) |
| **Forma** | Cantos arredondados consistentes (4px / 8px / 12px — escolha um) |
| **Densidade** | Muito espaço = limpo, denso = profissional. Decisão intencional |
| **Tom de voz** | Formal? Casual? Tem que estar em copy E visual |

**Decisões iniciais (escolha uma de cada para seu projeto):**

```yaml
personalidade:
  cor_brand: "blue-600 (#2563eb)"  # ou outra, mas UMA
  fonte_display: "Inter"            # ou Cal Sans, Manrope, Geist
  fonte_body: "Inter"               # geralmente mesma família
  radius_padrao: "8px"              # 4 (afiado), 8 (moderno), 12 (friendly)
  densidade: "balanced"             # compact, balanced, generous
  tom: "profissional acessível"     # formal, casual, brincalhão
```

**Anti-pattern:** design "neutro" que parece template Bootstrap = invisível.

### Princípio 2 — Hierarquia > tamanho

Tamanho NÃO é a única ferramenta de hierarquia. Use:

| Ferramenta | Como aplicar |
|---|---|
| **Cor** | Texto primário = preto/cinza-900. Secundário = cinza-600. Terciário = cinza-400 |
| **Peso** | Bold/semibold para destacar, regular para apoio |
| **Posição** | Topo = mais importante. À esquerda em LTR |
| **Espaço** | Mais espaço ao redor = mais importante |
| **Tamanho** | Última opção, não primeira |

**Exemplo errado vs correto:**

```css
/* ❌ ERRADO — só usa tamanho */
h1 { font-size: 40px; }
p { font-size: 16px; }
small { font-size: 10px; }

/* ✅ CORRETO — combina cor + peso + tamanho */
h1 {
  font-size: 30px;        /* maior, mas não 40 */
  font-weight: 700;       /* bold */
  color: var(--text-primary);
}
p {
  font-size: 16px;
  color: var(--text-primary);
}
.help-text {
  font-size: 14px;
  color: var(--text-secondary);  /* cinza médio */
}
```

### Princípio 3 — Cinza puro mata UI

Cinza puro (#888888) é morto. Use cinza com leve tom da brand.

```
Brand azul → use slate (cinza azulado)
Brand verde → use stone com leve tom verde
Brand vermelho/laranja → use stone (cinza warm)
Brand roxo → use slate ou neutral
```

**Exemplo:**

```css
/* ❌ ERRADO — cinza puro */
.text-secondary { color: #888888; }
.border { border-color: #cccccc; }

/* ✅ CORRETO — cinza com tom */
:root {
  --slate-500: #64748b;  /* tom azulado */
  --slate-300: #cbd5e1;
}
.text-secondary { color: var(--slate-500); }
.border { border-color: var(--slate-300); }
```

### Princípio 4 — Cores saturadas + dessaturadas, não 50/50

```
✅ Brand vibrante (saturação alta) + neutros próximos a cinza
❌ Tudo médio saturado (compete entre si)
```

**Regra:** 1 cor vibrante (CTA, brand). Resto sutil.

**Exemplo:**

```
✅ CORRETO:
- Brand: blue-600 (saturado, vibrante) — usado em CTA primária
- Texto: slate-900 (cinza escuro)
- Background: white
- Apoio: slate-100, slate-200 (cinzas claros)
- Sucesso: green-600 (vibrante, mas só em badges)

❌ ERRADO:
- Brand: pink-300 (pastel)
- Sucesso: green-300 (pastel)
- Erro: red-300 (pastel)
- Background: yellow-50 (pastel)
→ Tudo igualmente sutil = nada destaca
```

### Princípio 5 — Imagens precisam de elevação

Imagem em fundo branco sem borda = "flutuando", parece amador.

```css
/* ❌ ERRADO */
img { display: block; }

/* ✅ CORRETO — opção 1: sombra sutil */
img {
  display: block;
  border-radius: 8px;
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 8px rgba(0,0,0,0.06);
}

/* ✅ CORRETO — opção 2: borda */
img {
  display: block;
  border-radius: 8px;
  border: 1px solid var(--color-border-default);
}

/* ✅ CORRETO — opção 3: container */
.image-container {
  background: var(--color-surface-sunken);
  padding: 4px;
  border-radius: 12px;
}
.image-container img {
  border-radius: 8px;
}
```

### Princípio 6 — Branco é estrutura, não vazio

Mais espaço = mais profissional.

| Densidade | Padding container | Espaço entre seções | Quando usar |
|---|---|---|---|
| Compact | 16px | 24px | Dashboards admin, dense data |
| Balanced | 32px | 48px | SaaS típico (default) |
| Generous | 48-64px | 80-128px | Marketing pages, premium products |

**Inspiração:** Stripe, Linear, Apple — sites profissionais têm muito ar.

```css
/* ❌ ERRADO — apertado */
.card { padding: 8px; }
.card + .card { margin-top: 8px; }
section + section { margin-top: 16px; }

/* ✅ CORRETO — balanced */
.card { padding: 24px; }
.card + .card { margin-top: 16px; }
section + section { margin-top: 64px; }

/* ✅ CORRETO — generous (landing page) */
.hero { padding: 96px 32px; }
section + section { margin-top: 128px; }
```

### Princípio 7 — Imagens > ícones > texto (em hierarquia visual)

Para CTAs e moments de impacto:

```
1 imagem grande > 1 ícone grande > texto bold > texto regular
```

**Aplicação:**

```html
<!-- ✅ Hero com imagem como anchor -->
<section class="hero">
  <img src="dashboard-screenshot.png" />  <!-- ícone visual primário -->
  <h1>Validar ideia em 15 min</h1>
  <p>Sem chute. Com dado.</p>
  <button>Começar grátis</button>
</section>

<!-- ✅ Empty state com ícone como anchor -->
<div class="empty-state">
  <InboxIcon size="64" />  <!-- chama atenção -->
  <h3>Sem pedidos ainda</h3>
  <p>Quando você receber pedidos, eles aparecerão aqui.</p>
  <button>Compartilhar link</button>
</div>
```

---

## 4. Truques específicos (que fazem diferença)

### 4.1 Sombras realistas (camadas)

Sombras planas parecem fake. Sombras reais têm camadas.

```css
/* ❌ ERRADO — sombra plana */
.card {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* ✅ CORRETO — sombra com camadas */
.card-sm {
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 1px 3px rgba(0,0,0,0.06);
}
.card-md {
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 8px rgba(0,0,0,0.06),
    0 2px 4px rgba(0,0,0,0.04);
}
.card-lg {
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 8px 16px rgba(0,0,0,0.08),
    0 4px 8px rgba(0,0,0,0.06);
}
.card-xl {
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 12px 24px rgba(0,0,0,0.10),
    0 8px 16px rgba(0,0,0,0.06);
}
```

### 4.2 Cores em estados

NÃO use opacity para hover. Use cor mais escura.

```css
/* ❌ ERRADO — opacity */
.button-primary { background: #3b82f6; }
.button-primary:hover { opacity: 0.8; }  /* parece desbotado */

/* ✅ CORRETO — cor mais escura */
.button-primary { background: var(--blue-500); }
.button-primary:hover { background: var(--blue-600); }
.button-primary:active { background: var(--blue-700); }
.button-primary:disabled {
  background: var(--blue-200);  /* mais claro = menos importante */
  color: var(--blue-400);
  cursor: not-allowed;
}
```

### 4.3 Form fields elegantes

```css
/* ❌ ERRADO — border preto grosso (amador) */
input {
  border: 2px solid black;
  padding: 8px;
}

/* ❌ ERRADO — sem border (some visualmente) */
input {
  border: none;
  background: white;
}

/* ✅ CORRETO */
input {
  border: 1px solid var(--slate-300);          /* sutil */
  border-radius: 8px;
  padding: 12px 16px;
  background: white;
  transition: border-color 150ms;
}
input:hover {
  border-color: var(--slate-400);
}
input:focus {
  outline: none;
  border-color: var(--blue-600);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);  /* glow leve */
}
input:invalid {
  border-color: var(--red-500);
}
```

### 4.4 Botões consistentes

```css
/* Base — todos os botões compartilham */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  height: 40px;                /* altura consistente */
  border-radius: 8px;          /* radius consistente */
  font-weight: 500;
  font-size: 14px;
  transition: all 150ms;
  cursor: pointer;
}

/* Variantes */
.btn-primary {
  background: var(--blue-600);
  color: white;
  border: 1px solid transparent;
}
.btn-primary:hover { background: var(--blue-700); }

.btn-secondary {
  background: white;
  color: var(--slate-900);
  border: 1px solid var(--slate-300);
}
.btn-secondary:hover {
  background: var(--slate-50);
  border-color: var(--slate-400);
}

.btn-ghost {
  background: transparent;
  color: var(--slate-700);
  border: 1px solid transparent;
}
.btn-ghost:hover {
  background: var(--slate-100);
}

/* Tamanhos */
.btn-sm { height: 32px; padding: 0 12px; font-size: 13px; }
.btn-lg { height: 48px; padding: 0 24px; font-size: 16px; }
```

### 4.5 Cards profissionais

```css
.card {
  background: var(--color-surface-default);
  border: 1px solid var(--color-border-default);  /* sutil */
  border-radius: 12px;
  padding: 24px;
  /* SEM sombra default — sombra só em hover ou em cards especiais */
}

.card-interactive:hover {
  border-color: var(--slate-300);
  box-shadow:
    0 4px 8px rgba(0,0,0,0.04),
    0 2px 4px rgba(0,0,0,0.02);
  transform: translateY(-1px);  /* sutil lift */
}

.card-elevated {
  border: none;
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 8px rgba(0,0,0,0.06);
}
```

### 4.6 Tipografia que respira

```css
/* ❌ ERRADO — line-height padrão (1.0) */
h1 { font-size: 32px; line-height: 1; }

/* ✅ CORRETO — line-height contextual */
h1 {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;        /* tight para títulos */
  letter-spacing: -0.02em; /* negativo para tamanhos grandes */
  color: var(--text-primary);
}

p {
  font-size: 16px;
  line-height: 1.6;        /* generoso para body */
  color: var(--text-primary);
}

.help-text {
  font-size: 13px;
  line-height: 1.5;
  letter-spacing: 0.01em;  /* positivo para tamanhos pequenos */
  color: var(--text-secondary);
}
```

---

## 5. Anti-patterns "AI Slop"

UI gerada por IA (ChatGPT, v0, Bolt) tende a ter estes problemas. Como evitar:

### Anti-pattern 1: "Tudo igualmente bonito"

```
❌ ERRADO:
- Todo botão é gradient
- Todo card tem sombra grande
- Toda imagem tem border-radius enorme
- Todo texto é bold ou semi-bold

✅ CORRETO:
- Hierarquia: 1 elemento primário por tela
- Sombras ESCALONADAS por importância (sm, md, lg)
- Apenas headings em bold, body em regular
- Cards default sem sombra; sombra só em hover ou elevados
```

### Anti-pattern 2: Gradients em tudo

```
❌ ERRADO:
- Botão primário: gradient azul→roxo
- Card: gradient sutil
- Background: gradient
- Hero: gradient

✅ CORRETO:
- Cor sólida em 95% dos lugares
- Gradient apenas em 1-2 elementos de destaque (hero, CTA premium)
- Se usar gradient, MESMA família de cor (blue-500 → blue-600), não rainbow
```

### Anti-pattern 3: Cantos arredondados em tudo

```
❌ ERRADO:
- Container 1200px de largura: border-radius: 24px
- Card: border-radius: 16px
- Botão: border-radius: 12px
- Input: border-radius: 8px

✅ CORRETO:
- Containers grandes: border-radius pequeno (4-8px) ou zero
- Cards: 8-12px
- Botões: 6-10px
- Inputs: 6-10px
- Avatars/imagens: 8-12px ou círculo
- CONSISTÊNCIA: escolha 1 escala, todos múltiplos
```

### Anti-pattern 4: Múltiplas brand colors

```
❌ ERRADO:
- Brand 1: roxo
- Brand 2: rosa
- Brand 3: azul
- (cada tela usa uma diferente)

✅ CORRETO:
- 1 brand color principal (azul, por ex)
- Escala da brand (azul-500, azul-600, azul-700) para variações
- Outras cores APENAS para feedback (success/warning/danger/info)
```

### Anti-pattern 5: Texto Lorem Ipsum sem variação

```
❌ ERRADO:
"Lorem ipsum dolor sit amet, consectetur adipiscing elit."
"Lorem ipsum dolor sit amet, consectetur adipiscing elit."
(mesmo texto em todos os cards)

✅ CORRETO:
- Conteúdo real ou plausível
- Variação de tamanho (alguns títulos curtos, outros longos)
- Variação de status (3 ativos, 1 expirado, 2 pending)
- Real-world data (datas variadas, nomes reais)
```

### Anti-pattern 6: Tudo flat sem elevation

```
❌ ERRADO:
- Cards sem sombra, sem border
- Botões sem destaque visual
- Modais "flutuando" sem overlay

✅ CORRETO:
- Borders sutis em cards (1px slate-200)
- Sombras escalonadas para indicar elevação
- Modal com overlay escuro (rgba(0,0,0,0.5)) e sombra forte
```

### Anti-pattern 7: Espaçamentos iguais em tudo

```
❌ ERRADO:
- Tudo com padding 16px
- Tudo com gap 16px
- Tudo com margin 16px

✅ CORRETO:
- Hierarquia de espaços (4, 8, 12, 16, 24, 32, 48, 64, 96)
- Espaços relacionados a hierarquia (mais espaço = mais importante)
- Densidade adequada ao contexto
```

### Anti-pattern 8: Glassmorphism sem critério

```
❌ ERRADO:
- Backdrop-filter: blur em sidebars, modais, cards, toasts
- Tudo translúcido = nada destaca

✅ CORRETO:
- Glassmorphism em 1-2 lugares específicos (hero, nav fixo)
- Maioria dos componentes sólidos
- Quando usar, garantir contraste adequado (WCAG)
```

---

## 6. Antes/depois — UI real

### Caso 1: Tela de login

```
ANTES (AI slop):
┌────────────────────────────────────────┐
│  [Gradient azul→roxo full bleed]       │
│                                         │
│  ╔════════════════╗                    │
│  ║ ⚠ LOGO BIG     ║ (gradient texto)  │
│  ║ Bem-vindo!     ║                    │
│  ║ ┌────────────┐ ║ (input radius 24)  │
│  ║ │ email      │ ║                    │
│  ║ └────────────┘ ║                    │
│  ║ ┌────────────┐ ║                    │
│  ║ │ senha      │ ║                    │
│  ║ └────────────┘ ║                    │
│  ║ [GRADIENT BTN]║ (botão gradient)   │
│  ╚════════════════╝ (sombra exagerada) │
└────────────────────────────────────────┘

Problemas:
- Gradient em background + botão + logo (overload)
- Border-radius gigante (24px em input pequeno)
- Sombra exagerada no card
- Logo em gradient (ilegível)
- 3 elementos competindo por atenção

DEPOIS (refactored):
┌────────────────────────────────────────┐
│                                         │
│         [Logo simples]                  │
│                                         │
│         Entrar na conta                 │
│         Continue de onde parou          │
│                                         │
│         ┌──────────────────────┐       │
│         │ Email                 │       │
│         └──────────────────────┘       │
│                                         │
│         ┌──────────────────────┐       │
│         │ Senha     [esqueceu?]│       │
│         └──────────────────────┘       │
│                                         │
│         ┌──────────────────────┐       │
│         │       Entrar         │       │
│         └──────────────────────┘       │
│                                         │
│         Não tem conta? Cadastre-se     │
│                                         │
└────────────────────────────────────────┘

Mudanças:
- Background branco simples
- Logo PNG/SVG normal (sem gradient)
- Inputs com border 1px slate-300, radius 8px
- Botão primário sólido (sem gradient)
- Hierarquia clara: heading → form → CTA → secondary
- Espaços generosos
```

### Caso 2: Card de produto

```
ANTES (AI slop):
┌─────────────────────────────┐
│ [SOMBRA GIGANTE]            │
│ ╔═════════════════════════╗ │
│ ║ [imagem cantos 24px]    ║ │
│ ║                         ║ │
│ ║ ✨ Premium             ║ │ (badge gradient)
│ ║                         ║ │
│ ║ Título Bold Italic     ║ │
│ ║                         ║ │
│ ║ Descrição lorem ipsum  ║ │
│ ║                         ║ │
│ ║ R$ 99 [BIG GRADIENT BTN]║ │
│ ╚═════════════════════════╝ │
└─────────────────────────────┘

DEPOIS:
┌────────────────────────────┐
│ ┌────────────────────────┐ │
│ │ [imagem radius 8px]    │ │
│ └────────────────────────┘ │
│                             │
│ Premium                     │ (badge sutil)
│ Título do Produto          │ (heading regular)
│ Descrição em uma linha...  │ (text-secondary)
│                             │
│ R$ 99,00       [Comprar]   │ (botão primary normal)
└────────────────────────────┘

(border 1px slate-200, radius 12px, sem sombra)
```

---

## 7. Stack visual recomendada (decisões prontas)

Para projetos sem designer, **comece com este stack**:

```yaml
visual_stack:
  cor_brand: "blue-600 (#2563eb)"  # ou outra de quality/color-system
  fonte_display: "Inter"
  fonte_body: "Inter"
  fonte_size_base: "16px"
  fonte_scale_ratio: "1.2"
  radius_padrao: "8px"
  radius_pequeno: "6px"  # botões, inputs
  radius_grande: "12px"  # cards, modals
  sombra_padrao: "shadow-sm"
  sombra_hover: "shadow-md"
  sombra_modal: "shadow-xl"

  espaços:
    - 4px (xs)
    - 8px (sm)
    - 16px (md)
    - 24px (lg)
    - 32px (xl)
    - 48px (2xl)
    - 64px (3xl)

  cores_neutras: "slate"
  feedback:
    success: "emerald-600"
    warning: "amber-600"
    danger: "red-600"
    info: "blue-600"

  densidade_default: "balanced"
  motion_default: "150ms ease-out"
```

Implementar via tokens (vide `quality/color-system` e `quality/spacing-system`).

---

## 8. Checklist anti-AI-slop

Antes de declarar UI pronta:

```
PERSONALIDADE:
□ Cor brand específica e saturada (não pastel genérico)?
□ Fonte com personalidade (não Arial/Helvetica)?
□ Border-radius consistente em toda app?

HIERARQUIA:
□ Cada tela tem 1 ação primária clara?
□ Hierarquia usa cor + peso + tamanho (não só tamanho)?
□ Texto secundário tem cor cinza, não preto?

COR:
□ Cinza tem leve tom da brand (não cinza puro)?
□ 1 cor vibrante (brand) + neutros (não tudo médio saturado)?
□ Status comunicado por cor + ícone (acessibilidade)?

ELEVAÇÃO:
□ Cards têm border sutil OU sombra com camadas?
□ Sombras escalonadas (sm, md, lg) por importância?
□ Imagens não estão "flutuando" sem container?

ESPAÇO:
□ Padding generoso em containers principais (>24px)?
□ Espaço entre seções >48px?
□ Espaços derivados de escala (não random)?

ESTADOS:
□ Hover usa cor mais escura (não opacity)?
□ Focus tem outline visível (acessibilidade)?
□ Disabled tem cor mais clara + cursor-not-allowed?

FORMS:
□ Inputs com border 1px sutil, radius consistente?
□ Focus state com cor brand + glow leve?
□ Validation inline (não só no submit)?

BOTÕES:
□ Altura consistente (todos com 40px ou 48px)?
□ Padding horizontal generoso (16-24px)?
□ Variantes claras (primary, secondary, ghost)?

ANTI-AI-SLOP:
□ NÃO há gradient em todo lugar (max 1-2 elementos)?
□ NÃO há cantos arredondados gigantes em containers grandes?
□ NÃO há múltiplas brand colors competindo?
□ NÃO há tudo igualmente "bonito" (deve ter hierarquia)?
□ NÃO há sombras planas (use camadas)?
□ NÃO há texto lorem ipsum sem variação?
```

Se <20 checks, UI ainda parece amadora. Refactor.

---

## 9. Erros comuns

### Erro 1: "Vou seguir Material Design / Bootstrap puro"
Resultado: UI genérica, indistinguível de outras 1000 apps.
**Fix:** customize tokens. Faça o sistema seu.

### Erro 2: "Designer entrega Figma, eu copio"
Resultado: implementação degradada (Figma tem efeitos que CSS dificulta).
**Fix:** designer + dev em par. Tokens compartilhados (Tokens Studio).

### Erro 3: "Vou polir no final"
Resultado: deadline aperta, polish nunca acontece.
**Fix:** polish é phase explícita no roadmap, não "se sobrar tempo".

### Erro 4: "v0/Bolt gerou bonito"
Resultado: AI-slop documentado na seção 5.
**Fix:** sempre auditar com checklist anti-AI-slop antes de aceitar.

### Erro 5: "Mais features > melhor UI"
Resultado: produto com 50 features mal apresentadas é pior que 10 bem.
**Fix:** UI é feature. Tem peso no roadmap.

---

## 10. Como integra com outras skills

### 10.1 → `ui-ux-pro-max` (skill matriz)
ui-ux-pro-max define direção estética geral. refactoring-ui dá regras concretas.

### 10.2 → `quality/color-system`
Cor brand, neutros, feedback — vide color-system. refactoring-ui USA o que color-system define.

### 10.3 → `quality/typography-scale`
Hierarquia tipográfica via escala modular.

### 10.4 → `quality/heuristic-evaluation`
Heurística 8 (estético/minimalista) é avaliada com refactoring-ui em mente.

### 10.5 → `meta/jobs-to-be-done`
Estética alinha com job social (como usuário quer ser visto).

### 10.6 → PLAN.md de phase

```markdown
## Phase 4 — Polish UI checkout

### Skills Consultadas
- `meta/refactoring-ui` — checklist anti-AI-slop, princípios estéticos
- `quality/color-system` — uso correto de cor brand vs neutros
- `quality/heuristic-evaluation` — audit pós-fix
```

---

## 11. Como rodar audit anti-AI-slop com Claude

```
"Faça audit anti-AI-slop da phase N seguindo
.claude/skills/meta/refactoring-ui/SKILL.md.

Para cada um dos 7 princípios:
1. Avalie se UI atual segue
2. Identifique violações específicas (com location)
3. Sugira fix concreto

Compare com checklist da seção 8.
Severity: 4 = violação grave (parece AI-slop), 1 = cosmético.

Compile em .planning/phases/N/N-UI-POLISH-AUDIT.md."
```

---

## 12. Inspirações (UIs profissionais para estudar)

Quando em dúvida, olhe:

**SaaS B2B:**
- Linear (linear.app) — densidade alta, polish extremo
- Stripe (stripe.com) — espaço generoso, tipografia limpa
- Vercel (vercel.com) — minimalismo refinado
- Notion (notion.so) — friendly mas profissional

**B2C:**
- Apple (apple.com) — branco, espaço, foco
- Airbnb (airbnb.com) — fotografia, calor humano
- Spotify — dark mode bem feito

**Brasileiros:**
- Nubank (nubank.com.br) — roxo brand consistente
- Loft (loft.com.br) — UI moderna brasileira
- Hotmart — denso mas organizado

**O que observar:**
1. Quantas cores usam? (resposta: poucas)
2. Quanto espaço entre elementos? (resposta: muito)
3. Quantos níveis de hierarquia? (resposta: 3-5, não 8)
4. Sombras planas ou camadas? (resposta: camadas)

---

## 13. Referências

- **Refactoring UI** — Adam Wathan, Steve Schoger (2018) — livro base
- **Refactoring UI on YouTube** — Steve Schoger live design sessions
- **The Component Gallery** (component.gallery) — padrões reais
- **Refactoring UI sub** — Reddit r/web_design

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 13 seções, 7 princípios com snippets, 8 anti-patterns AI-slop com correção, 2 antes/depois, stack visual pronto, checklist 20+ itens
