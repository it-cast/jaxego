import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';
import { LoadingSkeletonComponent } from '@jaxego/shared/state/loading-skeleton.component';

export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'approved_auto';

/** Reject reason enum (mirrors the backend RejectReason). */
export type ReviewReason = 'ilegivel' | 'sem_ear' | 'vencida' | 'nao_confere' | 'outro';

export interface ReviewDecision {
  action: 'approve' | 'reject';
  reason?: ReviewReason;
  detail?: string;
}

const REASON_LABELS: { value: ReviewReason; label: string }[] = [
  { value: 'ilegivel', label: 'Ilegível' },
  { value: 'sem_ear', label: 'Sem EAR' },
  { value: 'vencida', label: 'Vencida' },
  { value: 'nao_confere', label: 'Não confere com o titular' },
  { value: 'outro', label: 'Outro' },
];

/**
 * jx-kyc-review-row — one document's item-a-item review (UI-SPEC §5.3 / D-04).
 *
 * Grid: thumb (presigned GET, short-lived) · data (mono, CPF masked) · action.
 * Approve flips the item; Reject reveals a reason <select> + a required detail
 * <textarea> — rejecting WITHOUT a reason is BLOCKED (error-ux). Auto items (MEI
 * via Receita) show "Aprovado (automático)" with no buttons. The thumb shows a
 * skeleton while loading and an error+retry if the signed URL expired.
 *
 * Tokens: only semantic vars; CPF always masked (PII/LGPD); status text+icon.
 */
@Component({
  selector: 'jx-kyc-review-row',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, LoadingSkeletonComponent, ErrorStateComponent],
  template: `
    <article class="jx-review" [attr.aria-label]="'Revisão: ' + title">
      <div class="jx-review__thumb">
        @if (thumbState === 'loading') {
          <jx-loading-skeleton variant="block" />
        } @else if (thumbState === 'error') {
          <jx-error-state
            message="Não foi possível abrir o documento. Recarregue."
            retryLabel="Recarregar"
            (retry)="reloadThumb.emit()"
          />
        } @else if (thumbUrl) {
          <button
            type="button"
            class="jx-review__thumb-btn"
            (click)="openFull.emit()"
            [attr.aria-label]="'Abrir ' + title + ' em tela cheia'"
          >
            <img [src]="thumbUrl" [alt]="title" />
          </button>
        }
      </div>

      <div class="jx-review__data">
        <h4 class="jx-review__title">{{ title }}</h4>
        @if (meta) {
          <p class="jx-review__meta">{{ meta }}</p>
        }
        <span class="jx-review__status jx-review__status--{{ statusCls }}">
          <span aria-hidden="true">{{ statusIcon }}</span> {{ statusText }}
        </span>
      </div>

      <div class="jx-review__action">
        @if (status === 'pending') {
          @if (!rejecting) {
            <button
              type="button"
              class="jx-review__btn jx-review__btn--approve"
              (click)="decide.emit({ action: 'approve' })"
            >
              Aprovar
            </button>
            <button
              type="button"
              class="jx-review__btn jx-review__btn--reject"
              (click)="rejecting = true"
            >
              Reprovar
            </button>
          } @else {
            <label class="jx-review__label" [for]="id + '-reason'">Motivo</label>
            <select
              [id]="id + '-reason'"
              class="jx-review__select"
              [(ngModel)]="reason"
            >
              <option [ngValue]="undefined" disabled>Selecione…</option>
              @for (r of reasons; track r.value) {
                <option [ngValue]="r.value">{{ r.label }}</option>
              }
            </select>
            <label class="jx-review__label" [for]="id + '-detail'">Detalhe</label>
            <textarea
              [id]="id + '-detail'"
              class="jx-review__textarea"
              [(ngModel)]="detail"
              maxlength="500"
              placeholder="Explique o que o entregador precisa corrigir"
            ></textarea>
            @if (rejectError) {
              <p class="jx-review__error" role="alert">{{ rejectError }}</p>
            }
            <div class="jx-review__confirm">
              <button type="button" class="jx-review__btn" (click)="cancelReject()">
                Cancelar
              </button>
              <button
                type="button"
                class="jx-review__btn jx-review__btn--reject"
                (click)="confirmReject()"
              >
                Confirmar reprovação
              </button>
            </div>
          }
        }
      </div>
    </article>
  `,
  styleUrl: './review-row.component.scss',
})
export class KycReviewRowComponent {
  @Input({ required: true }) title = '';
  @Input() status: ReviewStatus = 'pending';
  /** Mono metadata (CPF MASKED, CNAE, "enviada há 5h", placa). */
  @Input() meta?: string;
  @Input() thumbUrl: string | null = null;
  @Input() thumbState: 'loading' | 'ready' | 'error' = 'ready';

  @Output() decide = new EventEmitter<ReviewDecision>();
  @Output() openFull = new EventEmitter<void>();
  @Output() reloadThumb = new EventEmitter<void>();

  protected readonly id = `jx-review-${Math.random().toString(36).slice(2, 8)}`;
  protected readonly reasons = REASON_LABELS;
  protected rejecting = false;
  protected reason: ReviewReason | undefined;
  protected detail = '';
  protected rejectError: string | null = null;

  protected get statusText(): string {
    switch (this.status) {
      case 'approved':
        return 'Aprovado';
      case 'approved_auto':
        return 'Aprovado (automático)';
      case 'rejected':
        return 'Reprovado';
      default:
        return 'Em análise';
    }
  }

  protected get statusIcon(): string {
    switch (this.status) {
      case 'approved':
      case 'approved_auto':
        return '✓';
      case 'rejected':
        return '!';
      default:
        return '◷';
    }
  }

  protected get statusCls(): string {
    switch (this.status) {
      case 'approved':
      case 'approved_auto':
        return 'success';
      case 'rejected':
        return 'error';
      default:
        return 'warning';
    }
  }

  protected cancelReject(): void {
    this.rejecting = false;
    this.reason = undefined;
    this.detail = '';
    this.rejectError = null;
  }

  protected confirmReject(): void {
    // error-ux: rejecting without a reason is blocked (the courier must know why).
    if (!this.reason) {
      this.rejectError = 'Selecione o motivo antes de reprovar.';
      return;
    }
    this.decide.emit({
      action: 'reject',
      reason: this.reason,
      detail: this.detail || undefined,
    });
    this.rejecting = false;
  }
}
