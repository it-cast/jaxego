# Performance — Web Vitals (LCP/INP/CLS) em produção

> Skill obrigatória para qualquer fase com UI ou endpoint servindo em produção.
> Referenciada em `skills-enforcement.md` e `gates-v3.md` (Performance budget).

## Budget padrão (override em `.planning/config.json`)

| Métrica | Target | Threshold "crítico" | Como medir |
|---------|--------|---------------------|------------|
| LCP (Largest Contentful Paint) | ≤ 2500ms | ≤ 4000ms | Lighthouse CI em cada PR + Real User Monitoring |
| INP (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | RUM em staging |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | Lighthouse CI + RUM |
| TTFB (Time to First Byte) | ≤ 600ms | ≤ 1000ms | Synthetic + RUM |
| FCP (First Contentful Paint) | ≤ 1800ms | ≤ 3000ms | Lighthouse CI |
| TBT (Total Blocking Time) | ≤ 200ms | ≤ 600ms | Lighthouse CI |

Bundle budgets:
- `main.js` (main bundle, gzip): ≤ 400 KB
- `vendor.js` (gzip): ≤ 800 KB
- CSS total (gzip): ≤ 80 KB
- Imagens above-the-fold: WebP, lazy-load abaixo

## Regras aplicáveis

### LCP

1. **Imagem LCP com preload.** Se o LCP é uma imagem hero:
   ```html
   <link rel="preload" as="image" href="/hero.webp" fetchpriority="high">
   ```

2. **Evitar lazy-load no LCP.** Nunca `loading="lazy"` em imagem above-the-fold.

3. **Server-side render ou SSG** para páginas críticas. Client-side rendering puro penaliza LCP em 300-800ms.

4. **Responsivas obrigatórias:** `<img srcset>` ou `<picture>` com variantes WebP + fallback.

5. **Fontes: swap/optional com display.**
   ```css
   @font-face {
     font-family: "Inter";
     src: url("/inter.woff2") format("woff2");
     font-display: swap;  /* não "block" */
   }
   ```
   E preload da fonte principal:
   ```html
   <link rel="preload" as="font" type="font/woff2" href="/inter.woff2" crossorigin>
   ```

### INP

1. **Debounce/throttle em handlers pesados.** Busca em input = debounce 300ms mínimo.

2. **Web Workers para computação > 50ms.** Parsing grande, hashing, geração de QR code.

3. **`requestIdleCallback` para analytics, logs, cleanup.** Nunca blocking main thread.

4. **Listas virtuais para > 100 items.** React: `react-window`/`react-virtualized`. Angular: `cdk-virtual-scroll-viewport`.

5. **Evitar `setState` em loop de evento (React/Vue).** Agregar estado.

6. **Event delegation** em listas grandes em vez de handlers individuais.

### CLS

1. **Reservar espaço para imagens.** `width`/`height` ou `aspect-ratio`.

2. **Skeleton com altura real.** Nunca `height: auto` em skeleton — cria shift quando conteúdo chega.

3. **Zero inserção de banner após load** (cookie banner, CTA popup). Se necessário, usar `position: fixed` que não afeta layout.

4. **Fontes com `size-adjust`** para minimizar shift entre fallback e fonte real:
   ```css
   @font-face {
     font-family: "Inter";
     size-adjust: 100.06%;
     ascent-override: 90%;
     /* calibrar via https://deploy-preview-15--upbeat-shirley-608546.netlify.app/perfect-ish-font-fallback */
   }
   ```

5. **Imagens responsivas com aspect-ratio.**
   ```html
   <img src="hero.webp" width="1200" height="630" alt="...">
   ```

### Bundle size

1. **Route-based code splitting.** Cada rota top-level é lazy.

2. **Tree-shaking em libs.** Import específico:
   ```ts
   // ❌ pega biblioteca inteira
   import _ from "lodash";

   // ✅ só o que precisa
   import debounce from "lodash-es/debounce";
   ```

3. **Analyze bundle em CI.** `rollup-plugin-visualizer`, `webpack-bundle-analyzer`, `source-map-explorer`.

4. **Icon library: tree-shakeable.** Lucide/Heroicons importam ícone por ícone. FontAwesome default puxa tudo.

5. **Moment.js proibido.** Usar `date-fns` ou `dayjs`.

6. **Proibir `*` e `/dist` imports.**

## Anti-patterns

- ❌ `<img loading="lazy">` no hero above-the-fold
- ❌ CSS inline em `<style>` dentro de `<body>` (causa reflow)
- ❌ `@import` em CSS (sequencial, lento)
- ❌ `document.querySelectorAll` em loop de render
- ❌ Animar `width`, `height`, `top`, `left` (reflow) — usar `transform` e `opacity`
- ❌ Não medir em dispositivo real. Lighthouse simulado ≠ campo.

## CI/CD enforcement

```yaml
# .github/workflows/perf.yml
- name: Lighthouse CI
  run: |
    npx lhci autorun \
      --assert.preset=lighthouse:recommended \
      --assert.assertions.categories:performance=0.9

- name: Bundle size
  run: |
    npx bundlesize
```

`bundlesize.json`:
```json
[
  { "path": "./dist/main.*.js", "maxSize": "400 kB", "compression": "gzip" },
  { "path": "./dist/vendor.*.js", "maxSize": "800 kB", "compression": "gzip" }
]
```

## Real User Monitoring

- Web-vitals lib:
  ```ts
  import { onLCP, onINP, onCLS } from 'web-vitals';
  
  onLCP((m) => sendAnalytics('LCP', m.value));
  onINP((m) => sendAnalytics('INP', m.value));
  onCLS((m) => sendAnalytics('CLS', m.value));
  ```

- Enviar para PostHog, Datadog RUM, ou Sentry performance.

- Definir p75 do RUM como health metric — alertar se p75 LCP > 2500ms por 1h.

## Backend (complemento)

Skill `observability-production` cobre latência e profiling server-side. Resumo das sobreposições:

- Endpoint p95 ≤ 300ms, p99 ≤ 800ms
- N+1 queries: zero em endpoints de listagem (usar joinedload/selectinload)
- Cache em endpoints idempotentes (Redis com TTL)
- Compressão gzip/brotli no reverse proxy

## Checklist de PLAN.md (para fases com UI)

Copiar para `## Performance budget` do PLAN:

- [ ] LCP ≤ 2500ms medido em Lighthouse CI
- [ ] INP ≤ 200ms em interações principais (click do CTA, scroll em lista)
- [ ] CLS ≤ 0.1 em rotas desta fase
- [ ] Bundle main.js ≤ 400 KB gzip
- [ ] Imagens: WebP + srcset + lazy abaixo da dobra, `width`/`height` sempre
- [ ] Fontes: `font-display: swap`, preload da principal
- [ ] Lazy load de rotas novas desta fase
- [ ] CSS inline crítico se LCP é texto, resto lazy
- [ ] Web Vitals reportando no RUM

Cada item desta lista que não se aplica: documentar em "Dispensa" com razão.
