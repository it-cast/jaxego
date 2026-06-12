import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { MoneyComponent } from '../../../shared/components/money/money.component';
import { ErrorStateComponent } from '../../../shared/state/error-state.component';
import { DirectReceipt, LojaFinanceiroService } from './financeiro.service';

type ReceiptState = 'loading' | 'ready' | 'empty' | 'error';

const OUTCOME_LABEL: Record<string, string> = {
  cash: 'Recebido em dinheiro',
  pix: 'Recebido em PIX',
  not_received: 'Pagamento não recebido',
  pending: 'Aguardando confirmação',
};

/**
 * Tela 08 — Recibo do pagamento direto (UI-SPEC §08 / D-06 / RN-026).
 *
 * Confirmação transparente do pagamento direto de uma entrega: valor (mono),
 * referência (public_token / número da loja), data e status. trust-safety-ux:
 * transparência total do valor; SEM PII além do permitido (RN-013 — só token,
 * referência, valor, data e desfecho). Estados loading/empty/error. Rota lazy.
 * Tokens semânticos; zero hex; AA nos 2 temas.
 */
@Component({
  selector: 'jx-loja-recibo-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MoneyComponent, ErrorStateComponent],
  templateUrl: './recibo.page.html',
  styleUrl: './recibo.page.scss',
})
export class LojaReciboPage {
  private readonly service = inject(LojaFinanceiroService);
  private readonly route = inject(ActivatedRoute);

  protected readonly state = signal<ReceiptState>('loading');
  protected readonly receipt = signal<DirectReceipt | null>(null);

  private readonly deliveryId = Number(
    this.route.snapshot.paramMap.get('id') ?? 0,
  );

  constructor() {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const receipt = await this.service.receipt(this.deliveryId);
      this.receipt.set(receipt);
      // Sem confirmação ainda (outcome pending e sem data) → empty, não erro.
      this.state.set(
        receipt.outcome === 'pending' && receipt.confirmed_at === null
          ? 'empty'
          : 'ready',
      );
    } catch {
      this.state.set('error');
    }
  }

  protected outcomeLabel(outcome: string): string {
    return OUTCOME_LABEL[outcome] ?? outcome;
  }

  /** Tom semântico do desfecho (sucesso quando pago; alerta quando não recebido). */
  protected outcomeTone(outcome: string): 'success' | 'warning' {
    return outcome === 'not_received' ? 'warning' : 'success';
  }

  protected referenceLabel(receipt: DirectReceipt): string {
    return receipt.reference_number?.trim()
      ? receipt.reference_number
      : receipt.public_token;
  }

  protected formatDate(iso: string | null): string {
    if (!iso) {
      return '—';
    }
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
