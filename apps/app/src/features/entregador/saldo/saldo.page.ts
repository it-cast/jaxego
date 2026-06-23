import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { MoneyComponent } from '@jaxego/shared/components/money/money.component';
import { PageHeaderComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';
import { formatCents } from '@jaxego/shared/util/money';
import {
  Balance,
  ExtractEntry,
  SaldoService,
  WithdrawalHistoryRow,
} from './saldo.service';

const WITHDRAWAL_STATUS_META: Record<
  string,
  { label: string; tone: 'success' | 'warning' | 'error' }
> = {
  paid: { label: 'Pago', tone: 'success' },
  pending: { label: 'Em processamento', tone: 'warning' },
  failed: { label: 'Falhou', tone: 'error' },
};

/**
 * Tela 16 — Extrato/saldo + saque do entregador (UI-SPEC §16 / D-06 / REQ-038).
 *
 * MOBILE-first (touch targets ≥44px). Saldo disponível em destaque (mono via
 * jx-money), extrato das corridas liberadas (jx-data-table), CTA "Solicitar saque"
 * com confirmação sensível (foco-preso, Esc, aria-modal), e histórico de saques.
 *
 * O mínimo de saque vem do BACKEND (`minimum_cents`) — a UI apenas exibe a regra
 * ("Saque mínimo de R$ 20,00") e barra antes de enviar; um valor abaixo dispara um
 * erro semântico com aria-live (accessibility-pro). "Se o saque falhar, o valor
 * volta para o seu saldo" (trust-safety-ux). Estados loading/empty/error em todas
 * as superfícies. Tokens semânticos; zero hex; AA nos 2 temas (DEC-001).
 */
@Component({
  selector: 'jx-entregador-saldo-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, MoneyComponent, ErrorStateComponent, PageHeaderComponent, DotsLoaderComponent],
  templateUrl: './saldo.page.html',
  styleUrl: './saldo.page.scss',
})
export class EntregadorSaldoPage {
  private readonly service = inject(SaldoService);

  // --- Saldo ----------------------------------------------------------------
  protected readonly balanceState = signal<DataTableState>('loading');
  protected readonly balance = signal<Balance | null>(null);

  // --- Extrato --------------------------------------------------------------
  protected readonly extractState = signal<DataTableState>('loading');
  protected readonly extract = signal<ExtractEntry[]>([]);

  // --- Histórico de saques --------------------------------------------------
  protected readonly historyState = signal<DataTableState>('loading');
  protected readonly history = signal<WithdrawalHistoryRow[]>([]);

  // --- Confirmação de saque -------------------------------------------------
  protected readonly confirming = signal(false);
  protected readonly submitting = signal(false);
  protected readonly amountError = signal<string | null>(null);
  protected readonly submitError = signal<string | null>(null);
  protected readonly lastResult = signal<WithdrawalHistoryRow | null>(null);

  @ViewChild('confirmTrigger')
  private confirmTrigger?: ElementRef<HTMLButtonElement>;
  @ViewChild('confirmAction')
  private confirmAction?: ElementRef<HTMLButtonElement>;

  protected readonly extractColumns: DataTableColumn[] = [
    { key: 'at', label: 'Quando' },
    { key: 'amount_cents', label: 'Valor', numeric: true },
  ];

  protected readonly historyColumns: DataTableColumn[] = [
    { key: 'requested_at', label: 'Quando' },
    { key: 'amount_cents', label: 'Valor', numeric: true },
    { key: 'status', label: 'Status' },
  ];

  /** O saldo cobre o mínimo? (habilita o CTA de saque). */
  protected readonly canWithdraw = computed(() => {
    const b = this.balance();
    return !!b && b.balance_cents >= b.minimum_cents && b.balance_cents > 0;
  });

  /** Texto do mínimo, formatado a partir do valor do backend (nunca hardcoded). */
  protected readonly minimumLabel = computed(() => {
    const b = this.balance();
    return b ? formatCents(b.minimum_cents) : '';
  });

  constructor() {
    void this.loadAll();
  }

  protected async loadAll(): Promise<void> {
    await Promise.all([
      this.loadBalance(),
      this.loadExtract(),
      this.loadHistory(),
    ]);
  }

  protected async loadBalance(): Promise<void> {
    this.balanceState.set('loading');
    try {
      this.balance.set(await this.service.balance());
      this.balanceState.set('ready');
    } catch {
      this.balanceState.set('error');
    }
  }

  protected async loadExtract(): Promise<void> {
    this.extractState.set('loading');
    try {
      const rows = await this.service.extract();
      this.extract.set(rows);
      this.extractState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.extractState.set('error');
    }
  }

  protected async loadHistory(): Promise<void> {
    this.historyState.set('loading');
    try {
      const rows = await this.service.history();
      this.history.set(rows);
      this.historyState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.historyState.set('error');
    }
  }

  // --- Saque ----------------------------------------------------------------
  protected openConfirm(): void {
    this.amountError.set(null);
    this.submitError.set(null);
    this.lastResult.set(null);
    const b = this.balance();
    // Barra cedo: abaixo do mínimo não abre o fluxo (erro semântico + aria-live).
    if (b && b.balance_cents < b.minimum_cents) {
      this.amountError.set(
        `Saque mínimo de ${this.minimumLabel()}. Seu saldo ainda não chegou lá.`,
      );
      return;
    }
    this.confirming.set(true);
    // Move o foco para a ação de confirmar (foco-preso no modal — a11y).
    setTimeout(() => this.confirmAction?.nativeElement.focus(), 0);
  }

  protected closeConfirm(): void {
    this.confirming.set(false);
    this.confirmTrigger?.nativeElement.focus();
  }

  protected async confirmWithdrawal(): Promise<void> {
    const b = this.balance();
    if (!b) {
      return;
    }
    if (b.balance_cents < b.minimum_cents) {
      this.amountError.set(`Saque mínimo de ${this.minimumLabel()}.`);
      return;
    }
    this.submitting.set(true);
    this.submitError.set(null);
    try {
      // Saca o saldo disponível inteiro; idempotency_key evita duplo-clique (TH-02).
      const key = `wd_${Date.now()}`;
      const result = await this.service.requestWithdrawal(b.balance_cents, key);
      this.lastResult.set({
        id: result.id,
        amount_cents: result.amount_cents,
        status: result.status,
        transaction_id: result.transaction_id,
        settled_at: null,
        requested_at: new Date().toISOString(),
      });
      this.confirming.set(false);
      this.confirmTrigger?.nativeElement.focus();
      // Recarrega saldo + histórico (o saldo cai; o saque entra no histórico).
      await Promise.all([this.loadBalance(), this.loadHistory()]);
    } catch {
      this.submitError.set(
        'Não conseguimos solicitar o saque agora. Tente de novo em instantes.',
      );
    } finally {
      this.submitting.set(false);
    }
  }

  // --- Helpers de exibição --------------------------------------------------
  protected statusLabel(status: string): string {
    return WITHDRAWAL_STATUS_META[status]?.label ?? status;
  }

  protected statusTone(status: string): 'success' | 'warning' | 'error' {
    return WITHDRAWAL_STATUS_META[status]?.tone ?? 'warning';
  }

  protected formatDate(iso: string | null): string {
    if (!iso) {
      return '—';
    }
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  }

  protected trackExtract = (item: unknown): unknown => (item as ExtractEntry).id;
  protected trackHistory = (item: unknown): unknown =>
    (item as WithdrawalHistoryRow).id;
}
