import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { FieldComponent } from '../../../../shared/components';
import { PaymentCryptoService } from '../payment-crypto.service';

export type CardFormState = 'idle' | 'cifrando' | 'aprovado' | 'recusado';

/**
 * jx-card-form — card entry that encrypts with RSA-OAEP IN THE BROWSER before sending
 * (UI-SPEC §6.2 / D-02 / TH-A). The plaintext card stays in local component fields and
 * is encrypted to a base64 blob via PaymentCryptoService; it NEVER goes to global state,
 * a log, analytics, storage or the URL. CVV is never pre-filled; `autocomplete="off"`.
 *
 * Inline validation (Luhn / non-expired / CVV length) at blur, error associated by
 * jx-field aria-describedby. A trust band states the platform does NOT store the number
 * (trust-safety-ux). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-card-form',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FieldComponent, FormsModule],
  template: `
    <form class="jx-card-form" (ngSubmit)="submit()" autocomplete="off" novalidate>
      <jx-field
        label="Nome no cartão"
        autocomplete="cc-name"
        [(ngModel)]="holder"
        name="holder"
        [error]="errors().holder"
      />
      <jx-field
        label="Número do cartão"
        inputmode="numeric"
        autocomplete="cc-number"
        [mono]="true"
        [(ngModel)]="number"
        name="number"
        (blurred)="validateNumber()"
        [error]="errors().number"
      />
      <div class="jx-card-form__row">
        <jx-field
          label="Validade (MM/AAAA)"
          inputmode="numeric"
          autocomplete="cc-exp"
          [mono]="true"
          [(ngModel)]="expiry"
          name="expiry"
          (blurred)="validateExpiry()"
          [error]="errors().expiry"
        />
        <jx-field
          label="CVV"
          inputmode="numeric"
          autocomplete="cc-csc"
          [mono]="true"
          [maxlength]="4"
          [(ngModel)]="cvv"
          name="cvv"
          (blurred)="validateCvv()"
          [error]="errors().cvv"
        />
      </div>

      <p class="jx-card-form__trust">
        <span aria-hidden="true">🔒</span>
        Seus dados são criptografados no seu navegador antes de enviar. A Jaxegô não armazena
        o número do seu cartão.
      </p>

      @if (state() === 'recusado') {
        <p class="jx-card-form__error" role="alert">
          Não foi possível processar este cartão. Confira os dados ou use outro cartão. Você
          também pode pagar por PIX.
        </p>
      }

      <button
        type="submit"
        class="jx-card-form__cta"
        [disabled]="state() === 'cifrando' || state() === 'aprovado'"
        [attr.aria-busy]="state() === 'cifrando'"
      >
        {{ ctaLabel }}
      </button>
    </form>
  `,
  styleUrl: './jx-card-form.component.scss',
})
export class CardFormComponent {
  private readonly cryptoSvc = inject(PaymentCryptoService);

  @Input() ctaLabel = 'Confirmar pagamento';
  /** Emits the RSA-OAEP base64 blob — the ONLY thing that leaves this component. */
  @Output() cardEncrypted = new EventEmitter<string>();

  protected holder = '';
  protected number = '';
  protected expiry = '';
  protected cvv = '';

  protected readonly state = signal<CardFormState>('idle');
  protected readonly errors = signal<{
    holder?: string;
    number?: string;
    expiry?: string;
    cvv?: string;
  }>({});

  /** Set externally by the parent after the gateway responds. */
  setState(s: CardFormState): void {
    this.state.set(s);
  }

  protected validateNumber(): void {
    const digits = this.number.replace(/\D/g, '');
    const ok = digits.length >= 13 && digits.length <= 19 && luhn(digits);
    this.errors.update((e) => ({ ...e, number: ok ? undefined : 'Número de cartão inválido.' }));
  }

  protected validateExpiry(): void {
    const m = /^(\d{2})\/(\d{4})$/.exec(this.expiry.trim());
    let err: string | undefined = 'Use MM/AAAA.';
    if (m) {
      const month = Number(m[1]);
      const year = Number(m[2]);
      const now = new Date();
      const notExpired =
        month >= 1 &&
        month <= 12 &&
        (year > now.getFullYear() ||
          (year === now.getFullYear() && month >= now.getMonth() + 1));
      err = notExpired ? undefined : 'Cartão expirado.';
    }
    this.errors.update((e) => ({ ...e, expiry: err }));
  }

  protected validateCvv(): void {
    const ok = /^\d{3,4}$/.test(this.cvv.trim());
    this.errors.update((e) => ({ ...e, cvv: ok ? undefined : 'CVV inválido.' }));
  }

  protected async submit(): Promise<void> {
    this.validateNumber();
    this.validateExpiry();
    this.validateCvv();
    const e = this.errors();
    if (!this.holder || e.holder || e.number || e.expiry || e.cvv) return;

    this.state.set('cifrando');
    try {
      const blob = await this.cryptoSvc.encryptCard({
        nomeTitular: this.holder,
        numeroCartao: this.number.replace(/\s/g, ''),
        validade: this.expiry.trim(),
        cvv: this.cvv.trim(),
      });
      // Clear the plaintext fields immediately — only the blob survives.
      this.number = '';
      this.cvv = '';
      this.cardEncrypted.emit(blob);
    } catch {
      this.state.set('recusado');
    }
  }
}

/** Luhn checksum (client-side display validation only — server is authoritative). */
function luhn(digits: string): boolean {
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = Number(digits[i]);
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}
