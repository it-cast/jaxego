# Micro-animations & Delight — motion com propósito, não decoração

> Skill obrigatória para apps com UI que almeja percepção premium. Sem micro-animações corretas, o app parece funcional mas não polido.

## Princípio central

Animação sem propósito é ruído. Animação com propósito:
1. **Comunica mudança de estado** — "algo aconteceu aqui"
2. **Oferece continuidade espacial** — "este elemento veio dali"
3. **Dá feedback de interação** — "meu toque foi registrado"
4. **Mascara latência** — 300ms de transição cobrem 300ms de carregamento sem parecer lento

Nunca animar por animar. Toda animação responde a uma pergunta do usuário ("cliquei mesmo?", "para onde foi?", "está carregando?").

## Taxonomia

| Tipo | Duração | Exemplo | Quando |
|------|---------|---------|--------|
| **Micro-feedback** | 80-150ms | Botão scale 0.95 ao press | Toda ação interativa |
| **State change** | 150-300ms | Tab active muda estilo | Mudança de estado dentro de contexto |
| **Transition** | 200-400ms | Página navega | Mudança de contexto |
| **Celebration** | 400-800ms | ✓ animado em sucesso crítico | Fim de jornada importante (pagamento, conclusão) |
| **Loop ambiental** | > 1s, pausável | Skeleton shimmer | Comunicando atividade contínua |

**Regra de ouro:** nada > 500ms bloqueia usuário em ação crítica. Se precisa mais, quebra em fases com feedback intermediário.

## Física

### Easing

```css
/* Rejeitar */
transition: all 0.3s linear;       /* robótico */
transition: all 0.3s ease;         /* genérico demais */

/* Preferir */
transition: transform 0.2s cubic-bezier(0.0, 0.0, 0.2, 1);   /* ease-out — natural */
transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);          /* standard (Material) */
transition: transform 0.4s cubic-bezier(0.5, 1.25, 0.75, 1.25); /* spring overshoot */
```

Tokens no design system:
```scss
$easing-out: cubic-bezier(0.0, 0.0, 0.2, 1);       /* entra com impulso, para suave */
$easing-in: cubic-bezier(0.4, 0.0, 1, 1);          /* acelera saindo */
$easing-inout: cubic-bezier(0.4, 0.0, 0.2, 1);     /* para transições recíprocas */
$easing-spring: cubic-bezier(0.5, 1.25, 0.75, 1.25); /* bounce leve */
$easing-emphasized: cubic-bezier(0.2, 0.0, 0.0, 1); /* exagero em transição de contexto */
```

### Duração

```scss
$duration-fast: 100ms;    /* feedback de clique/hover */
$duration-normal: 200ms;  /* state change, toggle */
$duration-slow: 400ms;    /* transição de contexto */
$duration-celebration: 600ms;
```

Regra: **entrada** um pouco mais lenta que **saída** (item aparecer é mais importante que desaparecer):
```scss
.modal {
  transition: opacity 300ms ease-out, transform 300ms cubic-bezier(0.5, 1.25, 0.75, 1.25);
}
.modal.leave {
  transition: opacity 150ms ease-in, transform 150ms ease-in;
}
```

## Casos obrigatórios

### 1. Botão ao clicar

```scss
.app-button {
  transition: transform 100ms ease-out, background-color 150ms ease-out;
}
.app-button:active {
  transform: scale(0.97);
}
```

Feedback de 3% de escala é perceptível no pixel mas não jarring. Valida "meu toque foi registrado" antes mesmo da ação completar.

### 2. Input focus

```scss
.app-input {
  border: 1px solid var(--color-border);
  transition: border-color 150ms ease-out, box-shadow 150ms ease-out;
}
.app-input:focus {
  border-color: var(--color-brand-500);
  box-shadow: 0 0 0 3px rgba(var(--color-brand-500-rgb), 0.2);
}
```

### 3. Toast ao aparecer

```typescript
// Angular Animations
@Component({
  animations: [
    trigger('toast', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('300ms cubic-bezier(0.5, 1.25, 0.75, 1.25)',
                style({ opacity: 1, transform: 'translateY(0)' })),
      ]),
      transition(':leave', [
        animate('200ms ease-in',
                style({ opacity: 0, transform: 'translateY(-10px)' })),
      ]),
    ]),
  ],
})
```

Slide up + fade in é universal para notificações.

### 4. Item de lista ao remover

```scss
.list-item {
  transition: opacity 200ms ease-out, max-height 300ms ease-out, 
              padding 200ms ease-out, margin 200ms ease-out;
  overflow: hidden;
}
.list-item.removing {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  margin-bottom: 0;
}
```

Collapse elegante. Se apenas fade, o layout salta (ruim).

### 5. Card de ação sendo confirmada (ex: pagamento, confirmação)

```html
<div class="action-card" [class.confirming]="isConfirming" [class.confirmed]="isConfirmed">
  <!-- conteúdo -->
  <div class="check-overlay" *ngIf="isConfirmed">
    <svg class="check-icon" viewBox="0 0 24 24">
      <path class="check-path" d="M5 13l4 4L19 7" />
    </svg>
  </div>
</div>
```

```scss
.check-path {
  stroke-dasharray: 30;
  stroke-dashoffset: 30;
  transition: stroke-dashoffset 400ms cubic-bezier(0.5, 1.25, 0.75, 1.25);
}
.confirmed .check-path {
  stroke-dashoffset: 0;
}
.action-card.confirmed {
  animation: pulse-success 600ms ease-out;
}
@keyframes pulse-success {
  0%, 100% { background: var(--color-surface); }
  50% { background: rgba(var(--color-success-500-rgb), 0.15); }
}
```

Check animado + flash de cor de sucesso = celebração sem confetti.

### 6. Skeleton shimmer

```scss
.skeleton {
  background: linear-gradient(90deg,
    var(--color-surface-secondary) 25%,
    var(--color-surface-elevated) 50%,
    var(--color-surface-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 7. Celebrações (uso raro, impacto alto)

Fim de onboarding, primeiro pagamento confirmado, serviço concluído. Uma vez — não toda ação.

```typescript
// Confetti minimal com canvas (não lib 50KB)
function celebrate() {
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:9999';
  document.body.appendChild(canvas);
  // ... 60 partículas, 1.5s, fade out
  setTimeout(() => canvas.remove(), 1800);
}
```

## prefers-reduced-motion

**Obrigatório**. Respeitar sempre:

```scss
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Alternativa para animações essenciais (ex: skeleton): deixar mas ajustar:
```scss
@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
    background: var(--color-surface-secondary); /* solid sem shimmer */
  }
}
```

Em JS:
```typescript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (prefersReducedMotion) {
  // pular animação custom, ir direto ao estado final
}
```

## Performance

### Apenas `transform` e `opacity`

```scss
/* ❌ causa reflow/repaint */
.bad { transition: width 200ms, top 200ms, margin 200ms; }

/* ✅ composited — 60fps garantido */
.good { transition: transform 200ms, opacity 200ms; }
```

Propriedades "baratas" (GPU):
- `transform: translate/scale/rotate/skew`
- `opacity`
- `filter` (cuidado, pode ser caro)

Propriedades "caras" (reflow):
- `width`, `height`, `top`, `left`, `padding`, `margin`
- `display`, layout-related

### `will-change` com moderação

```scss
.card {
  /* não usar sempre — hint de GPU layer custa memória */
}
.card:hover {
  will-change: transform;  /* avisa o browser antes */
  transform: translateY(-2px);
}
```

Usar apenas em elementos que **vão** animar, e remover após. Excesso de `will-change` aumenta uso de memória.

### FLIP technique para mudanças de layout

Para animar mudanças de posição:
1. **First** — capture posição inicial
2. **Last** — vá para posição final (sem animação)
3. **Invert** — aplique transform inverso para estar visualmente onde estava
4. **Play** — anime o transform para zero

```typescript
function animateLayout(el: HTMLElement, action: () => void) {
  const first = el.getBoundingClientRect();
  action();
  const last = el.getBoundingClientRect();
  const dx = first.left - last.left;
  const dy = first.top - last.top;
  el.animate([
    { transform: `translate(${dx}px, ${dy}px)` },
    { transform: 'translate(0, 0)' },
  ], { duration: 300, easing: 'cubic-bezier(0.2, 0, 0.0, 1)' });
}
```

View Transitions API (navegadores modernos):
```typescript
document.startViewTransition(() => {
  // atualiza DOM — browser anima diff
  updateList(newItems);
});
```

## Route transitions (Ionic / mobile)

```typescript
// app.module.ts
IonicModule.forRoot({
  navAnimation: customPageTransition,
})

function customPageTransition(baseEl: HTMLElement, opts?: any): Animation {
  const { enteringEl, leavingEl } = opts;
  const rootAnim = createAnimation().duration(300).easing('cubic-bezier(0.32, 0.72, 0, 1)');
  
  const enterAnim = createAnimation()
    .addElement(enteringEl)
    .fromTo('transform', 'translateX(100%)', 'translateX(0)')
    .fromTo('opacity', 0.5, 1);
  
  const leaveAnim = createAnimation()
    .addElement(leavingEl)
    .fromTo('transform', 'translateX(0)', 'translateX(-30%)')
    .fromTo('opacity', 1, 0.5);
  
  return rootAnim.addAnimation([enterAnim, leaveAnim]);
}
```

Padrão iOS: slide horizontal. Android: pode ser fade ou slide vertical. Seguir plataforma.

## Haptic feedback (mobile)

```typescript
import { Haptics, ImpactStyle, NotificationType } from '@capacitor/haptics';

// Ação comum: tap light
await Haptics.impact({ style: ImpactStyle.Light });

// Ação crítica: tap medium
await Haptics.impact({ style: ImpactStyle.Medium });

// Sucesso após ação: success haptic
await Haptics.notification({ type: NotificationType.Success });

// Erro: warning haptic
await Haptics.notification({ type: NotificationType.Warning });
```

Regra: **apenas em ações iniciadas pelo usuário**, nunca passivo (nunca em notificação que chega sozinha).

## Anti-patterns

- Animação > 500ms bloqueando ação crítica — usuário percebe "app lento"
- Loop sem pausa (rotate infinito) sem reason claro — drena bateria mobile
- `setInterval` para animação — usar `requestAnimationFrame` ou CSS
- Animar `width`/`height`/`top`/`left` — sempre transform
- Ignorar `prefers-reduced-motion` — viola a11y
- Spinner genérico em tudo — skeleton é melhor para lista, progress bar para upload
- Parallax em mobile — causa motion sickness
- Celebração em toda ação (vira ruído) — reservar para momentos marcantes
- Micro-interação sem propósito ("ficou legal") — cognitivo overhead sem benefício
- Haptic em scroll ou ação passiva — incomoda
- Animação custom que ignora tokens do design system — quebra consistência

## Testando animação

### Testes unitários
```typescript
it('shows check icon when confirmed', () => {
  component.isConfirmed = true;
  fixture.detectChanges();
  const check = fixture.nativeElement.querySelector('.check-icon');
  expect(check).toBeTruthy();
});
```
Comportamento testável (elemento aparece), não física (duração exata).

### Testes visuais
Chromatic captura frames de animação se configurado. Alternativa: `pauseAnimationAtEnd` nas stories.

### Testes manuais
- Diferentes devices (iPhone SE velho → iPhone 15): animação suave em todos?
- `prefers-reduced-motion` ligado: UI ainda funcional?
- Rede lenta: transições não bloqueando UX?

## Checklist para PLAN.md

- [ ] Animações novas usam tokens de duration/easing do design system
- [ ] Apenas `transform` e `opacity` — zero `width`/`height`/`top`/`left`
- [ ] `prefers-reduced-motion` respeitado em todas as animações novas
- [ ] Feedback de clique (scale/color) em todos os botões/cards interativos
- [ ] State change < 300ms
- [ ] Transições de contexto com entrada > saída em duração
- [ ] Celebrações reservadas a momentos marcantes (1-2 por fluxo, máximo)
- [ ] Haptic em ações mobile iniciadas pelo usuário (quando aplicável)
- [ ] Skeletons em vez de spinner para lista/card
- [ ] Teste em device real lento (iPhone SE ou equivalente Android antigo)
