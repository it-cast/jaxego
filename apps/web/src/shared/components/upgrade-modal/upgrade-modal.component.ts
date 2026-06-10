import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { Plan, PlanCardComponent } from '../plan-card/plan-card.component';

/**
 * jx-upgrade-modal — the plan-limit modal (E4 / RN-028 / D-07). Opens INSTEAD of
 * creating when the Free monthly limit is reached. Anti-dark-pattern (UI-SPEC §5):
 *   - factual title + honest subtext ("o contador zera no dia 1º");
 *   - "Agora não" of EQUAL visual weight to the upgrade CTAs (not a faded link);
 *   - no countdown, no "last chance", no forced pre-selection;
 *   - Esc / X / "Agora não" are equivalent and lossless (the form keeps its data).
 *
 * Accessibility: `role="dialog"` `aria-modal`, focus moves to the title on open,
 * focus is trapped, Esc closes, focus returns to the trigger (caller handles).
 * The plan comparison reuses `jx-plan-card`, DATA-DRIVEN from GET /v1/plans.
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-upgrade-modal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PlanCardComponent],
  template: `
    <div class="jx-upgrade-overlay" (click)="onOverlay($event)">
      <div
        class="jx-upgrade"
        role="dialog"
        aria-modal="true"
        aria-labelledby="jx-upgrade-title"
        #panel
      >
        <button
          type="button"
          class="jx-upgrade__close"
          aria-label="Fechar"
          (click)="dismiss.emit()"
        >
          ×
        </button>

        <h2 id="jx-upgrade-title" class="jx-upgrade__title" tabindex="-1" #title>
          {{ titleText }}
        </h2>
        <p class="jx-upgrade__subtext">
          No plano {{ currentPlanName }} são {{ limit }} entregas por mês. O contador zera no dia
          1º. Para enviar agora, escolha um plano com mais entregas.
        </p>

        <div class="jx-upgrade__plans">
          @for (plan of plans; track plan.codename) {
            <jx-plan-card
              [plan]="plan"
              [selected]="plan.is_free"
              (choose)="choose.emit($event)"
            />
          }
        </div>

        <div class="jx-upgrade__actions">
          <button type="button" class="jx-upgrade__later" (click)="dismiss.emit()">
            Agora não
          </button>
        </div>
      </div>
    </div>
  `,
  styleUrl: './upgrade-modal.component.scss',
})
export class UpgradeModalComponent implements AfterViewInit {
  /** Plans from GET /v1/plans (DRV-009 — nothing hardcoded). */
  @Input() plans: Plan[] = [];
  @Input() currentPlanName = 'Free';
  @Input() limit = 2;

  @Output() choose = new EventEmitter<Plan>();
  @Output() dismiss = new EventEmitter<void>();

  @ViewChild('title') private titleRef?: ElementRef<HTMLElement>;
  @ViewChild('panel') private panelRef?: ElementRef<HTMLElement>;

  protected get titleText(): string {
    return `Você usou suas ${this.limit} entregas do mês`;
  }

  ngAfterViewInit(): void {
    // Focus the title on open (a11y — UI-SPEC §5).
    queueMicrotask(() => this.titleRef?.nativeElement.focus());
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    this.dismiss.emit();
  }

  @HostListener('document:keydown.tab', ['$event'])
  protected trapFocus(event: KeyboardEvent): void {
    const panel = this.panelRef?.nativeElement;
    if (!panel) {
      return;
    }
    const focusable = panel.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) {
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement as HTMLElement | null;
    if (event.shiftKey && active === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  protected onOverlay(event: MouseEvent): void {
    // Click on the backdrop (not the panel) dismisses — equivalent to "Agora não".
    if (event.target === event.currentTarget) {
      this.dismiss.emit();
    }
  }
}
