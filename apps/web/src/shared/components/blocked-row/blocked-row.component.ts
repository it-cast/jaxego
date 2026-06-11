import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/**
 * jx-blocked-row — a blocked courier row (tela 15, UI-SPEC §5.2). Shows the name
 * and a detail line with the block date + PRIVATE reason (RN-014 — visible only to
 * the store, NEVER to the courier; it never affects the courier's score). The
 * action is Unblock (≥44px). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-blocked-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <li class="jx-blocked-row">
      <div class="jx-blocked-row__body">
        <span class="jx-blocked-row__name">{{ name }}</span>
        <span class="jx-blocked-row__detail">
          @if (blockedAt) {
            bloqueado em {{ blockedAt }}
          }
          @if (reason) {
            — motivo (privado): {{ reason }}
          }
        </span>
      </div>
      <button
        type="button"
        class="jx-blocked-row__unblock"
        [attr.aria-label]="'Desbloquear ' + name"
        (click)="unblock.emit()"
      >
        Desbloquear
      </button>
    </li>
  `,
  styleUrl: './blocked-row.component.scss',
})
export class BlockedRowComponent {
  @Input({ required: true }) name = '';
  /** Block date (dd/MM) — display only. */
  @Input() blockedAt: string | null = null;
  /** PRIVATE store-only reason (RN-014) — never shown to the courier. */
  @Input() reason: string | null = null;

  @Output() unblock = new EventEmitter<void>();
}
