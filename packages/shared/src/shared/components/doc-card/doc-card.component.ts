import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import {
  DocUploadComponent,
  type DocUploadState,
} from '../doc-upload/doc-upload.component';

/** Per-item KYC status (mirrors the backend document status — UI-SPEC §4.2). */
export type DocStatus =
  | 'pending_upload'
  | 'pending'
  | 'uploading'
  | 'approved'
  | 'approved_auto'
  | 'rejected'
  | 'mei_pending';

interface BadgeSpec {
  text: string;
  icon: string;
  cls: string;
}

const BADGES: Record<DocStatus, BadgeSpec> = {
  pending_upload: { text: 'A enviar', icon: '○', cls: 'muted' },
  pending: { text: 'Em análise', icon: '◷', cls: 'warning' },
  uploading: { text: 'Enviando…', icon: '↑', cls: 'info' },
  approved: { text: 'Aprovado', icon: '✓', cls: 'success' },
  approved_auto: { text: 'Aprovado (automático)', icon: '✓', cls: 'success' },
  rejected: { text: 'Reprovado', icon: '!', cls: 'error' },
  mei_pending: { text: 'MEI pendente', icon: 'i', cls: 'warning' },
};

/**
 * jx-doc-card — a single KYC document with its per-item status (UI-SPEC §4 / D-04).
 *
 * Two modes: EDIT (wizard — composes jx-doc-upload) and READ (the entregador
 * watching analysis / the admin reviewing). The badge is ALWAYS text+icon+colour
 * (never colour alone — a11y). On a `rejected` item (E4) it shows the admin's
 * specific reason and re-opens the upload for THAT item only — an approved selfie
 * is never affected (status is independent per card).
 *
 * Tokens: only semantic vars; dark mode uses elevated surface + live semantic
 * colour (dark-mode-theming) — no `_bg` flat fills, no hex.
 */
@Component({
  selector: 'jx-doc-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DocUploadComponent],
  template: `
    <article class="jx-doc-card" [attr.aria-label]="title">
      <header class="jx-doc-card__head">
        <h3 class="jx-doc-card__title">{{ title }}</h3>
        <span class="jx-doc-card__badge jx-doc-card__badge--{{ badge.cls }}" role="status">
          <span aria-hidden="true">{{ badge.icon }}</span> {{ badge.text }}
        </span>
      </header>

      @if (purpose) {
        <p class="jx-doc-card__purpose">{{ purpose }}</p>
      }

      @if (mode === 'edit') {
        <jx-doc-upload
          [label]="title"
          [captureMode]="captureMode"
          [state]="uploadState"
          [progress]="progress"
          [previewUrl]="previewUrl"
          [error]="uploadError"
          (fileSelected)="fileSelected.emit($event)"
          (open)="open.emit()"
        />
      } @else if (previewUrl) {
        <button
          type="button"
          class="jx-doc-card__thumb"
          (click)="open.emit()"
          [attr.aria-label]="'Abrir documento: ' + title"
        >
          <img [src]="previewUrl" [alt]="title" />
        </button>
      }

      @if (meta) {
        <p class="jx-doc-card__meta">{{ meta }}</p>
      }

      <!-- E4: rejected item shows the specific reason + re-upload for THIS item only. -->
      @if (status === 'rejected' && rejectReason) {
        <p class="jx-doc-card__reject" role="alert">
          Motivo: {{ rejectReason }}
        </p>
        @if (mode === 'read') {
          <button type="button" class="jx-doc-card__resend" (click)="resend.emit()">
            Reenviar {{ title }}
          </button>
        }
      }
    </article>
  `,
  styleUrl: './doc-card.component.scss',
})
export class DocCardComponent {
  @Input({ required: true }) title = '';
  @Input() mode: 'edit' | 'read' = 'edit';
  @Input() status: DocStatus = 'pending_upload';
  @Input() captureMode: 'environment' | 'user' = 'environment';
  /** "Why we ask" microcopy (trust-safety). */
  @Input() purpose?: string;
  /** Mono metadata line (e.g. "enviado 23/04 · CNAE 5320-2/02"). */
  @Input() meta?: string;
  @Input() rejectReason?: string;
  @Input() previewUrl: string | null = null;

  // Forwarded to jx-doc-upload in edit mode.
  @Input() uploadState: DocUploadState = 'idle';
  @Input() progress = 0;
  @Input() uploadError: string | null = null;

  @Output() fileSelected = new EventEmitter<File>();
  @Output() open = new EventEmitter<void>();
  @Output() resend = new EventEmitter<void>();

  protected get badge(): BadgeSpec {
    return BADGES[this.status];
  }
}
