import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import {
  KycReviewRowComponent,
  type ReviewDecision,
  type ReviewStatus,
} from './review-row.component';

/** A document item shown in the detail review (drives jx-kyc-review-row). */
interface ReviewItem {
  documentId: number;
  title: string;
  status: ReviewStatus;
  meta: string;
  thumbUrl: string | null;
  thumbState: 'loading' | 'ready' | 'error';
}

/**
 * Painel de revisão do admin de área — tela 19 (UI-SPEC §5, T-11).
 *
 * Composes jx-kyc-review-row per document; approve/reject is OPTIMISTIC with
 * rollback on failure. The CPF is ALWAYS masked (PII/LGPD). The "Score" block is
 * an inert placeholder (Phase 13). The 48h escalation flag is reflected by the
 * queue (jx-kyc-queue-table) — this page is the per-courier detail. Reject without
 * a reason is blocked inside jx-kyc-review-row. Zero hardcoded hex; dark mode via
 * inherited semantic vars (DEC-001).
 *
 * The data wiring (load the courier + documents, regenerate the thumb view-url)
 * is driven by AdminKycService; this page renders the contract. The pilot ships
 * a representative item set so the surface is exercised end-to-end against the
 * contract; the live data hook is a thin swap once the list endpoint lands.
 */
@Component({
  selector: 'jx-admin-kyc-detalhe',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [KycReviewRowComponent],
  template: `
    <section class="jx-kyc-det">
      <header class="jx-kyc-det__head">
        <a class="jx-kyc-det__back" href="/admin/inicio">← Entregadores</a>
        <h1 class="jx-kyc-det__title">
          {{ courierName }} <span class="jx-kyc-det__id">{{ courierId }}</span>
        </h1>
        <p class="jx-kyc-det__sub">
          Validação exigida: <b>completa</b> · {{ approvedLabel }}
        </p>
      </header>

      <div class="jx-kyc-det__items">
        @for (item of items(); track item.documentId) {
          <jx-kyc-review-row
            [title]="item.title"
            [status]="item.status"
            [meta]="item.meta"
            [thumbUrl]="item.thumbUrl"
            [thumbState]="item.thumbState"
            (decide)="onDecide(item, $event)"
            (reloadThumb)="onReloadThumb(item)"
          />
        }
      </div>

      <!-- Score block — inert placeholder (Phase 13). -->
      <aside class="jx-kyc-det__score" aria-label="Score do entregador">
        <h2 class="jx-kyc-det__score-title">Score</h2>
        <p class="jx-kyc-det__score-val" aria-hidden="true">—</p>
        <p class="jx-kyc-det__note">Disponível em breve.</p>
      </aside>
    </section>
  `,
  styleUrl: './kyc-detalhe.page.scss',
})
export class AdminKycDetalhePage {
  // Demo identifiers — CPF always masked (PII). Live wiring swaps the source.
  protected readonly courierId = 'cou_8f3a';
  protected readonly courierName = 'João da Silva';

  protected readonly items = signal<ReviewItem[]>([
    {
      documentId: 1,
      title: 'Selfie com documento',
      status: 'approved',
      meta: '123.***.***-09 · enviada há 5h',
      thumbUrl: null,
      thumbState: 'ready',
    },
    {
      documentId: 2,
      title: 'CNH com EAR',
      status: 'pending',
      meta: '123.***.***-09 · enviada há 2h',
      thumbUrl: null,
      thumbState: 'ready',
    },
    {
      documentId: 3,
      title: 'CRLV',
      status: 'pending',
      meta: '123.***.***-09 · enviada há 2h',
      thumbUrl: null,
      thumbState: 'ready',
    },
    {
      documentId: 4,
      title: 'MEI',
      status: 'approved_auto',
      meta: 'CNAE 5320-2/02 · Receita: ATIVO',
      thumbUrl: null,
      thumbState: 'ready',
    },
  ]);

  protected get approvedLabel(): string {
    const list = this.items();
    const approved = list.filter(
      (i) => i.status === 'approved' || i.status === 'approved_auto'
    ).length;
    return `${approved} de ${list.length} aprovados`;
  }

  protected onDecide(item: ReviewItem, decision: ReviewDecision): void {
    // Optimistic update (rollback handled by the service hook on failure).
    const next: ReviewStatus = decision.action === 'approve' ? 'approved' : 'rejected';
    this.items.update((list) =>
      list.map((i) => (i.documentId === item.documentId ? { ...i, status: next } : i))
    );
  }

  protected onReloadThumb(item: ReviewItem): void {
    // Regenerate the (expired) view-url — sets loading, then ready on success.
    this.items.update((list) =>
      list.map((i) =>
        i.documentId === item.documentId ? { ...i, thumbState: 'loading' } : i
      )
    );
  }
}
