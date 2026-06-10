---
name: handoff-spec
category: product
description: Especificação completa de handoff designer→dev — medidas, behaviors, assets e edge cases. Reduz idas e voltas durante implementação.
---

# Handoff Spec — Especificação de Handoff

> "O design está no Figma" não é handoff. Handoff é documento que dev consegue implementar sem perguntas (ou com perguntas mínimas).

## Quando esta skill é obrigatória

- Phase com designer separado entregando design
- Antes de `/gsd-execute-phase` em phases UI complexas
- Toda vez que componente novo entra no design system

## Estrutura mínima

### 1. Visão geral

```yaml
component: PaymentMethodCard
purpose: "Card que mostra método de pagamento (cartão ou PIX) com opção de remover"
context_of_use: ["Tela de checkout", "Tela de configurações > Métodos de pagamento"]
designer: "Maria Silva"
version: "1.2"
last_updated: "2026-04-29"
figma_link: "https://figma.com/file/xxx?node=123"
```

### 2. Estados

Listar TODOS os estados possíveis:

```
✅ default
✅ hover
✅ focus (keyboard)
✅ active/pressed
✅ disabled
✅ loading
✅ error
✅ selected
✅ removed (animação de saída)
```

Para cada um:
- Preview visual
- Diferenças do default (cor, sombra, etc)
- Trigger (mouse over, click, etc)

### 3. Especificações de medida

Não usar "espaço médio". Usar tokens.

```yaml
dimensions:
  min_width: "320px"
  max_width: "100%"
  height: "auto"
  min_height: "80px"

padding:
  desktop: "16px 24px"  /* token: space.md space.lg */
  mobile: "12px 16px"   /* token: space.sm space.md */

border_radius: "8px"  /* token: radius.md */
border: "1px solid {color.border.default}"

elevation:
  default: "shadow.sm"
  hover: "shadow.md"
```

### 4. Tipografia

```yaml
text:
  card_title:
    font_size: "{typography.scale.base}"  /* 16px */
    font_weight: "{typography.weight.semibold}"
    line_height: "{typography.lineHeight.tight}"
    color: "{color.text.primary}"

  card_subtitle:
    font_size: "{typography.scale.sm}"
    font_weight: "{typography.weight.regular}"
    color: "{color.text.secondary}"
```

### 5. Cores e contraste

Garantir todos os textos passam WCAG AA:

```yaml
colors:
  background:
    light: "{color.surface.default}"
    dark: "{color.surface.raised.dark}"
  border:
    default: "{color.border.default}"
    selected: "{color.brand.primary}"
  text:
    primary: "{color.text.primary}" /* 4.5:1 mínimo */
    secondary: "{color.text.secondary}" /* 4.5:1 mínimo */

contrast_validations:
  - text_primary_on_background: "12.6:1 ✓ AAA"
  - text_secondary_on_background: "5.7:1 ✓ AA"
  - border_on_background: "3.1:1 ✓ AA"
```

### 6. Comportamentos / interações

```yaml
interactions:
  - trigger: "hover"
    response: "elevation aumenta para shadow.md, border highlight"
    duration: "150ms ease-out"

  - trigger: "click no botão remover"
    response: "modal de confirmação 'Remover este método?'"
    confirmation_required: true

  - trigger: "selected (radio button)"
    response: "border 2px brand-primary, ícone de check no canto"
    state_persistence: true

animations:
  enter: "fade-in 200ms ease-out"
  exit: "slide-up + fade-out 250ms ease-in"
```

### 7. Edge cases

```yaml
edge_cases:
  - case: "Texto longo no card title"
    behavior: "truncate com ellipsis após 1 linha"
    example: "Cartão com nome muito longo termina com... no final"

  - case: "Mais de 5 cards na lista"
    behavior: "scroll vertical na container"

  - case: "Sem cards cadastrados"
    behavior: "Mostrar empty state (componente EmptyPaymentMethods)"

  - case: "Modo offline"
    behavior: "Card cinza com badge 'Sem conexão' + botão tentar novamente"

  - case: "Tela <320px"
    behavior: "Layout não suportado, mostrar fallback simples"
```

### 8. Acessibilidade

```yaml
accessibility:
  role: "article"
  aria_label_template: "Método de pagamento: {method_type} terminando em {last_digits}"
  keyboard_navigation:
    - "Tab: foca no card"
    - "Enter/Space: ativa seleção"
    - "Delete (com card focado): aciona remoção"
  focus_indicator: "outline 2px brand-primary, offset 2px"
  screen_reader_only: "h3 para nome do método (sr-only se já visível)"
```

### 9. Assets

```yaml
icons:
  - name: "credit-card"
    source: "lucide-react@0.383.0"
    size: "24px"
  - name: "trash-2"
    source: "lucide-react@0.383.0"
    size: "20px"

images: []  /* sem imagens neste componente */

logos:
  - "visa.svg"
  - "mastercard.svg"
  - "elo.svg"
  - "amex.svg"
  source: "/assets/payment-logos/"
```

### 10. Componentes dependentes

```yaml
depends_on:
  - "Button (variant=ghost, size=sm)"
  - "Badge (variant=info)"
  - "Modal (para confirmar remoção)"

reusable_in:
  - "ProfileSettings"
  - "CheckoutFlow"
  - "AdminUserDetail"
```

### 11. Variantes

```yaml
variants:
  - name: "default"
    description: "Card padrão com nome e número"

  - name: "compact"
    description: "Versão menor para listagem em modal"
    differences: "padding reduzido, sem subtitle"

  - name: "selected"
    description: "Estado quando cartão é o método ativo"
    differences: "border brand-primary, ícone check"
```

### 12. Testes esperados

```yaml
tests_to_write:
  unit:
    - "Renderiza com props mínimas"
    - "Aciona onRemove quando botão clicado"
    - "Mostra modal antes de remover"

  integration:
    - "Selecionar card emite evento para parent"
    - "Card disabled não responde a clicks"

  e2e:
    - "Fluxo completo: listar > selecionar > confirmar > submeter pagamento"

  accessibility:
    - "Tab navigation funciona"
    - "Screen reader anuncia tipo do cartão"
    - "Contraste passa em axe"
```

## Anti-patterns

❌ "Espaço médio entre cards" — usar token explícito
❌ Cores em hex no spec ("background: #fff") — usar token
❌ Skipar estados (só default + hover)
❌ Sem edge cases (UI quebra em casos reais)
❌ Acessibilidade como afterthought
❌ Tipografia sem line-height
❌ Animação sem duração e easing

## Integração

- Antes desta: design no Figma/protótipo
- Aliada: `meta/design-to-code` (translation)
- Output vai para: `<N>-UI-SPEC.md` da phase + `docs/identidade-visual/components/<componente>.md`
