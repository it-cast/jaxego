import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import {
  DirectPaymentConfirmComponent,
  DirectPaymentOutcome,
} from '@jaxego/shared/components/direct-payment-confirm/direct-payment-confirm.component';
import { GeofenceState } from '@jaxego/shared/components/geofence-pill/geofence-pill.component';
import {
  PendingUploadBannerComponent,
} from '@jaxego/shared/components/pending-upload-banner/pending-upload-banner.component';
import {
  ProofCaptureComponent,
  ProofCapturePayload,
} from '@jaxego/shared/components/proof-capture/proof-capture.component';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { EntregadorService } from '../entregador.service';
import { PendingUploadService } from './pending-upload.service';
import { ConfirmDialogComponent, PageHeaderComponent } from '@jaxego/shared/components';
import { ProofKind, ProofService } from './proof.service';

@Component({
  selector: 'jx-comprovacao-page',
  standalone: true,
  imports: [ProofCaptureComponent, DirectPaymentConfirmComponent, PendingUploadBannerComponent, PageHeaderComponent, ConfirmDialogComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-proof-page">
      <jx-page-header [title]="'Comprovar ' + kindLabel()" backLink="/entregador/entrega-ativa" />

      <jx-pending-upload-banner [count]="pending.count()" [online]="pending.online()" />

      <jx-proof-capture
        [label]="kindLabel()"
        [geofence]="geofence()"
        [uploadState]="captureState()"
        [previewUrl]="previewUrl()"
        [error]="error()"
        (captured)="onCaptured($event)"
      />

      @if (photoReady() && needsReference()) {
        <div class="jx-proof-page__ref">
          <label for="refNum">Número do pedido (pergunte ao destinatário)</label>
          <input
            id="refNum"
            class="jx-proof-page__refinput"
            inputmode="numeric"
            maxlength="6"
            placeholder="0000"
            [value]="reference()"
            [disabled]="referenceValidated()"
            (input)="onRefInput($event)"
          />
          @if (refMessage(); as msg) {
            <p
              class="jx-proof-page__ref-msg"
              [class.jx-proof-page__ref-msg--ok]="referenceValidated()"
              [class.jx-proof-page__ref-msg--err]="!referenceValidated()"
              role="alert"
            >
              {{ msg }}
            </p>
          }
          @if (!referenceValidated()) {
            <button
              type="button"
              class="jx-proof-page__refbtn"
              [disabled]="reference().length < 3 || validatingRef()"
              (click)="validateReference()"
            >
              {{ validatingRef() ? 'Validando...' : 'Validar número' }}
            </button>
          }
        </div>
      }

      @if (canFinalize() && kind === 'delivery') {
        <button
          type="button"
          class="jx-proof-page__finalize"
          [disabled]="finalizing()"
          (click)="askFinalize()"
        >
          @if (finalizing()) {
            <span class="jx-proof-page__spinner" aria-hidden="true"></span>
            Finalizando...
          } @else {
            Finalizar entrega
          }
        </button>
      }

      @if (confirmingFinalize()) {
        <jx-confirm-dialog
          title="Deseja realmente finalizar a entrega?"
          message="Confirme que a entrega foi concluída com sucesso."
          confirmLabel="Finalizar entrega"
          (confirm)="confirmingFinalize.set(false); finalize()"
          (cancel)="confirmingFinalize.set(false)"
        />
      }

      @if (lowConfidence()) {
        <p class="jx-proof-page__lowconf" role="status" aria-live="polite">
          Não conseguimos confirmar a localização. Sua entrega segue para revisao da
          equipe — você pode concluir mesmo assim.
        </p>
      }
    </main>
  `,
  styleUrl: './comprovacao.page.scss',
})
export class ComprovacaoPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly proof = inject(ProofService);
  private readonly entregador = inject(EntregadorService);
  private readonly auth = inject(AuthService);
  protected readonly pending = inject(PendingUploadService);

  protected readonly geofence = signal<GeofenceState>('checking');
  protected readonly captureState = signal<'idle' | 'uploading' | 'success' | 'error'>('idle');
  protected readonly previewUrl = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly lowConfidence = signal(false);
  protected readonly proofMethod = signal<string>('photo');

  protected readonly photoReady = signal(false);
  protected readonly reference = signal('');
  protected readonly referenceValidated = signal(false);
  protected readonly validatingRef = signal(false);
  protected readonly refMessage = signal<string | null>(null);
  protected readonly finalizing = signal(false);
  protected readonly confirmingFinalize = signal(false);

  private deliveryId = 0;
  protected kind: ProofKind = 'pickup';
  protected amountLabel = '';
  private capturedPayload: ProofCapturePayload | null = null;

  async ngOnInit(): Promise<void> {
    this.deliveryId = Number(this.route.snapshot.paramMap.get('id') ?? 0);
    this.kind = (this.route.snapshot.paramMap.get('kind') as ProofKind) ?? 'pickup';
    await this.loadDeliveryProofMethod();
  }

  private async loadDeliveryProofMethod(): Promise<void> {
    try {
      const me = this.auth.me();
      if (!me?.courier_id) return;
      const delivery = await this.entregador.getDelivery(me.courier_id, this.deliveryId);
      this.proofMethod.set(delivery.proof_method ?? 'photo');
    } catch { /* fallback photo */ }
  }

  protected kindLabel(): string {
    return { pickup: 'a coleta', delivery: 'a entrega', refusal: 'a recusa' }[this.kind];
  }

  protected needsReference(): boolean {
    return this.kind === 'delivery' && this.proofMethod() === 'photo_reference';
  }

  protected canFinalize(): boolean {
    if (!this.photoReady()) return false;
    if (this.needsReference() && !this.referenceValidated()) return false;
    return true;
  }

  private readonly MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  protected onCaptured(payload: ProofCapturePayload): void {
    this.error.set(null);

    if (payload.file.size > this.MAX_FILE_SIZE) {
      this.error.set('A imagem é muito grande (máximo 10MB). Tire outra foto ou selecione uma imagem menor.');
      this.captureState.set('error');
      return;
    }

    this.previewUrl.set(URL.createObjectURL(payload.file));
    this.capturedPayload = payload;

    if (this.kind === 'pickup' || this.kind === 'refusal') {
      void this.submitAndNavigate(payload);
      return;
    }
    this.photoReady.set(true);
    this.captureState.set('idle');
  }

  private async submitAndNavigate(payload: ProofCapturePayload): Promise<void> {
    if (!this.pending.online()) {
      this.pending.enqueue({
        deliveryId: this.deliveryId, proofKind: this.kind,
        file: payload.file, lat: payload.lat, lng: payload.lng,
      });
      return;
    }
    this.captureState.set('uploading');
    try {
      const result = await this.proof.submitPhoto(
        this.deliveryId, this.kind, payload.file, payload.lat, payload.lng,
      );
      this.captureState.set('success');
      this.geofence.set(result.geofence_ok ? 'ok' : result.low_confidence ? 'low_confidence' : 'out');
      this.lowConfidence.set(result.low_confidence);
      if (this.kind === 'pickup') {
        void this.router.navigate(['/entregador/entrega-ativa']);
      } else if (this.kind === 'refusal') {
        void this.router.navigate(['/entregador/entrega', this.deliveryId, 'concluida']);
      }
    } catch (err: any) {
      this.captureState.set('error');
      const status = err?.status;
      if (status === 413 || status === 400) {
        this.error.set('A imagem é muito grande. Tire outra foto ou selecione uma imagem menor.');
      } else {
        this.error.set('Não foi possível enviar a foto agora. Tente de novo.');
      }
    }
  }

  protected onRefInput(e: Event): void {
    this.reference.set((e.target as HTMLInputElement).value);
    this.refMessage.set(null);
    this.referenceValidated.set(false);
  }

  protected async validateReference(): Promise<void> {
    const ref = this.reference().trim();
    if (ref.length < 3) return;
    this.validatingRef.set(true);
    this.refMessage.set(null);
    try {
      const valid = await this.proof.validateReference(this.deliveryId, ref);
      if (valid) {
        this.referenceValidated.set(true);
        this.refMessage.set('Número do pedido correto.');
      } else {
        this.referenceValidated.set(false);
        this.refMessage.set('Número do pedido incorreto. Verifique e tente novamente.');
      }
    } catch {
      this.referenceValidated.set(false);
      this.refMessage.set('Erro ao validar. Tente novamente.');
    } finally {
      this.validatingRef.set(false);
    }
  }

  protected askFinalize(): void {
    this.confirmingFinalize.set(true);
  }

  protected async finalize(): Promise<void> {
    if (!this.capturedPayload || this.finalizing()) return;
    this.finalizing.set(true);
    this.error.set(null);
    try {
      if (!this.pending.online()) {
        this.pending.enqueue({
          deliveryId: this.deliveryId, proofKind: this.kind,
          file: this.capturedPayload.file, lat: this.capturedPayload.lat, lng: this.capturedPayload.lng,
        });
        this.finalizing.set(false);
        return;
      }
      await this.proof.submitPhoto(
        this.deliveryId, this.kind,
        this.capturedPayload.file, this.capturedPayload.lat, this.capturedPayload.lng,
      );
      void this.router.navigate(['/entregador/entrega', this.deliveryId, 'concluida']);
    } catch (err: any) {
      const status = err?.status;
      if (status === 413 || status === 400) {
        this.error.set('A imagem é muito grande. Tire outra foto ou selecione uma imagem menor.');
      } else {
        this.error.set('Não foi possível finalizar. Tente de novo.');
      }
      this.finalizing.set(false);
    }
  }
}
