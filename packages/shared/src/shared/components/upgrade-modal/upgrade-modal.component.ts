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
import { RouterLink } from '@angular/router';

/**
 * jx-upgrade-modal — the plan-limit modal (E4 / RN-028 / D-07). Opens INSTEAD of
 * creating when the monthly limit is reached. Anti-dark-pattern (UI-SPEC §5):
 *   - factual title + honest subtext ("o contador zera no dia 1º");
 *   - "Agora não" of EQUAL visual weight to the upgrade CTA (not a faded link);
 *   - no countdown, no "last chance", no forced pre-selection;
 *   - Esc / X / "Agora não" are equivalent and lossless (the form keeps its data).
 *
 * Accessibility: `role="dialog"` `aria-modal`, focus moves to the title on open,
 * focus is trapped, Esc closes, focus returns to the trigger (caller handles).
 * Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-upgrade-modal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink],
  template: `
    <div class="jx-upgrade-overlay">
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
          No plano {{ planName || 'atual' }} são {{ limit }} entregas por mês.
          O contador zera no dia 1º.
        </p>

        <div class="jx-upgrade__actions">
          <a
            routerLink="/loja/plano"
            class="jx-upgrade__cta"
            (click)="dismiss.emit()"
          >
            Ver planos disponíveis
          </a>
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
  @Input() planName = '';
  @Input() limit = 0;
  @Input() used = 0;

  @Output() dismiss = new EventEmitter<void>();

  @ViewChild('title') private titleRef?: ElementRef<HTMLElement>;
  @ViewChild('panel') private panelRef?: ElementRef<HTMLElement>;

  protected get titleText(): string {
    return `Você usou suas ${this.used} de ${this.limit} entregas do mês`;
  }

  ngAfterViewInit(): void {
    queueMicrotask(() => this.titleRef?.nativeElement.focus());
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    this.dismiss.emit();
  }

  @HostListener('document:keydown', ['$event'])
  protected trapFocus(event: KeyboardEvent): void {
    if (event.key !== 'Tab') return;
    const panel = this.panelRef?.nativeElement;
    if (!panel) return;
    const focusable = panel.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) return;
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
}
