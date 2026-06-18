import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  KycReviewRowComponent,
  type ReviewDecision,
  type ReviewStatus,
} from './review-row.component';
import {
  AdminKycService,
  type CourierDetail,
  type CourierDocumentAdmin,
} from './kyc.service';

interface ReviewItem {
  documentId: number;
  kind: string;
  title: string;
  status: ReviewStatus;
  meta: string;
  thumbUrl: string | null;
  thumbState: 'loading' | 'ready' | 'error';
  rejectReason: string | null;
  rejectDetail: string | null;
}

const KIND_LABELS: Record<string, string> = {
  selfie: 'Selfie com documento',
  cnh: 'CNH com EAR',
  crlv: 'CRLV',
  antecedentes: 'Antecedentes',
  mei: 'MEI',
};

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `enviada há ${mins}min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `enviada há ${hours}h`;
  return `enviada há ${Math.floor(hours / 24)}d`;
}

@Component({
  selector: 'jx-admin-kyc-detalhe',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, KycReviewRowComponent],
  template: `
    <section class="jx-kyc-det">
      <header class="jx-kyc-det__head">
        <a class="jx-kyc-det__back" routerLink="/admin/entregadores">← Entregadores</a>

        @if (courier(); as c) {
          <h1 class="jx-kyc-det__title">
            {{ c.full_name }} <span class="jx-kyc-det__id">{{ c.cpf_masked }}</span>
          </h1>
          <p class="jx-kyc-det__sub">
            Validação exigida: <b>{{ c.kyc_level }}</b> · {{ c.vehicle_type }}{{ c.vehicle_plate ? ' · ' + c.vehicle_plate : '' }} · {{ approvedLabel }}
          </p>
        } @else if (loading()) {
          <p>Carregando…</p>
        } @else {
          <p>Entregador não encontrado.</p>
        }
      </header>

      @if (items().length === 0 && !loading()) {
        <p class="jx-kyc-det__empty">Nenhum documento enviado ainda.</p>
      }

      <div class="jx-kyc-det__items">
        @for (item of items(); track item.documentId) {
          <jx-kyc-review-row
            [title]="item.title"
            [status]="item.status"
            [meta]="item.meta"
            [thumbUrl]="item.thumbUrl"
            [thumbState]="item.thumbState"
            (decide)="onDecide(item, $event)"
            (openFull)="openLightbox(item)"
            (reloadThumb)="onReloadThumb(item)"
          />
        }
      </div>

      <aside class="jx-kyc-det__score" aria-label="Score do entregador">
        <h2 class="jx-kyc-det__score-title">Score</h2>
        <p class="jx-kyc-det__score-val" aria-hidden="true">—</p>
        <p class="jx-kyc-det__note">Disponível em breve.</p>
      </aside>
    </section>

    @if (lightboxUrl()) {
      <div class="jx-lightbox" (click)="closeLightbox()" role="dialog" aria-modal="true" aria-label="Visualizar documento">
        <button type="button" class="jx-lightbox__close" aria-label="Fechar">✕</button>
        <img class="jx-lightbox__img" [src]="lightboxUrl()" [alt]="lightboxTitle()" (click)="$event.stopPropagation()" />
      </div>
    }
  `,
  styleUrl: './kyc-detalhe.page.scss',
})
export class AdminKycDetalhePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly kycService = inject(AdminKycService);

  protected readonly courier = signal<CourierDetail | null>(null);
  protected readonly items = signal<ReviewItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly lightboxUrl = signal<string | null>(null);
  protected readonly lightboxTitle = signal('');

  private get courierId(): number {
    return Number(this.route.snapshot.paramMap.get('courierId'));
  }

  async ngOnInit(): Promise<void> {
    const c = await this.kycService.getCourier(this.courierId);
    this.courier.set(c);
    this.loading.set(false);
    if (!c) return;

    const reviewItems: ReviewItem[] = c.documents.map((d) => ({
      documentId: d.id,
      kind: d.kind,
      title: KIND_LABELS[d.kind] ?? d.kind,
      status: d.status as ReviewStatus,
      meta: `${c.cpf_masked} · ${timeAgo(d.created_at)}`,
      thumbUrl: null,
      thumbState: 'loading' as const,
      rejectReason: d.reject_reason,
      rejectDetail: d.reject_detail,
    }));
    this.items.set(reviewItems);

    for (const item of reviewItems) {
      this.loadThumb(item);
    }
  }

  private async loadThumb(item: ReviewItem): Promise<void> {
    const url = await this.kycService.viewUrl(this.courierId, item.documentId);
    this.items.update((list) =>
      list.map((i) =>
        i.documentId === item.documentId
          ? { ...i, thumbUrl: url, thumbState: url ? 'ready' as const : 'error' as const }
          : i
      )
    );
  }

  protected get approvedLabel(): string {
    const list = this.items();
    if (list.length === 0) return '';
    const approved = list.filter(
      (i) => i.status === 'approved' || i.status === 'approved_auto'
    ).length;
    return `${approved} de ${list.length} aprovados`;
  }

  protected async onDecide(item: ReviewItem, decision: ReviewDecision): Promise<void> {
    const next: ReviewStatus = decision.action === 'approve' ? 'approved' : 'rejected';
    this.items.update((list) =>
      list.map((i) => (i.documentId === item.documentId ? { ...i, status: next } : i))
    );
    const result = await this.kycService.review(this.courierId, item.documentId, decision);
    if (!result) {
      this.items.update((list) =>
        list.map((i) => (i.documentId === item.documentId ? { ...i, status: item.status } : i))
      );
    } else {
      const c = this.courier();
      if (c) this.courier.set({ ...c, status: result.courier_status });
    }
  }

  protected openLightbox(item: ReviewItem): void {
    if (item.thumbUrl) {
      this.lightboxUrl.set(item.thumbUrl);
      this.lightboxTitle.set(item.title);
    }
  }

  protected closeLightbox(): void {
    this.lightboxUrl.set(null);
  }

  protected async onReloadThumb(item: ReviewItem): Promise<void> {
    this.items.update((list) =>
      list.map((i) =>
        i.documentId === item.documentId ? { ...i, thumbState: 'loading' as const } : i
      )
    );
    await this.loadThumb(item);
  }
}
