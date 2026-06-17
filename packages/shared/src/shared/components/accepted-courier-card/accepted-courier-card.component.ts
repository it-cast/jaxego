import {
  ChangeDetectionStrategy,
  Component,
  Input,
  computed,
  signal,
} from '@angular/core';
import { StateBadgeComponent } from '../state-badge/state-badge.component';
import { ScoreChipComponent, type ScoreLevel } from '../score-chip/score-chip.component';

/**
 * jx-accepted-courier-card — the courier who accepted, shown to the STORE (D-05).
 * Renders photo (or initials fallback) · name · plate (mono) · jx-score-chip ·
 * jx-state-badge ACEITA. The store sees the courier's IDENTITY for trust/contact
 * after acceptance (ADR-007) but NEVER their live location (TH-3 — Phase 9, and
 * even there with rules). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-accepted-courier-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [StateBadgeComponent, ScoreChipComponent],
  template: `
    <article class="jx-accepted-card">
      <div class="jx-accepted-card__avatar" aria-hidden="true">
        @if (photo()) {
          <img class="jx-accepted-card__photo" [src]="photo()" alt="" />
        } @else {
          <span class="jx-accepted-card__initials">{{ initials() }}</span>
        }
      </div>
      <div class="jx-accepted-card__body">
        <p class="jx-accepted-card__name">{{ name }}</p>
        @if (plate) {
          <p class="jx-accepted-card__plate">{{ plate }}</p>
        }
      </div>
      <div class="jx-accepted-card__meta">
        <jx-state-badge state="ACEITA" variant="dashboard" />
        <jx-score-chip [level]="scoreLevel" [value]="scoreValue" />
      </div>
    </article>
  `,
  styleUrl: './accepted-courier-card.component.scss',
})
export class AcceptedCourierCardComponent {
  private readonly _photoUrl = signal<string | null>(null);

  /** Courier full name. */
  @Input({ required: true }) name = '';
  /** Vehicle plate (rendered in mono). */
  @Input() plate: string | null = null;
  /** Score level (drives the chip color + label). */
  @Input() scoreLevel: ScoreLevel = 'probation';
  /** Numeric score (optional). */
  @Input() scoreValue: number | null = null;

  /** Profile photo URL; when absent, initials are shown over a neutral surface. */
  @Input()
  set photoUrl(value: string | null) {
    this._photoUrl.set(value);
  }

  protected readonly photo = computed(() => this._photoUrl());

  protected readonly initials = computed(() => {
    const parts = this.name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) {
      return '?';
    }
    const first = parts[0][0] ?? '';
    const last = parts.length > 1 ? (parts[parts.length - 1][0] ?? '') : '';
    return (first + last).toUpperCase();
  });
}
