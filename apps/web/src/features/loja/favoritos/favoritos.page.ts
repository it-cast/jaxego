import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';
import {
  FavoriteRowComponent,
  BlockedRowComponent,
} from '@jaxego/shared/components';
import { FavoritosService } from './favoritos.service';
import type { BlockedRow, FavoriteRow } from './favoritos.models';

/**
 * Tela 15 — Favoritos e bloqueados da loja (RN-014, D-06, web responsivo). Two
 * SEPARATE lists: favorites (reorderable cascade priority — D-01) and blocks
 * (private reason, never exposed to the courier). Reorder ↑/↓ persists the
 * priority. Tokens only — no hex (Gate 2). Score level is a placeholder until the
 * scoring endpoint lands (ADR-013 — exhibited only).
 */
@Component({
  selector: 'jx-loja-favoritos',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FavoriteRowComponent,
    BlockedRowComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingSkeletonComponent,
  ],
  template: `
    <main class="jx-favoritos">
      <h1 class="jx-favoritos__page-title">Favoritos e Bloqueados</h1>

      <div class="jx-favoritos__tabs" role="tablist" aria-label="Lista">
        <button
          type="button"
          role="tab"
          class="jx-favoritos__tab"
          [class.jx-favoritos__tab--active]="tab() === 'favorites'"
          [attr.aria-selected]="tab() === 'favorites'"
          (click)="tab.set('favorites')"
        >
          Favoritos
        </button>
        <button
          type="button"
          role="tab"
          class="jx-favoritos__tab"
          [class.jx-favoritos__tab--active]="tab() === 'blocked'"
          [attr.aria-selected]="tab() === 'blocked'"
          (click)="tab.set('blocked')"
        >
          Bloqueados
        </button>
      </div>

      @if (loading()) {
        <jx-loading-skeleton variant="line" />
      } @else if (error()) {
        <jx-error-state message="Não deu pra carregar." retryLabel="Tentar de novo" (retry)="load()" />
      } @else if (tab() === 'favorites') {
        @if (favorites().length === 0) {
          <jx-empty-state
            icon=""
            title="Você ainda não tem favoritos."
            message="Marque a estrela em qualquer entrega concluída."
          />
        } @else {
          <p class="jx-favoritos__hint">Favoritos recebem suas ofertas primeiro, na ordem abaixo.</p>
          <ul class="jx-favoritos__list">
            @for (fav of favorites(); track fav.courier_id; let i = $index) {
              <jx-favorite-row
                [position]="i + 1"
                [name]="fav.courier_name"
                [avgStars]="fav.avg_stars"
                [canMoveUp]="i > 0"
                [canMoveDown]="i < favorites().length - 1"
                (moveUp)="moveUp(i)"
                (moveDown)="moveDown(i)"
                (remove)="removeFavorite(fav.courier_id)"
              />
            }
          </ul>
        }
      } @else {
        @if (blocks().length === 0) {
          <jx-empty-state
            icon=""
            title="Nenhum entregador bloqueado."
            message="Bloqueados nunca recebem suas ofertas. A lista é privada."
          />
        } @else {
          <p class="jx-favoritos__hint">Bloqueados nunca recebem suas ofertas — a lista é privada.</p>
          <ul class="jx-favoritos__list">
            @for (blk of blocks(); track blk.courier_id) {
              <jx-blocked-row
                [name]="blk.courier_name"
                [blockedAt]="formatDate(blk.created_at)"
                [reason]="blk.reason"
                (unblock)="unblock(blk.courier_id)"
              />
            }
          </ul>
        }
      }
    </main>
  `,
  styleUrl: './favoritos.page.scss',
})
export class FavoritosPage implements OnInit {
  private readonly service = inject(FavoritosService);

  protected readonly tab = signal<'favorites' | 'blocked'>('favorites');
  protected readonly favorites = signal<FavoriteRow[]>([]);
  protected readonly blocks = signal<BlockedRow[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  ngOnInit(): void {
    void this.load();
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      const [favs, blks] = await Promise.all([
        this.service.listFavorites(),
        this.service.listBlocks(),
      ]);
      this.favorites.set([...favs].sort((a, b) => a.priority - b.priority));
      this.blocks.set(blks);
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }


  protected formatDate(iso: string | null): string | null {
    if (!iso) return null;
    const d = new Date(iso);
    return Number.isNaN(d.getTime())
      ? null
      : d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
  }

  protected async moveUp(index: number): Promise<void> {
    if (index <= 0) return;
    await this.swapAndPersist(index, index - 1);
  }

  protected async moveDown(index: number): Promise<void> {
    const list = this.favorites();
    if (index >= list.length - 1) return;
    await this.swapAndPersist(index, index + 1);
  }

  private async swapAndPersist(a: number, b: number): Promise<void> {
    const list = [...this.favorites()];
    [list[a], list[b]] = [list[b], list[a]];
    this.favorites.set(list); // optimistic
    await this.service.reorderFavorites(list.map((f) => f.courier_id));
  }

  protected async removeFavorite(courierId: number): Promise<void> {
    await this.service.removeFavorite(courierId);
    this.favorites.set(this.favorites().filter((f) => f.courier_id !== courierId));
  }

  protected async unblock(courierId: number): Promise<void> {
    await this.service.removeBlock(courierId);
    this.blocks.set(this.blocks().filter((b) => b.courier_id !== courierId));
  }
}
