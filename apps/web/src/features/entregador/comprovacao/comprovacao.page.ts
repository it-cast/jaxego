import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import {
  DirectPaymentConfirmComponent,
  DirectPaymentOutcome,
} from '../../../shared/components/direct-payment-confirm/direct-payment-confirm.component';
import { GeofenceState } from '../../../shared/components/geofence-pill/geofence-pill.component';
import {
  PendingUploadBannerComponent,
} from '../../../shared/components/pending-upload-banner/pending-upload-banner.component';
import {
  ProofCaptureComponent,
  ProofCapturePayload,
} from '../../../shared/components/proof-capture/proof-capture.component';
import { PendingUploadService } from './pending-upload.service';
import { ProofKind, ProofService } from './proof.service';

/**
 * Comprovação (tela 07) — courier proof capture for the active delivery (F-06).
 *
 * Composes jx-proof-capture (camera + GPS) + the geofence pill + direct payment
 * confirm. The CTA verdict is server-side: a geofence failure shows the pill 'out'
 * and keeps the courier on the screen; 3 failures → 'low_confidence' destrava (the
 * delivery proceeds, admin reviews). Offline: the photo queues (jx-pending-upload-banner)
 * and the delivery does NOT show concluded until the upload + validation succeed.
 */
@Component({
  selector: 'jx-comprovacao-page',
  standalone: true,
  imports: [ProofCaptureComponent, DirectPaymentConfirmComponent, PendingUploadBannerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <main class="jx-proof-page">
      <h1 class="jx-proof-page__title">Comprovar {{ kindLabel() }}</h1>

      <jx-pending-upload-banner [count]="pending.count()" [online]="pending.online()" />

      <jx-proof-capture
        [label]="kindLabel()"
        [geofence]="geofence()"
        [uploadState]="uploadState()"
        [previewUrl]="previewUrl()"
        [error]="error()"
        (captured)="onCaptured($event)"
      />

      @if (paymentNeeded()) {
        <div class="jx-proof-page__ref">
          <label for="refNum">Número do pedido (pergunte ao destinatário)</label>
          <input
            id="refNum"
            class="jx-proof-page__refinput"
            inputmode="numeric"
            maxlength="6"
            placeholder="0000"
            [value]="reference()"
            (input)="onRefInput($event)"
          />
          <button
            type="button"
            class="jx-proof-page__refbtn"
            [disabled]="reference().length < 3"
            (click)="onReference()"
          >
            Enviar número do pedido
          </button>
          @if (referenceSent()) {
            <p class="jx-proof-page__refok" role="status">Número registrado ✓</p>
          }
        </div>
      }

      @if (state() === 'ENTREGUE' && paymentNeeded()) {
        <jx-direct-payment-confirm
          [amountLabel]="amountLabel"
          (confirm)="onPaymentConfirm($event)"
        />
      }

      @if (lowConfidence()) {
        <p class="jx-proof-page__lowconf" role="status" aria-live="polite">
          Não conseguimos confirmar a localização. Sua entrega segue para revisão da
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
  protected readonly pending = inject(PendingUploadService);

  protected readonly geofence = signal<GeofenceState>('checking');
  protected readonly uploadState = signal<'idle' | 'uploading' | 'success' | 'error'>('idle');
  protected readonly previewUrl = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly state = signal<string>('');
  protected readonly lowConfidence = signal(false);
  protected readonly reference = signal('');
  protected readonly referenceSent = signal(false);

  private deliveryId = 0;
  private kind: ProofKind = 'pickup';
  protected amountLabel = '';

  ngOnInit(): void {
    this.deliveryId = Number(this.route.snapshot.paramMap.get('id') ?? 0);
    this.kind = (this.route.snapshot.paramMap.get('kind') as ProofKind) ?? 'pickup';
  }

  protected kindLabel(): string {
    return { pickup: 'a coleta', delivery: 'a entrega', refusal: 'a recusa' }[this.kind];
  }

  protected paymentNeeded(): boolean {
    return this.kind === 'delivery';
  }

  protected async onCaptured(payload: ProofCapturePayload): Promise<void> {
    this.error.set(null);
    this.previewUrl.set(URL.createObjectURL(payload.file));
    // Offline → queue, reassure, do NOT conclude.
    if (!this.pending.online()) {
      this.pending.enqueue({
        deliveryId: this.deliveryId,
        proofKind: this.kind,
        file: payload.file,
        lat: payload.lat,
        lng: payload.lng,
      });
      return;
    }
    this.uploadState.set('uploading');
    try {
      const result = await this.proof.submitPhoto(
        this.deliveryId,
        this.kind,
        payload.file,
        payload.lat,
        payload.lng,
      );
      this.uploadState.set('success');
      this.state.set(result.state);
      this.geofence.set(result.geofence_ok ? 'ok' : result.low_confidence ? 'low_confidence' : 'out');
      this.lowConfidence.set(result.low_confidence);
      // Wire-through (F1.3): pickup → back to the active delivery (now COLETADA);
      // refusal → done screen; delivery waits for the direct-payment confirm.
      if (this.kind === 'pickup') {
        void this.router.navigate(['/entregador/entrega-ativa']);
      } else if (this.kind === 'refusal') {
        void this.router.navigate(['/entregador/entrega', this.deliveryId, 'concluida']);
      }
    } catch {
      this.uploadState.set('error');
      this.error.set('Não foi possível enviar a foto agora. Tente de novo.');
      this.geofence.set('out');
    }
  }

  protected onRefInput(e: Event): void {
    this.reference.set((e.target as HTMLInputElement).value);
  }

  protected async onReference(): Promise<void> {
    const ref = this.reference().trim();
    if (ref.length < 3) return;
    try {
      await this.proof.submitReference(this.deliveryId, ref);
      this.referenceSent.set(true);
    } catch {
      this.referenceSent.set(false);
    }
  }

  protected async onPaymentConfirm(outcome: DirectPaymentOutcome): Promise<void> {
    await this.proof.confirmPayment(this.deliveryId, outcome, null);
    void this.router.navigate(['/entregador/entrega', this.deliveryId, 'concluida']);
  }
}
