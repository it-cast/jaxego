# Skill: motion-design-patterns

> Motion design com propósito: duration/easing tokens, page transitions, micro-interactions, spring physics, respeito a reduced motion.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

Animação boa reforça percepção ("isso cai aqui, aquilo some"), animação ruim cansa e atrapalha. Esta skill define quando usar animação, qual duração, qual easing, e o que **não** animar.

## Quando usar (triggers)

- Transição entre telas ou estados
- Feedback após ação (button press, toggle)
- Aparecimento/desaparecimento de elemento
- Skeleton loader, shimmer
- Entrada de dados em lista

## Quando NÃO usar

- Decoração gratuita ("ficou bonito") — animação tem que ter função
- Conteúdo essencial — não pode bloquear leitura por 2 segundos

---

## Princípios (inspirado em Material Motion)

### 1. Informativo, não decorativo

Cada animação responde:
- **De onde vem?** (origem)
- **Para onde vai?** (destino)
- **Por que agora?** (causa — clique, load, notificação)

### 2. Duração por intenção

| Contexto | Duration | Uso |
|---|---|---|
| Micro (hover, press) | 150ms (`--app-duration-fast`) | Feedback tátil imediato |
| Padrão (toggle, fade) | 250ms (`--app-duration-base`) | Maioria das UI changes |
| Lento (modal enter, page transition) | 400ms (`--app-duration-slow`) | Mudança de contexto grande |
| Muito lento (elementos grandes) | 600ms | Raro — navegação full-screen |

**Regra:** nunca animar > 600ms. Parece travado.

### 3. Easing por movimento

| Easing | Token | Quando |
|---|---|---|
| Ease-out | `--app-easing-out` | Elemento entrando (sai rápido, chega devagar) |
| Ease-in | `--app-easing-in` | Elemento saindo (começa devagar, sai rápido) |
| Default (ease-in-out) | `--app-easing-default` | Movimento entre 2 estados |
| Linear | `linear` | Só para progress bar e spinner (constante) |

**Nunca** `ease` puro — visual datado.

---

## Padrões concretos

### 1. Hover em card (micro)

```scss
.card {
  transition:
    transform var(--app-duration-fast) var(--app-easing-out),
    box-shadow var(--app-duration-fast) var(--app-easing-out);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--app-shadow-lg);
}

.card:active {
  transform: translateY(0);
  box-shadow: var(--app-shadow-sm);
  transition-duration: 50ms;  // feedback instantâneo ao clicar
}
```

### 2. Fade-in de modal

```scss
.modal-backdrop {
  opacity: 0;
  animation: fadeIn var(--app-duration-base) var(--app-easing-out) forwards;
}

.modal {
  opacity: 0;
  transform: translateY(20px) scale(0.98);
  animation: slideUpIn var(--app-duration-slow) var(--app-easing-out) forwards;
}

@keyframes fadeIn { to { opacity: 1; } }
@keyframes slideUpIn {
  to { opacity: 1; transform: translateY(0) scale(1); }
}
```

### 3. Skeleton shimmer

```scss
.skeleton {
  background: linear-gradient(
    90deg,
    var(--app-gray-200) 0%,
    var(--app-gray-100) 50%,
    var(--app-gray-200) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
  border-radius: var(--app-radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 4. Lista entrando (stagger)

```scss
.list-item {
  opacity: 0;
  transform: translateY(8px);
  animation: listIn var(--app-duration-base) var(--app-easing-out) forwards;
}

.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 40ms; }
.list-item:nth-child(3) { animation-delay: 80ms; }
.list-item:nth-child(4) { animation-delay: 120ms; }
.list-item:nth-child(5) { animation-delay: 160ms; }
// ... stagger max de 6 elementos
// depois do 6º, sem delay (não animar lista gigante)

@keyframes listIn {
  to { opacity: 1; transform: translateY(0); }
}
```

### 5. Page transition (Ionic já cuida no mobile)

Ionic faz automaticamente com `NavController`. No admin web:

```typescript
import { Router, NavigationEnd } from '@angular/router';

// app.component.ts
constructor(router: Router) {
  router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe(() => {
    document.querySelector('main')?.classList.remove('page-in');
    requestAnimationFrame(() => {
      document.querySelector('main')?.classList.add('page-in');
    });
  });
}
```

```scss
main {
  opacity: 0;
  transform: translateY(12px);
  transition:
    opacity var(--app-duration-slow) var(--app-easing-out),
    transform var(--app-duration-slow) var(--app-easing-out);
}

main.page-in {
  opacity: 1;
  transform: translateY(0);
}
```

### 6. Toast entrando/saindo

```scss
.toast {
  transform: translateY(-100%);
  animation: toastIn var(--app-duration-base) var(--app-easing-out) forwards;
}

.toast.leaving {
  animation: toastOut var(--app-duration-fast) var(--app-easing-in) forwards;
}

@keyframes toastIn { to { transform: translateY(0); } }
@keyframes toastOut { to { transform: translateY(-100%); opacity: 0; } }
```

### 7. Button loading state

```html
<button [disabled]="loading()" class="btn">
  <span [class.invisible]="loading()">Salvar</span>
  @if (loading()) {
    <mat-spinner class="btn-spinner" diameter="16" />
  }
</button>
```

```scss
.btn { position: relative; }
.btn .invisible { visibility: hidden; }  // mantém largura
.btn-spinner {
  position: absolute;
  inset: 0;
  margin: auto;
}
```

### 8. Number counter animado (dashboard KPI)

```typescript
@Component({
  selector: 'app-counter',
  template: `<span>{{ current() | number:'1.0-0':'pt-BR' }}</span>`,
})
export class CounterComponent {
  @Input({ required: true }) set value(v: number) { this.target.set(v); }

  target = signal(0);
  current = signal(0);

  constructor() {
    effect(() => {
      const target = this.target();
      const start = this.current();
      const duration = 600;
      const startTime = performance.now();

      const tick = (now: number) => {
        const t = Math.min(1, (now - startTime) / duration);
        const eased = 1 - Math.pow(1 - t, 3);  // ease-out cubic
        this.current.set(Math.round(start + (target - start) * eased));
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
}
```

---

## Spring physics (opcional, elevado)

CSS puro + `cubic-bezier` cobre 95%. Para bouncy (confetti, drawer), use:

```typescript
// Opcional: @motionone/animation
import { animate } from 'motion';

animate(element, { transform: ['scale(0.9)', 'scale(1)'] }, {
  duration: 0.6,
  easing: [0.5, 1.5, 0.5, 1],  // spring feeling
});
```

Mobile (Ionic): use `Animations API` do próprio Ionic:

```typescript
import { AnimationController } from '@ionic/angular/standalone';

const anim = this.animationCtrl.create()
  .addElement(this.el.nativeElement)
  .duration(400)
  .easing('cubic-bezier(0.25, 1.5, 0.5, 1)')  // bouncy
  .fromTo('opacity', '0', '1')
  .fromTo('transform', 'scale(0.9)', 'scale(1)');

anim.play();
```

---

## Reduced motion (obrigatório)

Sempre, em todo arquivo que tem animação:

```scss
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Para animação essencial (spinner), reduza em vez de zerar:

```scss
.spinner {
  animation: spin 1s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .spinner { animation-duration: 2s; }
}
```

---

## Performance

### Anime só `transform` e `opacity`

```scss
/* ✅ GPU-acelerado */
.card { transition: transform 250ms; }

/* ❌ Force reflow */
.card { transition: width 250ms, top 250ms, margin 250ms; }
```

### `will-change` com cuidado

```scss
.modal { will-change: transform, opacity; }
/* Só em elementos que REALMENTE vão animar em breve — senão come memória */
```

### Remova animação após fim

```typescript
element.addEventListener('animationend', () => {
  element.style.animation = '';  // libera GPU
}, { once: true });
```

---

## Anti-patterns

1. ❌ **Animar `width`, `height`, `top`, `left`** — force reflow; use `transform`
2. ❌ **Duration > 600ms** — parece travado
3. ❌ **`ease` puro** (`transition: 300ms ease`) — visual de 2010; use cubic-bezier
4. ❌ **Animação infinita decorativa** fora de loaders — cansa
5. ❌ **Stagger em lista de 100 items** — últimos aparecem depois de 4s; limite a 6
6. ❌ **Transition sem `prefers-reduced-motion`** — barreira de acessibilidade
7. ❌ **Animação de entrada mas não de saída** — elemento "some" sem explicação
8. ❌ **`scroll-behavior: smooth`** global — scroll programático fica lento em listas longas
9. ❌ **Hover effect em mobile** (`:hover`) — fica "presa" após toque
10. ❌ **`animation-delay` cumulativo gigante** — último elemento demora ver

---

## Checklist de review

- [ ] Animações usam tokens `--app-duration-*` e `--app-easing-*`
- [ ] Duração ≤ 400ms (padrão); > 400ms só em transição de página
- [ ] `transform` e `opacity` são as propriedades animadas (não `width`, `top`)
- [ ] `prefers-reduced-motion` respeitado
- [ ] Hover effects não aplicados em mobile (`@media (hover: hover)`)
- [ ] Lista staggered limita stagger a 6 elementos
- [ ] Animações de entrada têm equivalente de saída
- [ ] Spinners e skeletons são a única animação "infinita"
- [ ] Page transitions via Ionic NavController (mobile) ou route transition (web)
- [ ] Performance: sem jank visível em listas longas

<!-- Skill aplicada: todo SCSS com @keyframes, transition, animation -->
