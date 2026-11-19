import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { DeliveryState } from '@jaxego/shared/components/state-badge/state-badge.component';

export interface AdminEntrega {
  id: number;
  state: DeliveryState;
  created_at: string | null;
  scheduled_at: string | null;
  merchant_id: number;
  merchant_name: string | null;
  courier_id: number | null;
  courier_name: string | null;
  pickup_address: string;
  dropoff_address: string;
  dropoff_number: string | null;
  dropoff_neighborhood: string | null;
  payment_method: string;
  /** Como foi paga de fato: pix (inclui o PIX da plataforma), card ou direct. */
  pagamento: string;
  proof_method: string;
  price_cents: number | null;
  fee_cents: number;
  reference_number: string | null;
  public_token: string;
}

export interface AdminEntregaLista {
  items: AdminEntrega[];
  total: number;
  limit: number;
  offset: number;
  por_estado: Partial<Record<DeliveryState, number>>;
}

export interface AdminEntregaDetalhe extends AdminEntrega {
  dropoff_complement: string | null;
  dropoff_reference: string | null;
  recipient_name: string | null;
  recipient_phone_masked: string | null;
  items_description: string | null;
  items_quantity: number;
  notes: string | null;
  distance_m: number | null;
  accepted_at: string | null;
  collected_at: string | null;
  delivered_at: string | null;
  finalized_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  historico: {
    from_state: string | null;
    to_state: string;
    actor_type: string | null;
    reason: string | null;
    created_at: string | null;
  }[];
}

export interface FiltroOpcao {
  id: number;
  nome: string;
}

export interface AdminEntregaFiltros {
  q?: string;
  state?: string;
  merchant_id?: number | null;
  courier_id?: number | null;
  payment_method?: string;
  inicio?: string | null;
  fim?: string | null;
  limit: number;
  offset: number;
}

/** Entregas da cidade (admin da área) — só leitura. */
@Injectable({ providedIn: 'root' })
export class AdminEntregasService {
  private readonly http = inject(HttpClient);

  listar(f: AdminEntregaFiltros): Promise<AdminEntregaLista> {
    let params = new HttpParams().set('limit', f.limit).set('offset', f.offset);
    if (f.q) params = params.set('q', f.q);
    if (f.state) params = params.set('state', f.state);
    if (f.merchant_id) params = params.set('merchant_id', f.merchant_id);
    if (f.courier_id) params = params.set('courier_id', f.courier_id);
    if (f.payment_method) params = params.set('payment_method', f.payment_method);
    if (f.inicio) params = params.set('inicio', f.inicio);
    if (f.fim) params = params.set('fim', f.fim);
    return firstValueFrom(this.http.get<AdminEntregaLista>('/v1/admin/deliveries', { params }));
  }

  detalhe(id: number): Promise<AdminEntregaDetalhe> {
    return firstValueFrom(this.http.get<AdminEntregaDetalhe>(`/v1/admin/deliveries/${id}`));
  }

  opcoes(): Promise<{ lojas: FiltroOpcao[]; entregadores: FiltroOpcao[] }> {
    return firstValueFrom(
      this.http.get<{ lojas: FiltroOpcao[]; entregadores: FiltroOpcao[] }>('/v1/admin/deliveries/filtros')
    );
  }
}
