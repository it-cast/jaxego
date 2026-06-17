/**
 * pt-BR money helpers for masked currency inputs (br/brazilian-forms).
 *
 * NEVER use a raw `type="number"` for money: it loses the pt-BR `R$ 0,00` shape,
 * the comma decimal separator, and inputmode. These helpers convert between the
 * displayed mask and a numeric value (reais as a Decimal-safe string).
 */

/** Mask a raw digit string into `R$ 0,00` (last 2 digits = cents). */
export function maskBrl(raw: string): string {
  const digits = raw.replace(/\D/g, '');
  if (digits === '') {
    return '';
  }
  const cents = parseInt(digits, 10);
  const reais = (cents / 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `R$ ${reais}`;
}

/** Parse a masked `R$ 1.234,56` (or partial) into a numeric reais value. */
export function parseBrl(masked: string): number {
  const digits = masked.replace(/\D/g, '');
  if (digits === '') {
    return 0;
  }
  return parseInt(digits, 10) / 100;
}

/** Format a numeric reais value into `R$ 0,00` for display. */
export function formatBrl(value: number): string {
  return `R$ ${value.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Format INTEGER cents into pt-BR currency (e.g. `9990` → `R$ 99,90`). The single
 * source of cents→reais formatting for the whole app — money crosses the API as
 * integer cents (DRV-009) and is formatted only at the display edge. Reused by
 * jx-money, jx-invoice-summary and the Phase 15 financial screens; supersedes the
 * ad-hoc `formatCents` that lived in billing.service.ts (Phase 10).
 */
export function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}
