import { ChangeDetectionStrategy, Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { MoneyComponent, type MoneySign } from '@jaxego/shared/components/money/money.component';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';
import { formatCents, maskBrl, parseBrl } from '@jaxego/shared/util/money';

interface CreditLedgerEntry {
  id: number;
  delivery_id: number | null;
  kind: 'reconciliation' | 'consumption' | 'reversal' | 'topup';
  amount_cents: number;
  reason: string | null;
  created_at: string | null;
}

interface CreditTopupResponse {
  charge_id: number;
  amount_cents: number;
  taxa_pix_cents: number;
  taxa_servico_cents: number;
  total_cents: number;
  qr_code: string | null;
  qr_code_base64: string | null;
}

// TEMPORÁRIO: mínimo de R$5 removido a pedido do usuário só pra teste — 1 cent
// é o piso técnico. Reintroduzir 500 (R$5) antes de ir pra produção.
const TOPUP_MIN_CENTS = 1;
const TOPUP_PRESETS_REAIS = [20, 50, 100, 200];
const POLL_INTERVAL_MS = 5000;

/**
 * Saldo/crédito da loja (extrato) — sobra/falta apurada na finalização das
 * entregas `platform_pix` (preço do entregador vs. valor pago no PIX),
 * consumo quando a loja escolhe usar saldo como desconto numa entrega nova,
 * e recarga manual via PIX (CORRECAO-260). Espelha
 * `apps/api/app/merchants/credit.py` + `GET /v1/merchants/credit-balance`,
 * `GET /v1/merchants/credit-ledger`, `POST /v1/merchants/credit-topup`.
 */
@Component({
  selector: 'jx-loja-saldo-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, MoneyComponent, ErrorStateComponent],
  templateUrl: './saldo.page.html',
  styleUrl: './saldo.page.scss',
})
export class LojaSaldoPage implements OnDestroy {
  private readonly http = inject(HttpClient);

  protected readonly balanceCents = signal(0);
  protected readonly balanceState = signal<'loading' | 'ready' | 'error'>('loading');

  protected readonly entries = signal<CreditLedgerEntry[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');

  protected readonly columns: DataTableColumn[] = [
    { key: 'created_at', label: 'Data' },
    { key: 'reason', label: 'Motivo' },
    { key: 'amount_cents', label: 'Valor', numeric: true },
  ];

  // --- Recarga de saldo (modal) ----------------------------------------------
  protected readonly presetsReais = TOPUP_PRESETS_REAIS;
  protected readonly minCents = TOPUP_MIN_CENTS;

  protected readonly showTopupModal = signal(false);
  protected readonly topupInput = signal('');
  protected readonly topupLoading = signal(false);
  protected readonly topupError = signal<string | null>(null);
  protected readonly topupPending = signal(false);
  protected readonly topupConfirmed = signal(false);
  protected readonly topupQrImage = signal<string | null>(null);
  protected readonly topupQrCode = signal<string | null>(null);
  protected readonly topupCopied = signal(false);
  protected readonly topupTaxaPixCents = signal(0);
  protected readonly topupTaxaServicoCents = signal(0);
  protected readonly topupTotalCents = signal(0);

  protected readonly topupAmountCents = computed(() =>
    Math.round(parseBrl(this.topupInput()) * 100)
  );
  protected readonly topupValid = computed(() => this.topupAmountCents() >= TOPUP_MIN_CENTS);
  /** Prévia do total (recarga + taxas do plano, já conhecidas antes de confirmar) —
   * o servidor recalcula do zero ao gerar o PIX; isso é só o resumo pra loja decidir. */
  protected readonly topupExpectedTotalCents = computed(
    () => this.topupAmountCents() + this.topupTaxaPixCents() + this.topupTaxaServicoCents()
  );

  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private topupChargeId: number | null = null;

  constructor() {
    void this.load();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  protected async load(): Promise<void> {
    this.balanceState.set('loading');
    this.tableState.set('loading');
    await Promise.all([this.loadBalance(), this.loadLedger()]);
  }

  private async loadBalance(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ balance_cents: number }>('/v1/merchants/credit-balance')
      );
      this.balanceCents.set(res.balance_cents);
      this.balanceState.set('ready');
    } catch {
      this.balanceState.set('error');
    }
  }

  private async loadLedger(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ items: CreditLedgerEntry[] }>('/v1/merchants/credit-ledger')
      );
      this.entries.set(res.items);
      this.tableState.set(res.items.length === 0 ? 'empty' : 'ready');
    } catch {
      this.tableState.set('error');
    }
  }

  protected get balanceSign(): MoneySign {
    const c = this.balanceCents();
    if (c > 0) return 'credit';
    if (c < 0) return 'debit';
    return 'none';
  }

  protected entrySign(entry: CreditLedgerEntry): MoneySign {
    return entry.amount_cents >= 0 ? 'credit' : 'debit';
  }

  /** jx-money espera a magnitude (sem sinal) — `sign` já cuida do +/−. */
  protected entryAbsCents(entry: CreditLedgerEntry): number {
    return Math.abs(entry.amount_cents);
  }

  protected kindLabel(kind: string): string {
    if (kind === 'consumption') return 'Desconto usado';
    if (kind === 'reversal') return 'Saldo devolvido (cancelamento)';
    if (kind === 'topup') return 'Recarga de saldo';
    return 'Ajuste de entrega';
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  protected trackEntry = (item: unknown): unknown => (item as CreditLedgerEntry).id;

  // --- Recarga de saldo --------------------------------------------------

  protected readonly formatBrl = formatCents;

  protected openTopupModal(): void {
    this.showTopupModal.set(true);
    this.topupInput.set('');
    this.topupError.set(null);
    this.topupPending.set(false);
    this.topupConfirmed.set(false);
    this.topupQrImage.set(null);
    this.topupQrCode.set(null);
    this.topupChargeId = null;
    void this.loadPlanTaxas();
  }

  private async loadPlanTaxas(): Promise<void> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ taxa_pix_cents: number; taxa_servico_cents: number }>(
          '/v1/merchants/plan-taxas'
        )
      );
      this.topupTaxaPixCents.set(res.taxa_pix_cents);
      this.topupTaxaServicoCents.set(res.taxa_servico_cents);
    } catch {
      this.topupTaxaPixCents.set(0);
      this.topupTaxaServicoCents.set(0);
    }
  }

  protected closeTopupModal(): void {
    this.stopPolling();
    this.showTopupModal.set(false);
    // Recarga confirmada nesta sessão — recarrega saldo/extrato ao fechar.
    if (this.topupConfirmed()) void this.load();
  }

  protected selectPreset(reais: number): void {
    this.topupInput.set(maskBrl(String(reais * 100)));
  }

  protected onTopupInput(raw: string): void {
    this.topupInput.set(maskBrl(raw));
  }

  protected async submitTopup(): Promise<void> {
    if (!this.topupValid() || this.topupLoading()) return;
    this.topupLoading.set(true);
    this.topupError.set(null);
    try {
      const res = await firstValueFrom(
        this.http.post<CreditTopupResponse>('/v1/merchants/credit-topup', {
          amount_cents: this.topupAmountCents(),
        })
      );
      this.topupChargeId = res.charge_id;
      this.topupTaxaPixCents.set(res.taxa_pix_cents);
      this.topupTaxaServicoCents.set(res.taxa_servico_cents);
      this.topupTotalCents.set(res.total_cents);
      this.topupQrImage.set(res.qr_code_base64);
      this.topupQrCode.set(res.qr_code);
      this.topupPending.set(true);
      this.startPolling();
    } catch {
      this.topupError.set('Não foi possível gerar o PIX agora. Tente de novo.');
    } finally {
      this.topupLoading.set(false);
    }
  }

  protected async copyTopupCode(): Promise<void> {
    const code = this.topupQrCode();
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      this.topupCopied.set(true);
      setTimeout(() => this.topupCopied.set(false), 2000);
    } catch {
      // clipboard bloqueado — código já está visível pra copiar na mão
    }
  }

  private startPolling(): void {
    this.pollTimer = setInterval(() => void this.checkTopupStatus(), POLL_INTERVAL_MS);
  }

  private stopPolling(): void {
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  private async checkTopupStatus(): Promise<void> {
    if (this.topupChargeId === null) return;
    try {
      const res = await firstValueFrom(
        this.http.get<{ paid: boolean; status: string }>(
          `/v1/merchants/credit-topup/${this.topupChargeId}/status`
        )
      );
      if (res.paid) {
        this.stopPolling();
        this.topupPending.set(false);
        this.topupConfirmed.set(true);
      }
    } catch {
      // rede instável — tenta de novo no próximo tick
    }
  }
}
