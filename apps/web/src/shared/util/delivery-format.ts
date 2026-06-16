import type { PaymentMethod } from '../components';

/**
 * Formatação de entrega — fonte ÚNICA de verdade (DRY). Antes estava duplicado em
 * inicio/entregas/entrega-ativa/concluida (entregador) e detalhe (loja).
 */

/** Normaliza o método de pagamento do backend para o tipo do badge. */
export function paymentMethodOf(method: string | null | undefined): PaymentMethod {
  return method === 'pix' || method === 'card' ? method : 'direct';
}

const STATE_LABELS: Record<string, string> = {
  CRIADA: 'Criada',
  ACEITA: 'Aceita',
  COLETADA: 'Coletada',
  ENTREGUE: 'Entregue',
  FINALIZADA: 'Finalizada',
  RECUSADA_NO_DESTINO: 'Recusada',
  CANCELADA: 'Cancelada',
};

/** Rótulo pt-BR do estado da entrega (7 estados, RN-019). */
export function deliveryStateLabel(state: string | null | undefined): string {
  return (state && STATE_LABELS[state]) || state || '';
}

export interface PackageSize {
  weight_g?: number | null;
  length_cm?: number | null;
  width_cm?: number | null;
  height_cm?: number | null;
}

/** "2,5 kg · 40×30×20 cm" — só as partes preenchidas; vazio se nada (MG-1). */
export function packageLabel(p: PackageSize): string {
  const parts: string[] = [];
  if (p.weight_g) {
    parts.push(`${(p.weight_g / 1000).toLocaleString('pt-BR')} kg`);
  }
  if (p.length_cm && p.width_cm && p.height_cm) {
    parts.push(`${p.length_cm}×${p.width_cm}×${p.height_cm} cm`);
  }
  return parts.join(' · ');
}
