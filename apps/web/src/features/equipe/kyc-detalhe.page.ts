import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  KycReviewRowComponent,
  type ReviewDecision,
  type ReviewStatus,
} from '../admin/kyc/review-row.component';
import { EquipeKycService, type CourierDetail } from './equipe-kyc.service';

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
  selector: 'jx-equipe-kyc-detalhe',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, KycReviewRowComponent],
  template: `
    <section class="jx-kyc-det">
      <header class="jx-kyc-det__head">
        <a class="jx-kyc-det__back" routerLink="/equipe/entregadores">← Entregadores</a>

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

      @if (items().length > 0) {
        <div class="jx-kyc-det__filters">
          <label class="jx-kyc-det__filter">
            <span>Documento</span>
            <select [value]="filterKind()" (change)="filterKind.set($any($event.target).value)">
              <option value="all">Todos</option>
              @for (k of availableKinds(); track k) {
                <option [value]="k">{{ kindLabel(k) }}</option>
              }
            </select>
          </label>
          <label class="jx-kyc-det__filter">
            <span>Status</span>
            <select [value]="filterStatus()" (change)="filterStatus.set($any($event.target).value)">
              <option value="all">Todos</option>
              <option value="pending">Em análise</option>
              <option value="approved">Aprovado</option>
              <option value="rejected">Reprovado</option>
              <option value="pending_upload">Aguardando envio</option>
            </select>
          </label>
        </div>
      }

      @if (filteredItems().length === 0 && items().length > 0 && !loading()) {
        <p class="jx-kyc-det__empty">Nenhum documento com esse filtro.</p>
      }

      <div class="jx-kyc-det__items">
        @for (item of filteredItems(); track item.documentId) {
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
    </section>

    @if (lightboxUrl()) {
      <div class="jx-lightbox" (click)="closeLightbox()" role="dialog" aria-modal="true" aria-label="Visualizar documento">
        <button type="button" class="jx-lightbox__close" aria-label="Fechar">✕</button>
        <img class="jx-lightbox__img" [src]="lightboxUrl()" [alt]="lightboxTitle()" (click)="$event.stopPropagation()" />
      </div>
    }
  `,
  styleUrl: '../admin/kyc/kyc-detalhe.page.scss',
})
export class EquipeKycDetalhePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly svc = inject(EquipeKycService);

  protected readonly courier = signal<CourierDetail | null>(null);
  protected readonly items = signal<ReviewItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly lightboxUrl = signal<string | null>(null);
  protected readonly lightboxTitle = signal('');

  protected readonly filterKind = signal<string>('all');
  protected readonly filterStatus = signal<string>('pending');

  protected readonly filteredItems = computed(() => {
    let list = this.items();
    const kind = this.filterKind();
    const status = this.filterStatus();
    if (kind !== 'all') list = list.filter(i => i.kind === kind);
    if (status !== 'all') list = list.filter(i => i.status === status);
    return list;
  });

  protected readonly availableKinds = computed(() => [...new Set(this.items().map(i => i.kind))]);

  private get courierId(): number {
    return Number(this.route.snapshot.paramMap.get('courierId'));
  }

  async ngOnInit(): Promise<void> {
    const c = await this.svc.getCourier(this.courierId);
    this.courier.set(c);
    this.loading.set(false);
    if (!c) return;

    const reviewItems: ReviewItem[] = c.documents.map(d => ({
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
    for (const item of reviewItems) this.loadThumb(item);
  }

  private async loadThumb(item: ReviewItem): Promise<void> {
    const url = await this.svc.viewUrl(this.courierId, item.documentId);
    this.items.update(list =>
      list.map(i => i.documentId === item.documentId
        ? { ...i, thumbUrl: url, thumbState: url ? 'ready' as const : 'error' as const }
        : i
      )
    );
  }

  protected get approvedLabel(): string {
    const list = this.items();
    if (!list.length) return '';
    return `${list.filter(i => i.status === 'approved').length} de ${list.length} aprovados`;
  }

  protected async onDecide(item: ReviewItem, decision: ReviewDecision): Promise<void> {
    const next: ReviewStatus = decision.action === 'approve' ? 'approved' : 'rejected';
    this.items.update(list => list.map(i => i.documentId === item.documentId ? { ...i, status: next } : i));

    const ok = decision.action === 'approve'
      ? await this.svc.approve(this.courierId, item.documentId)
      : await this.svc.reject(this.courierId, item.documentId, decision.reason ?? 'outro');

    if (!ok) {
      this.items.update(list => list.map(i => i.documentId === item.documentId ? { ...i, status: item.status } : i));
    } else {
      const c = await this.svc.getCourier(this.courierId);
      if (c) this.courier.set(c);
    }
  }

  protected kindLabel(kind: string): string { return KIND_LABELS[kind] ?? kind; }

  protected openLightbox(item: ReviewItem): void {
    if (item.thumbUrl) { this.lightboxUrl.set(item.thumbUrl); this.lightboxTitle.set(item.title); }
  }

  protected closeLightbox(): void { this.lightboxUrl.set(null); }

  protected async onReloadThumb(item: ReviewItem): Promise<void> {
    this.items.update(list => list.map(i => i.documentId === item.documentId ? { ...i, thumbState: 'loading' as const } : i));
    await this.loadThumb(item);
  }
}
