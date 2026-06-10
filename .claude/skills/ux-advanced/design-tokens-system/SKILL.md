# Skill: design-tokens-system

> Sistema de design tokens em CSS variables para {PROJETO}: hierarquia semantic → alias → literal, bridge Ionic/Material, prep dark mode (Fase 2+), nada de hex direto.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

Garantir que toda cor, spacing, radius, duração e tipografia do {PROJETO} venha de **tokens**, não de valores hardcoded. Resultado: mudar a paleta da marca é 1 diff; preparar dark mode é trocar valores de tokens semânticos; Ionic e Material falam a mesma linguagem.

## Quando usar (triggers)

- Qualquer novo componente ou estilo
- CSS com hex (`#1565C0`), rgba ou valor mágico (`16px`, `12px`)
- Alinhamento de look entre admin (Material) e mobile (Ionic)
- Preparação para dark mode
- Revisão de estilos que vazaram valores literais

## Quando NÃO usar

- Prototipagem rápida descartável
- Código de terceiros (libs externas)

---

## Hierarquia de tokens (3 camadas)

```
Literal (cores crus)        →  --app-blue-600: #1565C0
Alias (intenção)            →  --app-brand-primary: var(--app-blue-600)
Semantic (contexto de uso)  →  --app-surface-primary: var(--app-brand-primary)
```

**Regra de ouro:**
- **Literal**: define o hex. Nunca usado direto em componente.
- **Alias**: dá significado de marca. Usado em documentação, não em componente.
- **Semantic**: contexto de UI. **Isso** é o que componente consome.

---

## Arquivo único: `styles/_tokens.scss`

```scss
// --- CAMADA 1: LITERAL ---
:root {
  // Escala azul (primary do {PROJETO})
  --app-blue-50:  #E3F2FD;
  --app-blue-100: #BBDEFB;
  --app-blue-400: #42A5F5;
  --app-blue-500: #2196F3;
  --app-blue-600: #1E88E5;
  --app-blue-700: #1976D2;
  --app-blue-800: #1565C0;  // cor do logo
  --app-blue-900: #0D47A1;

  // Escala turquesa (accent)
  --app-cyan-400: #4FC3F7;
  --app-cyan-500: #00BCD4;
  --app-cyan-600: #00ACC1;

  // Escala neutra (cinza)
  --app-gray-50:  #FAFAFA;
  --app-gray-100: #F5F5F5;
  --app-gray-200: #EEEEEE;
  --app-gray-300: #E0E0E0;
  --app-gray-400: #BDBDBD;
  --app-gray-500: #9E9E9E;
  --app-gray-600: #757575;
  --app-gray-700: #616161;
  --app-gray-800: #424242;
  --app-gray-900: #212121;

  // Cores funcionais
  --app-success-500: #00C853;
  --app-warning-500: #FFD600;
  --app-error-500:   #FF1744;
  --app-energy-500:  #FF6D00;

  // Tipografia (escala modular 1.125)
  --app-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --app-font-size-xs:   12px;
  --app-font-size-sm:   14px;
  --app-font-size-base: 16px;
  --app-font-size-lg:   18px;
  --app-font-size-xl:   20px;
  --app-font-size-2xl:  24px;
  --app-font-size-3xl:  30px;
  --app-font-size-4xl:  36px;

  --app-font-weight-normal:   400;
  --app-font-weight-medium:   500;
  --app-font-weight-semibold: 600;
  --app-font-weight-bold:     700;

  --app-line-height-tight:  1.2;
  --app-line-height-normal: 1.5;
  --app-line-height-loose:  1.75;

  // Spacing (escala 4px)
  --app-space-0:  0;
  --app-space-1:  4px;
  --app-space-2:  8px;
  --app-space-3:  12px;
  --app-space-4:  16px;
  --app-space-5:  20px;
  --app-space-6:  24px;
  --app-space-8:  32px;
  --app-space-10: 40px;
  --app-space-12: 48px;
  --app-space-16: 64px;

  // Border radius
  --app-radius-sm:   4px;
  --app-radius-base: 8px;
  --app-radius-md:   12px;  // botões padrão {PROJETO}
  --app-radius-lg:   16px;  // cards padrão {PROJETO}
  --app-radius-xl:   24px;
  --app-radius-full: 9999px;

  // Shadow
  --app-shadow-sm:  0 1px 2px rgba(0, 0, 0, 0.05);
  --app-shadow-md:  0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.04);
  --app-shadow-lg:  0 10px 15px rgba(0, 0, 0, 0.08), 0 4px 6px rgba(0, 0, 0, 0.04);
  --app-shadow-xl:  0 20px 25px rgba(0, 0, 0, 0.10), 0 8px 10px rgba(0, 0, 0, 0.04);

  // Durations
  --app-duration-fast:   150ms;
  --app-duration-base:   250ms;
  --app-duration-slow:   400ms;
  --app-easing-default:  cubic-bezier(0.4, 0, 0.2, 1);
  --app-easing-in:       cubic-bezier(0.4, 0, 1, 1);
  --app-easing-out:      cubic-bezier(0, 0, 0.2, 1);

  // Z-index
  --app-z-base:      1;
  --app-z-dropdown:  1000;
  --app-z-sticky:    1020;
  --app-z-modal:     1050;
  --app-z-toast:     1080;
}

// --- CAMADA 2: ALIAS (marca) ---
:root {
  --app-brand-primary:      var(--app-blue-800);
  --app-brand-primary-soft: var(--app-blue-100);
  --app-brand-accent:       var(--app-cyan-500);
  --app-brand-energy:       var(--app-energy-500);

  --app-gradient-header: linear-gradient(135deg, #0D3B66, var(--app-blue-500));
  --app-gradient-cta:    linear-gradient(135deg, var(--app-cyan-500), var(--app-cyan-400));
}

// --- CAMADA 3: SEMANTIC (contexto de UI) ---
:root {
  // Surfaces
  --app-surface-page:      var(--app-gray-50);
  --app-surface-card:      #FFFFFF;
  --app-surface-raised:    #FFFFFF;
  --app-surface-overlay:   rgba(0, 0, 0, 0.5);
  --app-surface-primary:   var(--app-brand-primary);

  // Text
  --app-text-primary:   var(--app-gray-900);
  --app-text-secondary: var(--app-gray-700);
  --app-text-tertiary:  var(--app-gray-500);
  --app-text-disabled:  var(--app-gray-400);
  --app-text-inverse:   #FFFFFF;
  --app-text-brand:     var(--app-brand-primary);

  // Borders
  --app-border-subtle:  var(--app-gray-200);
  --app-border-default: var(--app-gray-300);
  --app-border-strong:  var(--app-gray-500);
  --app-border-focus:   var(--app-brand-primary);

  // Feedback
  --app-feedback-success: var(--app-success-500);
  --app-feedback-warning: var(--app-warning-500);
  --app-feedback-error:   var(--app-error-500);

  // Interactive states
  --app-state-hover:    rgba(21, 101, 192, 0.08);
  --app-state-pressed:  rgba(21, 101, 192, 0.12);
  --app-state-focus:    rgba(21, 101, 192, 0.24);
  --app-state-selected: rgba(21, 101, 192, 0.16);
}
```

---

## Bridge para Ionic

Ionic usa suas próprias CSS vars (`--ion-color-primary` etc). Mapeie para as nossas:

```scss
// apps/mobile/src/theme/variables.scss
@import 'tokens';

:root {
  --ion-color-primary:          var(--app-brand-primary);
  --ion-color-primary-rgb:      21, 101, 192;
  --ion-color-primary-contrast: var(--app-text-inverse);
  --ion-color-primary-shade:    var(--app-blue-900);
  --ion-color-primary-tint:     var(--app-blue-700);

  --ion-color-secondary:        var(--app-brand-accent);
  --ion-color-tertiary:         var(--app-brand-energy);
  --ion-color-success:          var(--app-feedback-success);
  --ion-color-warning:          var(--app-feedback-warning);
  --ion-color-danger:           var(--app-feedback-error);

  // Backgrounds
  --ion-background-color:       var(--app-surface-page);
  --ion-background-color-rgb:   250, 250, 250;
  --ion-text-color:             var(--app-text-primary);
  --ion-text-color-rgb:         33, 33, 33;

  // Tipografia
  --ion-font-family:            var(--app-font-family);

  // Border radius dos componentes
  --ion-border-radius:          var(--app-radius-md);
}

// Ionic component overrides
ion-button {
  --border-radius: var(--app-radius-md);
  --padding-start: var(--app-space-5);
  --padding-end: var(--app-space-5);
  font-weight: var(--app-font-weight-semibold);
}

ion-card {
  --border-radius: var(--app-radius-lg);
  box-shadow: var(--app-shadow-md);
}
```

---

## Bridge para Material M3

Material M3 usa `--mat-sys-*` e `--mat-*-*`. Mapeie:

```scss
// apps/admin/src/styles.scss
@use '@angular/material' as mat;
@import 'tokens';

html {
  @include mat.theme((
    color: (primary: mat.$azure-palette, tertiary: mat.$cyan-palette),
    typography: Inter,
  ));
}

// Override M3 com tokens {PROJETO}
:root {
  --mat-sys-primary:         var(--app-brand-primary);
  --mat-sys-on-primary:      var(--app-text-inverse);
  --mat-sys-tertiary:        var(--app-brand-accent);
  --mat-sys-error:           var(--app-feedback-error);
  --mat-sys-surface:         var(--app-surface-card);
  --mat-sys-surface-variant: var(--app-gray-100);
  --mat-sys-on-surface:      var(--app-text-primary);
  --mat-sys-outline:         var(--app-border-default);
}
```

---

## Uso em componente

### ✅ Correto (só tokens semânticos)

```scss
.card {
  background: var(--app-surface-card);
  color: var(--app-text-primary);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--app-radius-lg);
  padding: var(--app-space-6);
  box-shadow: var(--app-shadow-md);
  transition: box-shadow var(--app-duration-base) var(--app-easing-default);
}

.card:hover {
  box-shadow: var(--app-shadow-lg);
  background: var(--app-state-hover);
}
```

### ❌ Errado

```scss
.card {
  background: white;              // usa --app-surface-card
  color: #212121;                 // usa --app-text-primary
  border: 1px solid #EEEEEE;      // usa --app-border-subtle
  border-radius: 16px;            // usa --app-radius-lg
  padding: 24px;                  // usa --app-space-6
  box-shadow: 0 4px 6px rgba(0,0,0,0.07);  // usa --app-shadow-md
  transition: box-shadow 250ms ease;  // usa duration/easing tokens
}
```

---

## Dark mode prep (Fase 2+)

A hierarquia semântica **já é** a preparação. Para ativar dark mode no futuro, basta adicionar:

```scss
@media (prefers-color-scheme: dark) {
  :root {
    --app-surface-page:   var(--app-gray-900);
    --app-surface-card:   var(--app-gray-800);
    --app-text-primary:   var(--app-gray-50);
    --app-text-secondary: var(--app-gray-300);
    --app-border-subtle:  var(--app-gray-700);
    --app-border-default: var(--app-gray-600);
    // ... nada em componente muda
  }
}
```

**Hoje (MVP) não ativamos.** Mas a arquitetura já aceita.

---

## Anti-patterns

1. ❌ **Hex direto em componente** (`color: #1565C0`) — mude paleta e tem que caçar 200 lugares
2. ❌ **Literal usado direto** (`var(--app-blue-800)`) — ignora a camada semântica
3. ❌ **Valor mágico de spacing** (`padding: 17px`) — fora da escala; use `--app-space-*`
4. ❌ **`rgba(0,0,0,0.5)` repetido** — crie token (`--app-surface-overlay`)
5. ❌ **Duas fontes na aplicação** (`Inter` no admin, `Roboto` no mobile) — use `--app-font-family` único
6. ❌ **Token com nome de cor** (`--app-blue`) em vez de contexto (`--app-brand-primary`)
7. ❌ **Não alinhar Ionic + Material** — app mobile tem botão arredondado, admin tem reto
8. ❌ **Hardcode duration** (`transition: 300ms`) — inconsistente; use `--app-duration-*`
9. ❌ **`!important`** para sobrescrever Material/Ionic — prova que o token não está aplicado
10. ❌ **SCSS `$variable`** — não funciona em runtime; use CSS custom property

---

## Checklist de review

- [ ] Nenhum hex hardcoded em componente
- [ ] Valores vêm da escala de tokens (spacing, radius, font-size)
- [ ] Componentes consomem tokens **semânticos**, não literais
- [ ] Cor funcional usa `--app-feedback-*`, não hex direto
- [ ] Tipografia usa `--app-font-family` + `--app-font-size-*`
- [ ] Ionic e Material bridgeados no seu theme file
- [ ] Border-radius consistente (botões 12px, cards 16px)
- [ ] Transições usam duration + easing tokens
- [ ] Arquitetura permite dark mode via swap de semânticos

<!-- Skill aplicada: todo SCSS, theme files Ionic + Material -->
