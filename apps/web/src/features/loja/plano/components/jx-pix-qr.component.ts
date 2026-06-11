import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  signal,
} from '@angular/core';

export type PixState = 'aguardando' | 'aprovado' | 'expirado';

/**
 * jx-pix-qr — PIX automático QR + copia-e-cola + deep link (UI-SPEC §6.3).
 *
 * Renders the base64 QR image (with alt) + the EMV copy-paste string (mono) + a copy
 * button + an optional deep link. The waiting state is `role="status"` `aria-live=polite`
 * (the activation arrives by webhook; the UI only reflects the status). Expired → an
 * actionable "Gerar novo QR Code". The copy-paste alternative is ALWAYS present (does not
 * depend on a camera). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-pix-qr',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-pix">
      @if (state() === 'aprovado') {
        <p class="jx-pix__ok" role="status">Pagamento confirmado. Plano ativado.</p>
      } @else if (state() === 'expirado') {
        <div class="jx-pix__expired" role="alert">
          <p>Esse código PIX expirou. Gere um novo para continuar.</p>
          <button type="button" class="jx-pix__regen" (click)="regenerate.emit()">
            Gerar novo QR Code
          </button>
        </div>
      } @else {
        @if (qrBase64()) {
          <img
            class="jx-pix__img"
            [src]="'data:image/png;base64,' + qrBase64()"
            alt="QR Code PIX para pagamento da assinatura"
            width="200"
            height="200"
          />
        }
        <div class="jx-pix__copy">
          <code class="jx-pix__code">{{ qrCode() }}</code>
          <button type="button" class="jx-pix__copy-btn" (click)="copy()" aria-label="Copiar código PIX">
            Copiar código
          </button>
        </div>
        @if (deepLink) {
          <a class="jx-pix__deep" [href]="deepLink">Abrir app do banco</a>
        }
        <p class="jx-pix__waiting" role="status" aria-live="polite">
          Aguardando o pagamento. Assim que cair, seu plano é ativado.
        </p>
      }
    </div>
  `,
  styleUrl: './jx-pix-qr.component.scss',
})
export class PixQrComponent {
  protected readonly qrCode = signal('');
  protected readonly qrBase64 = signal('');
  protected readonly state = signal<PixState>('aguardando');
  @Input() deepLink: string | null = null;

  @Input()
  set copyPaste(v: string | null) {
    this.qrCode.set(v ?? '');
  }
  @Input()
  set image(v: string | null) {
    this.qrBase64.set(v ?? '');
  }
  @Input()
  set pixState(v: PixState) {
    this.state.set(v);
  }

  @Output() regenerate = new EventEmitter<void>();
  @Output() copied = new EventEmitter<void>();

  protected async copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.qrCode());
      this.copied.emit();
    } catch {
      // Clipboard blocked — the code is visible for manual copy (always present).
    }
  }
}
