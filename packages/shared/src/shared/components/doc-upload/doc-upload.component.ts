import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';

/** The upload state machine (file-upload-ux — UI-SPEC §3.2). */
export type DocUploadState =
  | 'idle'
  | 'selecting'
  | 'compressing'
  | 'uploading'
  | 'success'
  | 'error';

/**
 * jx-doc-upload — capture/preview/validate/compress/upload of a KYC document
 * (UI-SPEC §3 / file-upload-ux + gesture-touch + owasp).
 *
 * The component is PRESENTATIONAL: the parent drives `state`/`progress`/`error`/
 * `previewUrl` (the actual presign PUT + compression run in the parent service so
 * the upload does not block the wizard). It exposes the file pick (camera or
 * gallery) and the retry. Status is ALWAYS text+icon, never colour alone (a11y);
 * progress is announced via aria-live; targets are ≥44px.
 *
 * Tokens: only semantic vars (design-tokens-system / dark-mode-theming) — no hex.
 */
@Component({
  selector: 'jx-doc-upload',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="jx-doc-up"
      [class.jx-doc-up--error]="state === 'error'"
      [attr.aria-busy]="busy ? 'true' : null"
    >
      @if (previewUrl) {
        <button
          type="button"
          class="jx-doc-up__preview"
          [class.jx-doc-up__preview--dim]="state === 'compressing' || state === 'uploading'"
          (click)="open.emit()"
          [attr.aria-label]="'Pré-visualização: ' + label"
        >
          <img [src]="previewUrl" [alt]="'Pré-visualização: ' + label" />
        </button>
      } @else {
        <div class="jx-doc-up__zone">
          <span class="jx-doc-up__icon" aria-hidden="true">▣</span>
          <p class="jx-doc-up__hint">{{ idleHint }}</p>
        </div>
      }

      <!-- Status line: text + icon, never colour alone (a11y). -->
      @if (state === 'compressing') {
        <p class="jx-doc-up__status" aria-live="polite">
          <span aria-hidden="true">…</span> Otimizando a imagem…
        </p>
      }
      @if (state === 'uploading') {
        <div
          class="jx-doc-up__bar"
          role="progressbar"
          [attr.aria-valuenow]="progress"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span class="jx-doc-up__bar-fill" [style.width.%]="progress"></span>
        </div>
        <p class="jx-doc-up__status jx-doc-up__status--mono" aria-live="polite">
          Enviando {{ progress }}%
        </p>
      }
      @if (state === 'success') {
        <p class="jx-doc-up__status jx-doc-up__status--ok" role="status">
          <span aria-hidden="true">✓</span> Enviado
        </p>
      }
      @if (state === 'error' && error) {
        <p class="jx-doc-up__status jx-doc-up__status--err" role="alert">
          <span aria-hidden="true">!</span> {{ error }}
        </p>
      }

      <div class="jx-doc-up__actions">
        @if (state === 'idle' || state === 'error') {
          <button type="button" class="jx-doc-up__btn jx-doc-up__btn--fill" (click)="camera.click()">
            {{ state === 'error' ? 'Tentar de novo' : 'Tirar foto' }}
          </button>
          <button type="button" class="jx-doc-up__btn" (click)="gallery.click()">
            Escolher da galeria
          </button>
        }
        @if (state === 'success') {
          <button type="button" class="jx-doc-up__btn" (click)="camera.click()">
            Trocar foto
          </button>
        }
      </div>

      <!-- Camera (capture) + gallery inputs. Operable by keyboard via the buttons. -->
      <input
        #camera
        class="jx-doc-up__file"
        type="file"
        accept="image/*"
        [attr.capture]="captureMode"
        [attr.aria-label]="'Tirar foto: ' + label"
        (change)="onPick($event)"
      />
      <input
        #gallery
        class="jx-doc-up__file"
        type="file"
        accept="image/*"
        [attr.aria-label]="'Escolher da galeria: ' + label"
        (change)="onPick($event)"
      />
    </div>
  `,
  styleUrl: './doc-upload.component.scss',
})
export class DocUploadComponent {
  /** Document label (for aria-labels — "CNH", "Selfie", …). */
  @Input({ required: true }) label = '';
  /** 'environment' (rear camera) for documents, 'user' (front) for selfie. */
  @Input() captureMode: 'environment' | 'user' = 'environment';
  @Input() state: DocUploadState = 'idle';
  @Input() progress = 0;
  @Input() previewUrl: string | null = null;
  @Input() error: string | null = null;

  /** A file was picked (camera or gallery) — the parent runs compress + presign. */
  @Output() fileSelected = new EventEmitter<File>();
  /** Open the preview full-screen (gesture-touch — tap to enlarge). */
  @Output() open = new EventEmitter<void>();

  protected readonly idleHint = 'Toque para tirar uma foto ou escolher da galeria';

  protected get busy(): boolean {
    return this.state === 'compressing' || this.state === 'uploading';
  }

  protected onPick(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      this.fileSelected.emit(file);
    }
    input.value = ''; // allow re-picking the same file
  }
}
