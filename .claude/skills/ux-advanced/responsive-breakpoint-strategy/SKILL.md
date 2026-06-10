# Skill: responsive-breakpoint-strategy

> Estratégia mobile-first para o {PROJETO}: breakpoints padronizados, container queries, tipografia fluida, grid responsivo, imagens adaptativas.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

Evitar dois anti-patterns opostos: (a) CSS só pra desktop que quebra no celular, (b) CSS só pra mobile que desperdiça espaço em tela grande. Define breakpoints únicos para admin (desktop-first com adaptação mobile) e mobile (mobile-first com adaptação tablet).

## Quando usar (triggers)

- Qualquer layout novo (tela, componente)
- Grid, lista multi-coluna
- Tipografia que precisa escalar
- Elementos com width fixo (`width: 800px`) → provável bug em mobile
- Media query hardcoded

---

## Breakpoints padrão {PROJETO}

```scss
// Adicionar ao _tokens.scss
:root {
  --bp-sm:   640px;   // tablet pequeno / landscape phone
  --bp-md:   768px;   // tablet
  --bp-lg:   1024px;  // laptop pequeno / tablet landscape
  --bp-xl:   1280px;  // desktop padrão
  --bp-2xl:  1536px;  // desktop grande
}
```

**Não criar breakpoints ad-hoc.** Se o layout precisa ajuste em 900px, ou arredonda pra 768/1024 ou usa container query.

```scss
// Mixins SCSS para reusar
@mixin mq($breakpoint) {
  @if $breakpoint == sm { @media (min-width: 640px) { @content; } }
  @else if $breakpoint == md { @media (min-width: 768px) { @content; } }
  @else if $breakpoint == lg { @media (min-width: 1024px) { @content; } }
  @else if $breakpoint == xl { @media (min-width: 1280px) { @content; } }
  @else if $breakpoint == 2xl { @media (min-width: 1536px) { @content; } }
}
```

---

## Mobile-first é padrão

**Sempre** escreva primeiro para mobile (menor), adicione estilos maiores com `min-width`. Evita reset hell.

### ❌ Errado (desktop-first)

```scss
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
```

### ✅ Certo (mobile-first)

```scss
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--app-space-3);

  @include mq(md) {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--app-space-4);
  }

  @include mq(xl) {
    grid-template-columns: repeat(4, 1fr);
    gap: var(--app-space-6);
  }
}
```

---

## Grid de KPIs responsivo (exemplo dashboard {PROJETO})

```scss
.kpi-grid {
  display: grid;
  gap: var(--app-space-4);
  grid-template-columns: 1fr;                          // mobile: 1 col

  @include mq(sm) {
    grid-template-columns: repeat(2, 1fr);             // tablet: 2 col
  }
  @include mq(lg) {
    grid-template-columns: repeat(3, 1fr);             // laptop: 3 col
  }
  @include mq(xl) {
    grid-template-columns: repeat(4, 1fr);             // desktop: 4 col
    gap: var(--app-space-6);
  }
}
```

### Angular CDK alternativa (tipagem forte)

```typescript
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

readonly columns = toSignal(
  this.breakpoint.observe([Breakpoints.XSmall, Breakpoints.Small, Breakpoints.Medium, Breakpoints.Large, Breakpoints.XLarge])
    .pipe(map(state => {
      if (state.breakpoints[Breakpoints.XLarge]) return 4;
      if (state.breakpoints[Breakpoints.Large]) return 3;
      if (state.breakpoints[Breakpoints.Medium]) return 2;
      return 1;
    })),
  { initialValue: 1 },
);
```

---

## Container queries (quando o componente importa mais que a tela)

Container query checa o container pai, não a viewport. Útil em dashboards onde um card pode estar em layout de 2 colunas ou 4 colunas e deve se adaptar.

```scss
.chart-card {
  container-type: inline-size;
  container-name: chart;
}

.chart-card .chart-header {
  display: flex;
  flex-direction: column;

  @container chart (min-width: 400px) {
    flex-direction: row;
    justify-content: space-between;
  }
}
```

**Suporte:** Chrome 105+, Safari 16+, Firefox 110+ (todos 2023+). Seguro usar no {PROJETO}.

---

## Tipografia fluida

Evite degraus abruptos (`font-size: 16px` no mobile, `font-size: 24px` no desktop). Use `clamp()`:

```scss
h1 {
  font-size: clamp(1.75rem, 1.5rem + 1.5vw, 2.5rem);  // 28px-40px
  line-height: 1.2;
}

h2 {
  font-size: clamp(1.25rem, 1rem + 1vw, 1.75rem);     // 20px-28px
}

.kpi-value {
  font-size: clamp(1.5rem, 1.25rem + 1.5vw, 2.25rem); // 24px-36px
}
```

**Regra geral:**
```
clamp(min, preferido, max)
preferido = base-rem + vw-factor
vw-factor = diferença desejada / (bp-max - bp-min) * 100
```

---

## Imagens responsivas

### srcset para fotos de portfólio

```html
<img
  [src]="photo.large"
  [srcset]="photo.small + ' 480w, ' + photo.medium + ' 960w, ' + photo.large + ' 1920w'"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  alt="Foto do serviço"
  loading="lazy"
/>
```

Backblaze B2 pode servir múltiplos tamanhos via naming:
- `portfolio/{id}/photo-480.webp`
- `portfolio/{id}/photo-960.webp`
- `portfolio/{id}/photo-1920.webp`

Pipeline de upload gera as 3 versões (ver `file-upload-ux`).

### Aspect ratio sem CLS

```scss
.photo-card {
  aspect-ratio: 4 / 3;
  width: 100%;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
```

---

## Touch targets em mobile

```scss
// Regra WCAG 2.5.5: mínimo 44x44px para alvo tátil
button, .clickable, ion-item[button] {
  min-height: 44px;
  min-width: 44px;
}
```

---

## Safe area (já tratado em `ionic-patterns`, mas vale lembrar)

```scss
.fab, .fixed-bottom-bar {
  bottom: calc(var(--app-space-4) + env(safe-area-inset-bottom, 0));
}

.header {
  padding-top: calc(var(--app-space-3) + env(safe-area-inset-top, 0));
}
```

---

## Admin vs Mobile — estratégias diferentes

| Aspecto | Admin (desktop-first) | Mobile (Ionic) |
|---|---|---|
| Breakpoint de entrada | 1280px (otimiza para trabalho) | 375px (iPhone SE) |
| Sidebar | Side persistente em `lg+`, over em `<lg` | N/A (usa tabs) |
| Grid cards | 4 col em xl, 2 em md, 1 em sm | 1-2 col (lista vertical) |
| Tabelas | Tabela padrão com scroll horizontal em mobile | Transformar em cards (não tabela rolada) |
| Formulário | 2 col em md+ | 1 col sempre |
| Font base | 14px (denso, muita info) | 16px (toque, conforto) |

### Transformar tabela em cards no mobile

```html
<!-- Desktop: tabela -->
<table class="desktop-only">...</table>

<!-- Mobile: lista de cards -->
<div class="mobile-only">
  @for (prof of items(); track prof.id) {
    <div class="prof-card">
      <img [src]="prof.avatar" />
      <div>
        <h3>{{ prof.name }}</h3>
        <span>{{ prof.category }} · {{ prof.city }}</span>
        <span class="badge" [class.approved]="prof.status === 'approved'">
          {{ prof.status | statusLabel }}
        </span>
      </div>
    </div>
  }
</div>
```

```scss
.desktop-only { display: none; @include mq(lg) { display: block; } }
.mobile-only  { display: block; @include mq(lg) { display: none; } }
```

---

## Anti-patterns

1. ❌ **Width fixo em px** (`width: 800px`) — quebra em < 800px
2. ❌ **Media query com valor arbitrário** (`@media (max-width: 823px)`) — cria breakpoint novo; use os 5 padrão
3. ❌ **Desktop-first com `max-width`** — reset hell; use mobile-first
4. ❌ **Tabela com scroll horizontal em mobile** sem alternativa — UX ruim; transforme em cards
5. ❌ **Font-size < 16px no mobile** em input — iOS Safari dá zoom automático
6. ❌ **Botão 32x32px** — abaixo do mínimo tátil WCAG (44x44)
7. ❌ **Imagem sem `loading="lazy"`** em lista longa — carrega tudo de uma vez
8. ❌ **Imagem sem `aspect-ratio`** — CLS (layout shift) na chegada
9. ❌ **`vw` sem `clamp`** em tipografia — `font-size: 3vw` fica minúsculo em mobile
10. ❌ **`min-height: 100vh`** em mobile — barra de endereço do Safari causa jump; use `100dvh`

---

## Checklist de review

- [ ] Mobile-first: estilos base funcionam em 375px
- [ ] Sem media queries ad-hoc — só nos 5 breakpoints
- [ ] Grid responsivo com `grid-template-columns` progressivo
- [ ] Tipografia em `clamp()` para escala fluida
- [ ] Imagens com `srcset` + `sizes` + `loading="lazy"` + `aspect-ratio`
- [ ] Botão e ícone-botão ≥ 44x44px em mobile
- [ ] Input com `font-size: 16px` em mobile (evita zoom iOS)
- [ ] Tabelas: viram cards em mobile ou scroll horizontal aceitável
- [ ] Safe-area respeitada em FABs e fixed
- [ ] `100dvh` em vez de `100vh` onde full-height é crítico
- [ ] Container queries se o componente é reusado em múltiplos contextos

<!-- Skill aplicada: todo SCSS de layout, grids, dashboards, listas -->
