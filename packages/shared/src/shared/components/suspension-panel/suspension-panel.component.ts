import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  EventEmitter,
  Input,
  Output,
  computed,
  inject,
  signal,
} from '@angular/core';

/** A suspension appeal — mirrors the backend `AppealRead` (REQ-045 / D-05). */
export interface SuspensionAppeal {
  id: number;
  subject_type: 'courier' | 'merchant';
  subject_id: number;
  reason: string;
  opened_at: string;
  sla_due_at: string;
  decision: string | null;
  decided_at: string | null;
  reverted_at: string | null;
}

/** The decision an admin can record on an appeal. */
export type AppealDecision = 'upheld' | 'overturned';

/**
 * jx-suspension-panel — the suspension + appeal panel (UI-SPEC §Tela 25/09,
 * REQ-045 / D-04 / D-05).
 *
 * Shows the suspension MOTIVO (never silent), the appeal WINDOW, a live SLA
 * COUNTDOWN (`aria-live="polite"` — accessibility-pro), and the decision actions
 * (manter / reverter). When the SLA is overdue without a decision, the backend job
 * reverts the subject automatically (REQ-045) — the panel states this clearly. The
 * decision is auditadа; the action is disabled once a decision/reversion exists.
 * Tokens only — no hex (Gate 2). pt-BR sem jargão (UI-SPEC §copy).
 */
@Component({
  selector: 'jx-suspension-panel',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section
      class="jx-suspension-panel"
      [class.jx-suspension-panel--resolved]="isResolved()"
      aria-labelledby="susp-title"
    >
      <header class="jx-suspension-panel__head">
        <h3 id="susp-title" class="jx-suspension-panel__title">
          {{ subjectLabel() }} suspenso
        </h3>
        <span
          class="jx-suspension-panel__status"
          [class.jx-suspension-panel__status--active]="!isResolved()"
          [class.jx-suspension-panel__status--reverted]="isReverted()"
          [class.jx-suspension-panel__status--upheld]="isUpheld()"
        >
          {{ statusLabel() }}
        </span>
      </header>

      <dl class="jx-suspension-panel__meta">
        <div>
          <dt>Motivo</dt>
          <dd>{{ data().reason }}</dd>
        </div>
        <div>
          <dt>Suspenso em</dt>
          <dd>{{ formatDateTime(data().opened_at) }}</dd>
        </div>
        <div>
          <dt>Prazo do recurso</dt>
          <dd>{{ formatDateTime(data().sla_due_at) }}</dd>
        </div>
      </dl>

      @if (!isResolved()) {
        <p
          class="jx-suspension-panel__sla"
          [class.jx-suspension-panel__sla--risk]="slaAtRisk()"
          [class.jx-suspension-panel__sla--overdue]="slaOverdue()"
          aria-live="polite"
        >
          @if (slaOverdue()) {
            Prazo vencido — a suspensão será revertida automaticamente.
          } @else {
            Tempo restante para decidir: <strong>{{ countdown() }}</strong>
          }
        </p>
        <p class="jx-suspension-panel__hint">
          Se não houver decisão até o prazo, a suspensão é revertida
          automaticamente.
        </p>
      } @else if (isReverted()) {
        <p class="jx-suspension-panel__resolved-note">
          Suspensão revertida — acesso reativado em
          {{ formatDateTime(data().reverted_at) }}.
        </p>
      } @else {
        <p class="jx-suspension-panel__resolved-note">
          Recurso indeferido em {{ formatDateTime(data().decided_at) }} — a
          suspensão foi mantida.
        </p>
      }

      @if (!isResolved()) {
        <div class="jx-suspension-panel__actions">
          <button
            type="button"
            class="jx-suspension-panel__btn jx-suspension-panel__btn--keep"
            [disabled]="busy"
            (click)="decide.emit('upheld')"
          >
            Manter suspensão
          </button>
          <button
            type="button"
            class="jx-suspension-panel__btn jx-suspension-panel__btn--revert"
            [disabled]="busy"
            (click)="decide.emit('overturned')"
          >
            Reverter (reativar acesso)
          </button>
        </div>
      }
    </section>
  `,
  styleUrl: './suspension-panel.component.scss',
})
export class SuspensionPanelComponent {
  private readonly destroyRef = inject(DestroyRef);
  private readonly _appeal = signal<SuspensionAppeal | null>(null);
  private readonly _now = signal<number>(Date.now());

  /** The appeal to render (required). Drives the countdown + decision state. */
  @Input({ required: true })
  set appeal(value: SuspensionAppeal) {
    this._appeal.set(value);
  }
  get appeal(): SuspensionAppeal {
    return this._appeal()!;
  }

  /** Disables actions while a decision request is in flight. */
  @Input() busy = false;

  /** Emits the admin's decision (manter / reverter). */
  @Output() decide = new EventEmitter<AppealDecision>();

  constructor() {
    // Live SLA countdown — ticks once a minute (UI-SPEC: aria-live discreto).
    const timer = setInterval(() => this._now.set(Date.now()), 60_000);
    this.destroyRef.onDestroy(() => clearInterval(timer));
  }

  /** The appeal exposed to the template (non-null once the input is set). */
  protected readonly data = computed(() => this._appeal()!);

  protected readonly isReverted = computed(
    () => this._appeal()?.reverted_at != null,
  );
  protected readonly isUpheld = computed(
    () => this._appeal()?.decision === 'upheld',
  );
  protected readonly isResolved = computed(
    () => this.isReverted() || this._appeal()?.decided_at != null,
  );

  protected subjectLabel = computed(() =>
    this._appeal()?.subject_type === 'merchant' ? 'Lojista' : 'Entregador',
  );

  protected statusLabel = computed(() => {
    if (this.isReverted()) {
      return 'Revertida';
    }
    if (this.isUpheld()) {
      return 'Mantida';
    }
    return 'Suspensão ativa';
  });

  private readonly msRemaining = computed(() => {
    const a = this._appeal();
    if (!a) {
      return 0;
    }
    return new Date(a.sla_due_at).getTime() - this._now();
  });

  protected readonly slaOverdue = computed(() => this.msRemaining() <= 0);

  /** Within 6h of the deadline → highlight as at-risk (warning). */
  protected readonly slaAtRisk = computed(() => {
    const ms = this.msRemaining();
    return ms > 0 && ms <= 6 * 60 * 60 * 1000;
  });

  protected readonly countdown = computed(() => {
    const ms = this.msRemaining();
    if (ms <= 0) {
      return '0min';
    }
    const totalMinutes = Math.floor(ms / 60_000);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      const remHours = hours % 24;
      return remHours > 0 ? `${days}d ${remHours}h` : `${days}d`;
    }
    if (hours > 0) {
      return `${hours}h ${minutes}min`;
    }
    return `${minutes}min`;
  });

  protected formatDateTime(iso: string | null): string {
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
