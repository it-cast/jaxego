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

/**
 * jx-confirm-dialog — bottom-sheet de confirmação genérico ("Deseja realmente...?"),
 * usado antes de ações que avançam estado de forma irreversível (coletar, chegar
 * ao destino, finalizar entrega, etc). Mesmo idioma visual do modal de contato em
 * entrega-ativa (slide-up de baixo — mobile-first).
 *
 * Acessibilidade: `role="alertdialog"` `aria-modal`, foco vai pro título ao abrir,
 * Esc cancela (equivalente a tocar fora / botão Cancelar).
 */
@Component({
  selector: 'jx-confirm-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-confirm-overlay" (click)="cancel.emit()">
      <div
        class="jx-confirm"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="jx-confirm-title"
        (click)="$event.stopPropagation()"
        #panel
      >
        <h2 id="jx-confirm-title" class="jx-confirm__title" tabindex="-1" #titleEl>
          {{ title }}
        </h2>
        @if (message) {
          <p class="jx-confirm__message">{{ message }}</p>
        }
        <div class="jx-confirm__actions">
          <button type="button" class="jx-confirm__confirm" (click)="confirm.emit()">
            {{ confirmLabel }}
          </button>
          <button type="button" class="jx-confirm__cancel" (click)="cancel.emit()">
            {{ cancelLabel }}
          </button>
        </div>
      </div>
    </div>
  `,
  styleUrl: './confirm-dialog.component.scss',
})
export class ConfirmDialogComponent implements AfterViewInit {
  @Input({ required: true }) title = '';
  @Input() message = '';
  @Input() confirmLabel = 'Confirmar';
  @Input() cancelLabel = 'Cancelar';

  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  @ViewChild('titleEl') private readonly titleRef?: ElementRef<HTMLElement>;

  ngAfterViewInit(): void {
    this.titleRef?.nativeElement.focus();
  }

  @HostListener('document:keydown.escape')
  protected onEsc(): void {
    this.cancel.emit();
  }
}
