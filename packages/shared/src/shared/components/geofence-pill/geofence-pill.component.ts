import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';

/** GPS/geofence verdict (UI-SPEC §07 / error-ux). */
export type GeofenceState = 'checking' | 'ok' | 'out' | 'missing' | 'low_confidence';

interface PillMeta {
  cssVar: string;
  icon: string;
  label: string;
}

/**
 * jx-geofence-pill — the GPS/geofence verdict pill on the proof screen (tela 07).
 *
 * 3+ states ALWAYS rendered as text + icon, NEVER colour alone (accessibility-pro):
 * - checking: "Conferindo sua localização…"
 * - ok: "Você está no local"
 * - out: "Fora do raio — aproxime-se"
 * - missing: "Sem localização — ative o GPS"
 * - low_confidence: "Não confirmamos — segue para revisão"
 *
 * `aria-live="polite"` announces every verdict change (the CTA lock/unlock follows
 * the server verdict, owned by the parent). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-geofence-pill',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span
      class="jx-geofence-pill"
      [style.--pill-color]="'var(' + meta().cssVar + ')'"
      role="status"
      aria-live="polite"
    >
      <span class="jx-geofence-pill__icon" aria-hidden="true">{{ meta().icon }}</span>
      <span class="jx-geofence-pill__label">{{ meta().label }}</span>
    </span>
  `,
  styleUrl: './geofence-pill.component.scss',
})
export class GeofencePillComponent {
  private readonly _state = signal<GeofenceState>('checking');

  @Input({ required: true })
  set state(value: GeofenceState) {
    this._state.set(value);
  }
  get state(): GeofenceState {
    return this._state();
  }

  protected readonly META: Record<GeofenceState, PillMeta> = {
    checking: { cssVar: '--text-muted', icon: '◌', label: 'Conferindo sua localização…' },
    ok: { cssVar: '--success', icon: '✓', label: 'Você está no local' },
    out: { cssVar: '--warning', icon: '⚠', label: 'Fora do raio — aproxime-se do endereço' },
    missing: { cssVar: '--error', icon: '!', label: 'Sem localização — ative o GPS e tente de novo' },
    low_confidence: {
      cssVar: '--info',
      icon: '⊙',
      label: 'Não confirmamos a localização — segue para revisão',
    },
  };

  protected readonly meta = computed(() => this.META[this._state()]);
}
