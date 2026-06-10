---
name: payment-checkout-ux
description: Padrões de UX para fluxo de pagamento no {PROJETO}. Cobre Pix (QR code, cópia, polling), cartão de crédito (máscara BR, CVV, CPF titular), fee breakdown, estados de loading/sucesso/erro. Use em qualquer tela de pagamento.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Payment Checkout UX

> O pagamento é o momento de maior ansiedade do usuário. Cada friction aqui = abandono.

---

## 1. Quando usar

- `apps/mobile/src/app/client/pages/payment/`
- Qualquer componente de resumo de pedido com CTA de pagamento
- Tela de confirmação pós-pagamento

---

## 2. Seleção de método (Pix vs Cartão)

```html
<ion-segment [(ngModel)]="method" color="primary">
  <ion-segment-button value="pix">
    <ion-label>
      <ion-icon name="qr-code-outline"></ion-icon>
      Pix
    </ion-label>
    <p class="method-hint">Aprovado em até 1 minuto</p>
  </ion-segment-button>
  <ion-segment-button value="credit_card">
    <ion-label>
      <ion-icon name="card-outline"></ion-icon>
      Cartão
    </ion-label>
    <p class="method-hint">Crédito ou débito</p>
  </ion-segment-button>
</ion-segment>
```

```scss
.method-hint {
  font-size: 10px;
  color: var(--app-text-tertiary);
  margin: 0;
  font-weight: 400;
}
```

---

## 3. Fluxo Pix

### QR Code display
```scss
.pix-qr-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-md);
  padding: var(--sp-xl);
}

.pix-qr-img {
  width: 240px;
  height: 240px;
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--radius-md);
  padding: var(--sp-md);
  background: white; // QR code sempre em fundo branco
}

.pix-code-copy {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  width: 100%;
  background: var(--app-surface-page);
  border-radius: var(--radius-md);
  padding: var(--sp-sm) var(--sp-md);
  border: 1px dashed var(--app-border-subtle);
}

.pix-countdown {
  font-size: var(--type-caption);
  color: var(--app-text-tertiary);
  // Vermelho quando < 5 minutos
  &.countdown--urgent { color: var(--app-error); font-weight: 600; }
}
```

### Auto-poll de status
```typescript
private startPolling(): void {
  // Polling a cada 5s, máximo 12 tentativas (1 minuto)
  this.pollInterval = interval(5000).pipe(
    take(12),
    switchMap(() => this.paymentService.checkStatus(this.paymentId()))
  ).subscribe(status => {
    if (status === 'paid') {
      this.onPaymentSuccess();
    }
  });
}

ngOnDestroy(): void {
  this.pollInterval?.unsubscribe(); // NUNCA esquecer de cancelar
}
```

### Cópia do código
```typescript
async copyPixCode(): Promise<void> {
  await Clipboard.write({ string: this.pixCode() });
  // Toast de confirmação (não alert)
  const toast = await this.toastCtrl.create({
    message: 'Código copiado!',
    duration: 2000,
    position: 'bottom',
    color: 'success'
  });
  await toast.present();
}
```

---

## 4. Formulário de cartão (contexto brasileiro)

```html
<form [formGroup]="cardForm">
  <!-- Número do cartão -->
  <ion-input
    label="Número do cartão"
    labelPlacement="floating"
    formControlName="cardNumber"
    inputmode="numeric"
    [maskito]="cardMask"
    placeholder="0000 0000 0000 0000">
  </ion-input>

  <div class="card-row">
    <!-- Validade -->
    <ion-input
      label="Validade"
      labelPlacement="floating"
      formControlName="expiry"
      inputmode="numeric"
      [maskito]="expiryMask"
      placeholder="MM/AA">
    </ion-input>

    <!-- CVV -->
    <ion-input
      label="CVV"
      labelPlacement="floating"
      formControlName="cvv"
      inputmode="numeric"
      maxlength="4"
      placeholder="000">
    </ion-input>
  </div>

  <!-- Nome impresso -->
  <ion-input
    label="Nome no cartão"
    labelPlacement="floating"
    formControlName="holderName"
    autocomplete="cc-name"
    enterkeyhint="next">
  </ion-input>

  <!-- CPF do titular (obrigatório no Brasil) -->
  <ion-input
    label="CPF do titular"
    labelPlacement="floating"
    formControlName="cpf"
    inputmode="numeric"
    [maskito]="cpfMask"
    placeholder="000.000.000-00">
  </ion-input>
</form>
```

```typescript
// Máscaras Maskito para cartão
readonly cardMask: MaskitoOptions = {
  mask: [/\d/,/\d/,/\d/,/\d/,' ',/\d/,/\d/,/\d/,/\d/,' ',/\d/,/\d/,/\d/,/\d/,' ',/\d/,/\d/,/\d/,/\d/]
};
readonly expiryMask: MaskitoOptions = {
  mask: [/\d/,/\d/,'/',/\d/,/\d/]
};
```

---

## 5. Order summary (obrigatório antes de pagar)

```html
<div class="order-summary">
  <div class="summary-row">
    <span class="summary-label">{{ serviceName }}</span>
    <span>R$ {{ servicePrice | number:'1.2-2' }}</span>
  </div>
  <div class="summary-row summary-row--fee">
    <span>Taxa da plataforma (12%)</span>
    <span>R$ {{ platformFee | number:'1.2-2' }}</span>
    <ion-icon
      name="information-circle-outline"
      class="fee-info-icon"
      (click)="showFeeInfo()">
    </ion-icon>
  </div>
  <div class="summary-row summary-row--total">
    <strong>Total</strong>
    <strong>R$ {{ total | number:'1.2-2' }}</strong>
  </div>
</div>

<!-- Trust indicator -->
<div class="escrow-note">
  <ion-icon name="lock-closed-outline"></ion-icon>
  <span>Seu pagamento fica retido até a conclusão confirmada do serviço</span>
</div>
```

---

## 6. Estados pós-pagamento

### Processing (full-screen — bloquear navegação)
```html
<div class="payment-processing" *ngIf="processing()">
  <ion-spinner name="crescent" color="primary"></ion-spinner>
  <p>Processando pagamento...</p>
  <p class="processing-hint">Não feche este aplicativo</p>
</div>
```

### Success
```html
<div class="payment-success">
  <ion-icon name="checkmark-circle" class="success-icon"></ion-icon>
  <h2>Pagamento confirmado!</h2>
  <p>Seu serviço foi contratado. O profissional será notificado.</p>
  <ion-button expand="block" (click)="goToServiceDetail()">
    Ver detalhes do serviço
  </ion-button>
</div>
```

```scss
.success-icon {
  font-size: 72px;
  color: var(--app-success);
  animation: success-pop 0.4s var(--ease-default);

  @media (prefers-reduced-motion: reduce) { animation: none; }
}
@keyframes success-pop {
  0% { transform: scale(0.5); opacity: 0; }
  70% { transform: scale(1.1); }
  100% { transform: scale(1); opacity: 1; }
}
```

### Error
```typescript
// NUNCA mostrar código de erro do {gateway-pagamento} para o usuário
const friendlyErrors: Record<number, string> = {
  1: 'Cartão recusado. Verifique os dados ou tente outro cartão.',
  2: 'Saldo insuficiente. Tente outro cartão ou use Pix.',
  3: 'Cartão expirado. Atualize a data de validade.',
  default: 'Não foi possível processar o pagamento. Tente novamente.'
};
```

---

## 7. Anti-patterns

- ❌ Nunca mostrar total sem breakdown de taxa (trust killer)
- ❌ Nunca auto-navegar para sucesso antes da confirmação do webhook {gateway-pagamento}
- ❌ Nunca usar `window.open` para Pix (usar Capacitor Clipboard + toast)
- ❌ Nunca mostrar código de erro interno do {gateway-pagamento} (ex: "HasError: true, Error: 401")
- ❌ Nunca deixar o polling rodando após componente destruído (memory leak)
- ❌ Nunca validar cartão só no frontend — sempre validar no backend também
- ❌ Nunca esconder o campo CPF do titular (obrigatório para cartões BR)
