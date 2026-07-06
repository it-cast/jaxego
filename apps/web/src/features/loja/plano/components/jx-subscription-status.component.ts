import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';
import { formatCents } from '../billing.service';

export type BillingStatus = 'trial' | 'active' | 'blocked' | 'cancelado';

interface StatusMeta {
  cssVar: string;
  icon: string;
  role: 'status' | 'alert';
}

const STATUS_META: Record<BillingStatus, StatusMeta> = {
  trial: { cssVar: '--info', icon: '◷', role: 'status' },
  active: { cssVar: '--success', icon: '✓', role: 'status' },
  blocked: { cssVar: '--error', icon: '!', role: 'alert' },
  cancelado: { cssVar: '--text-muted', icon: '×', role: 'status' },
};

/**
 * jx-subscription-status — the subscription state banner (UI-SPEC §6.4 / §3 map).
 *
 * Renders TEXT + ICON + COLOR (never color-only — a11y). `blocked` is a strong
 * `role="alert"` banner with the regularisation copy (UI-SPEC §7). Money/dates are
 * mono (`--jx-font-mono`). Tokens: only the semantic `--info/--success/--error/
 * --text-muted` vars reused from the state vocabulary — NO new token, NO hex (Gate 2).
 */
@Component({
  selector: 'jx-subscription-status',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="jx-sub-status"
      [class.jx-sub-status--blocked]="statusValue() === 'blocked'"
      [style.--status-color]="'var(' + meta().cssVar + ')'"
      [attr.role]="meta().role"
    >
      <span class="jx-sub-status__icon" aria-hidden="true">{{ meta().icon }}</span>
      <div class="jx-sub-status__body">
        <p class="jx-sub-status__label">{{ label() }}</p>
        @if (detail()) {
          <p class="jx-sub-status__detail">{{ detail() }}</p>
        }
      </div>
    </div>
  `,
  styleUrl: './jx-subscription-status.component.scss',
})
export class SubscriptionStatusComponent {
  private readonly _status = signal<BillingStatus>('trial');
  private readonly _amountCents = signal(0);
  private readonly _nextDue = signal<string | null>(null);
  private readonly _planName = signal<string | null>(null);

  @Input({ required: true })
  set status(v: BillingStatus) {
    this._status.set(v);
  }
  @Input()
  set amountCents(v: number) {
    this._amountCents.set(v);
  }
  @Input()
  set nextDueAt(v: string | null) {
    this._nextDue.set(v);
  }
  @Input()
  set planName(v: string | null) {
    this._planName.set(v);
  }

  protected readonly statusValue = this._status;
  protected readonly meta = computed(() => STATUS_META[this._status()]);

  protected readonly label = computed(() => {
    switch (this._status()) {
      case 'trial':
        return this._planName() ?? 'Plano gratuito';
      case 'active':
        return this._planName() ?? 'Assinatura ativa';
      case 'blocked':
        return 'Assinatura bloqueada';
      case 'cancelado':
        return 'Assinatura cancelada';
    }
  });

  protected readonly detail = computed(() => {
    const due = this._nextDue();
    const dueFmt = due ? new Date(due).toLocaleDateString('pt-BR') : null;
    switch (this._status()) {
      case 'trial':
        return null;
      case 'active':
        return dueFmt
          ? `Renova em ${dueFmt} por ${formatCents(this._amountCents())}`
          : null;
      case 'blocked':
        return 'Sua assinatura está bloqueada por falta de pagamento (mais de 10 dias em atraso). Regularize para voltar a criar entregas. Após 20 dias o plano é cancelado.';
      case 'cancelado':
        return 'Reative quando quiser para voltar a usar a plataforma.';
    }
  });
}
