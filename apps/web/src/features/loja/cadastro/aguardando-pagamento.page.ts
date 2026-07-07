import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { MerchantService } from './merchant.service';

@Component({
  selector: 'jx-aguardando-pagamento',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-aguardando">
      <header class="jx-aguardando__header">
        <h1 class="jx-h1">
          @if (confirmed()) { Pagamento confirmado! } @else { Aguardando pagamento }
        </h1>
        @if (!confirmed()) {
          <p class="jx-aguardando__sub">
            Pague pelo seu banco para ativar o plano. A confirmação é automática.
          </p>
        }
      </header>

      @if (confirmed()) {
        <div class="jx-aguardando__success">
          <div class="jx-aguardando__success-icon" aria-hidden="true">✓</div>
          <p class="jx-aguardando__success-msg">
            Sua assinatura foi ativada. Bem-vindo ao Jaxego!
          </p>
          <button type="button" class="jx-aguardando__submit" (click)="goToSystem()">
            Acessar o sistema
          </button>
        </div>
      } @else {
        @if (loading()) {
          <p class="jx-aguardando__note" role="status">Carregando dados do pagamento…</p>
        }

        @if (error()) {
          <p class="jx-aguardando__error" role="alert">{{ error() }}</p>
        }

        @if (!loading() && !error()) {
          <div class="jx-aguardando__pix-result">
            @if (qrImage()) {
              <img [src]="qrImage()!" alt="QR Code PIX" class="jx-aguardando__pix-qr" />
            }
            @if (qrCode()) {
              <p class="jx-aguardando__pix-code">{{ qrCode() }}</p>
              <button type="button" class="jx-aguardando__back" (click)="copyCode()">
                {{ copied() ? 'Copiado!' : 'Copiar código PIX' }}
              </button>
            }
            <p class="jx-aguardando__pix-note" role="status">
              Pague pelo seu banco. A assinatura ativa automaticamente após a confirmação.
            </p>
          </div>
        }
      }
    </main>
  `,
  styles: [`
    .jx-aguardando {
      display: block;
      max-width: 520px;
      margin: var(--jx-space-6) auto;
      padding: 0 var(--jx-space-4);
    }

    .jx-aguardando__header {
      margin-bottom: var(--jx-space-5);
    }

    .jx-aguardando__sub {
      margin-top: var(--jx-space-2);
      font-size: var(--jx-text-sm);
      color: var(--text-muted);
    }

    /* PIX result — mesma estrutura do cadastro */
    .jx-aguardando__pix-result {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--jx-space-3);
    }

    .jx-aguardando__pix-qr {
      width: 200px;
      border-radius: var(--jx-radius-md);
    }

    .jx-aguardando__pix-code {
      font-family: var(--jx-font-mono);
      font-size: var(--jx-text-xs);
      word-break: break-all;
      background: var(--surface-sunken);
      padding: var(--jx-space-2) var(--jx-space-3);
      border-radius: var(--jx-radius-sm);
      margin: 0;
      width: 100%;
      overflow-x: auto;
    }

    .jx-aguardando__pix-note {
      margin: 0;
      font-size: var(--jx-text-sm);
      color: var(--text-muted);
      text-align: center;
    }

    /* Botão secundário (copiar) */
    .jx-aguardando__back {
      width: 100%;
      min-height: 44px;
      padding: var(--jx-space-4);
      background: transparent;
      color: var(--text, #1a1a1a);
      border: 1px solid var(--border);
      border-radius: var(--jx-radius-md);
      font-size: var(--jx-text-base);
      cursor: pointer;
    }

    /* Tela de confirmação */
    .jx-aguardando__success {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--jx-space-4);
      text-align: center;
      padding: var(--jx-space-6) 0;
    }

    .jx-aguardando__success-icon {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: var(--jx-color-success, #22c55e);
      color: #fff;
      font-size: 2rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
    }

    .jx-aguardando__success-msg {
      font-size: var(--jx-text-lg);
      margin: 0;
    }

    /* Botão primário (acessar sistema) */
    .jx-aguardando__submit {
      width: 100%;
      min-height: 44px;
      padding: var(--jx-space-4);
      background: var(--brand);
      color: var(--brand-contrast);
      border: none;
      border-radius: var(--jx-radius-md);
      font-size: var(--jx-text-base);
      font-weight: 600;
      cursor: pointer;
    }

    .jx-aguardando__submit:hover {
      background: var(--brand-hover);
    }

    .jx-aguardando__note {
      font-size: var(--jx-text-sm);
      color: var(--text-muted);
    }

    .jx-aguardando__error {
      color: var(--jx-color-error);
      font-size: var(--jx-text-sm);
    }
  `],
})
export class AguardandoPagamentoPage implements OnInit, OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly merchants = inject(MerchantService);
  private readonly router = inject(Router);

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly qrImage = signal<string | null>(null);
  protected readonly qrCode = signal<string | null>(null);
  protected readonly confirmed = signal(false);
  protected readonly copied = signal(false);

  private pollTimer: ReturnType<typeof setInterval> | null = null;

  async ngOnInit(): Promise<void> {
    if (!this.auth.isAuthenticated()) {
      void this.router.navigate(['/entrar']);
      return;
    }
    await this.loadSubscription();
    if (!this.confirmed()) {
      this.startPolling();
    }
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  private async loadSubscription(): Promise<void> {
    const sub = await this.merchants.getSubscription();
    this.loading.set(false);
    if (!sub) {
      this.error.set('Não foi possível carregar os dados do pagamento. Tente recarregar a página.');
      return;
    }
    if (sub.billing_status === 'active') {
      this.confirmed.set(true);
      return;
    }
    this.qrImage.set(sub.qr_code_base64 ?? null);
    this.qrCode.set(sub.qr_code ?? null);
  }

  private startPolling(): void {
    this.pollTimer = setInterval(() => void this.checkStatus(), 5000);
  }

  private stopPolling(): void {
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private async checkStatus(): Promise<void> {
    const sub = await this.merchants.getSubscription();
    if (sub?.billing_status === 'active') {
      this.stopPolling();
      this.confirmed.set(true);
    }
  }

  protected async copyCode(): Promise<void> {
    const code = this.qrCode();
    if (!code) return;
    await navigator.clipboard.writeText(code);
    this.copied.set(true);
    setTimeout(() => this.copied.set(false), 2000);
  }

  protected goToSystem(): void {
    void this.router.navigate(['/loja']);
  }
}
