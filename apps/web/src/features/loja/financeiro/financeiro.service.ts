import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type {
  InvoiceStatus,
  InvoiceSummary,
} from '../../../shared/components/invoice-summary/invoice-summary.component';

/**
 * Contratos das telas 15 (fatura da loja) e 08 (recibo do direto) — espelham
 * `apps/api/app/invoices/router.py` e `apps/api/app/payments_direct/router.py`.
 * Dinheiro cruza a API em CENTAVOS inteiros (DRV-009); a formatação pt-BR acontece
 * só na borda (jx-money). Reads escopados à loja no backend (IDOR → 404 — TH-03).
 */

/** Uma fatura de plataforma (GET /v1/invoices) — superset de InvoiceSummary. */
export interface Invoice extends InvoiceSummary {
  status: InvoiceStatus;
}

/** Uma linha da fatura (GET /v1/invoices/{id}/lines) — entrega + taxa (derivada). */
export interface InvoiceLine {
  id: number;
  delivery_id: number | null;
  description: string;
  amount_cents: number;
}

/** Recibo do pagamento direto (GET /v1/deliveries/{id}/receipt) — sem PII (RN-013). */
export interface DirectReceipt {
  delivery_id: number;
  public_token: string;
  reference_number: string | null;
  amount_cents: number | null;
  /** cash | pix | not_received | pending. */
  outcome: string;
  status: string;
  confirmed_at: string | null;
}

@Injectable({ providedIn: 'root' })
export class LojaFinanceiroService {
  private readonly http = inject(HttpClient);

  /** Lista as faturas de plataforma da loja (mais recente primeiro). */
  async invoices(): Promise<Invoice[]> {
    return firstValueFrom(this.http.get<Invoice[]>('/v1/invoices'));
  }

  /** As linhas (entrega/taxa) de uma fatura (tela 15). */
  async invoiceLines(invoiceId: number): Promise<InvoiceLine[]> {
    return firstValueFrom(
      this.http.get<InvoiceLine[]>(`/v1/invoices/${invoiceId}/lines`),
    );
  }

  /** Paga uma fatura em aberto/vencida via PaymentPort (fluxo de checkout). */
  async payInvoice(invoiceId: number): Promise<Invoice> {
    return firstValueFrom(
      this.http.post<Invoice>(`/v1/invoices/${invoiceId}/pay`, {}),
    );
  }

  /** O recibo do pagamento direto de uma entrega (tela 08). */
  async receipt(deliveryId: number): Promise<DirectReceipt> {
    return firstValueFrom(
      this.http.get<DirectReceipt>(`/v1/deliveries/${deliveryId}/receipt`),
    );
  }
}
