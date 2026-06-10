---
name: form-ux-mastery
description: Padrões de UX para formulários no {PROJETO}. Cobre multi-step, validação inline, campos adaptativos, teclado mobile, feedback de erro amigável e submit seguro. Use em qualquer formulário de cadastro, edição ou solicitação.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Form UX Mastery

> Um formulário mal projetado é a segunda maior causa de abandono. A primeira é a taxa inesperada.

---

## 1. Quando usar

- `apps/mobile/src/app/shared/pages/auth/` (login, register)
- Formulários de profissional (new-service, edit-service, portfolio)
- Qualquer `ion-input`, `ion-select`, `ion-textarea` no projeto
- Formulários do admin (`apps/admin/src/app/features/`)

---

## 2. Multi-step form (formulários longos)

Dividir em etapas de ≤ 5 campos cada. Nunca uma única tela com 10+ campos.

```html
<!-- Step indicator -->
<div class="form-steps">
  @for (step of steps; track step.id) {
    <div class="step-dot" [class.step-dot--active]="currentStep() === step.id"
                          [class.step-dot--done]="currentStep() > step.id">
    </div>
  }
</div>

<!-- Step content com animação de slide -->
<div class="step-container" [@slideStep]="currentStep()">
  @switch (currentStep()) {
    @case (1) { <ng-container *ngTemplateOutlet="step1"></ng-container> }
    @case (2) { <ng-container *ngTemplateOutlet="step2"></ng-container> }
    @case (3) { <ng-container *ngTemplateOutlet="step3"></ng-container> }
  }
</div>
```

```scss
.form-steps {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  justify-content: center;
  margin-bottom: var(--sp-xl);
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--app-border-subtle);
  transition: all var(--duration-base) var(--ease-default);

  &--active {
    width: 24px;
    border-radius: var(--radius-full);
    background: var(--app-gradient-cta);
  }

  &--done {
    background: var(--app-success);
  }
}
```

```typescript
// Animação de slide entre steps
export const slideStep = trigger('slideStep', [
  transition(':increment', [
    style({ transform: 'translateX(100%)', opacity: 0 }),
    animate('250ms var(--ease-default)', style({ transform: 'translateX(0)', opacity: 1 }))
  ]),
  transition(':decrement', [
    style({ transform: 'translateX(-100%)', opacity: 0 }),
    animate('250ms var(--ease-default)', style({ transform: 'translateX(0)', opacity: 1 }))
  ])
]);
```

---

## 3. Validação inline (não no submit)

```typescript
// Validar ao sair do campo (blur), não ao digitar
getErrorMessage(controlName: string): string | null {
  const control = this.form.get(controlName);
  if (!control?.touched || !control.errors) return null;

  if (control.errors['required']) return 'Campo obrigatório';
  if (control.errors['email']) return 'E-mail inválido';
  if (control.errors['minlength']) {
    return `Mínimo ${control.errors['minlength'].requiredLength} caracteres`;
  }
  if (control.errors['cpfInvalid']) return 'CPF inválido';
  if (control.errors['pattern']) return 'Formato inválido';
  return 'Campo inválido';
}
```

```html
<!-- Padrão de campo com erro inline -->
<ion-input
  label="E-mail"
  labelPlacement="floating"
  formControlName="email"
  type="email"
  inputmode="email"
  autocomplete="email"
  enterkeyhint="next"
  [class.ion-invalid]="form.get('email')?.touched && form.get('email')?.invalid"
  [class.ion-touched]="form.get('email')?.touched">
</ion-input>
@if (getErrorMessage('email')) {
  <p class="field-error" role="alert">
    <ion-icon name="alert-circle-outline"></ion-icon>
    {{ getErrorMessage('email') }}
  </p>
}
```

```scss
.field-error {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--type-caption);
  color: var(--app-error);
  margin: 4px 0 0 16px;
  animation: fadeIn var(--duration-fast) var(--ease-default);

  ion-icon { font-size: 14px; flex-shrink: 0; }
}
```

---

## 4. Keyboard UX no mobile (crítico)

```html
<!-- Sequência de campos: enterkeyhint define o botão do teclado -->
<ion-input formControlName="name"     enterkeyhint="next"  (keydown.enter)="focusNext('email')"></ion-input>
<ion-input formControlName="email"    enterkeyhint="next"  (keydown.enter)="focusNext('phone')"></ion-input>
<ion-input formControlName="phone"    enterkeyhint="next"  (keydown.enter)="focusNext('city')"></ion-input>
<ion-input formControlName="city"     enterkeyhint="done"  (keydown.enter)="submitForm()"></ion-input>
```

```typescript
// inputmode correto por tipo de campo
// text     → nome, cidade, descrição
// email    → e-mail
// tel      → telefone
// numeric  → CPF, cartão, CVV
// decimal  → preços
// url      → URLs
// search   → busca (lupa no teclado)
```

**Regras de teclado:**
- Último campo → `enterkeyhint="done"` ou `"send"` (chama submit)
- Campos numéricos → `inputmode="numeric"` NUNCA `type="number"` (evita spinner)
- Telefone → `type="tel"` com mask `(00) 00000-0000`
- Scroll automático para o campo ativo — Ionic faz isso nativamente com `IonContent`

---

## 5. Label flutuante (padrão {PROJETO})

```html
<!-- SEMPRE labelPlacement="floating" — nunca placeholder sem label -->
<ion-input
  label="Nome completo"
  labelPlacement="floating"
  formControlName="name"
  autocomplete="name">
</ion-input>

<!-- Placeholder só como dica de formato (não substitui label) -->
<ion-input
  label="Telefone"
  labelPlacement="floating"
  formControlName="phone"
  placeholder="(21) 99999-9999"
  inputmode="tel">
</ion-input>
```

---

## 6. Submit seguro (anti-double-submit)

```typescript
// Sinal de loading impede duplo envio
readonly submitting = signal<boolean>(false);

async onSubmit(): Promise<void> {
  if (this.form.invalid || this.submitting()) return;

  this.submitting.set(true);
  try {
    await this.service.save(this.form.value);
    // sucesso
  } catch (err) {
    // erro
  } finally {
    this.submitting.set(false);
  }
}
```

```html
<ion-button
  expand="block"
  type="submit"
  [disabled]="form.invalid || submitting()"
  (click)="onSubmit()">
  @if (submitting()) {
    <ion-spinner name="crescent" slot="start"></ion-spinner>
    Salvando...
  } @else {
    Salvar
  }
</ion-button>
```

---

## 7. Select e picker patterns

```html
<!-- Ion-Select com interface="action-sheet" para listas curtas (≤ 6 itens) -->
<ion-select
  label="Urgência"
  labelPlacement="floating"
  formControlName="urgency"
  interface="action-sheet">
  <ion-select-option value="normal">Normal (até 7 dias)</ion-select-option>
  <ion-select-option value="soon">Em breve (2-3 dias)</ion-select-option>
  <ion-select-option value="urgent">Urgente (hoje/amanhã)</ion-select-option>
</ion-select>

<!-- Ion-Select com interface="popover" para listas médias (7-15 itens) -->
<!-- Ion-Modal customizado para listas longas (16+ itens com busca) -->
```

---

## 8. Anti-patterns

- ❌ Nunca usar `type="number"` — usar `inputmode="numeric"` (evita spinner/+/- no mobile)
- ❌ Nunca validar só no submit — sempre inline ao blur
- ❌ Nunca placeholder como único label — usar `labelPlacement="floating"`
- ❌ Nunca permitir duplo submit — desabilitar botão imediatamente
- ❌ Nunca um formulário com 10+ campos em uma tela — multi-step obrigatório
- ❌ Nunca abrir teclado em campo numérico com `type="text"` (teclado full no mobile)
- ❌ Nunca mostrar erro antes do usuário tocar o campo
- ❌ Nunca mensagem genérica "Erro no formulário" — especificar qual campo e por quê
