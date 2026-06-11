import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../../shared/state';
import {
  FavoriteRowComponent,
  BlockedRowComponent,
  type ScoreLevel,
} from '../../../shared/components';
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
      <p class="jx-favoritos__hint">
        Favoritos recebem suas ofertas primeiro, um por vez. Bloqueados nunca recebem suas
        ofertas — a lista é privada e não afeta o score de ninguém.
      </p>

      @if (loading()) {
        <jx-loading-skeleton variant="line" />
      } @else if (error()) {
        <jx-error-state message="Não deu pra carregar." retryLabel="Tentar de novo" (retry)="load()" />
      } @else {
        <section class="jx-favoritos__card" aria-labelledby="fav-title">
          <h2 id="fav-title" class="jx-favoritos__title">⭐ Favoritos (ordem de prioridade)</h2>
          @if (favorites().length === 0) {
            <jx-empty-state
              icon="⭐"
              title="Você ainda não tem favoritos."
              message="Marque a estrela em qualquer entrega concluída."
            />
          } @else {
            <ul class="jx-favoritos__list">
              @for (fav of favorites(); track fav.courier_id; let i = $index) {
                <jx-favorite-row
                  [position]="i + 1"
                  [name]="fav.courier_name"
                  [scoreLevel]="placeholderScoreLevel"
                  [scoreValue]="null"
                  [stats]="plateStats(fav)"
                  [canMoveUp]="i > 0"
                  [canMoveDown]="i < favorites().length - 1"
                  (moveUp)="moveUp(i)"
                  (moveDown)="moveDown(i)"
                  (remove)="removeFavorite(fav.courier_id)"
                />
              }
            </ul>
          }
        </section>

        <section class="jx-favoritos__card" aria-labelledby="blk-title">
          <h2 id="blk-title" class="jx-favoritos__title">🚫 Bloqueados</h2>
          @if (blocks().length === 0) {
            <jx-empty-state icon="🚫" title="Nenhum entregador bloqueado." />
          } @else {
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
        </section>
      }
    </main>
  `,
  styleUrl: './favoritos.page.scss',
})
export class FavoritosPage implements OnInit {
  private readonly service = inject(FavoritosService);

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

  /** Score endpoint lands later (ADR-013 — exhibited only); placeholder for now. */
  protected readonly placeholderScoreLevel: ScoreLevel = 'probation';

  protected plateStats(fav: FavoriteRow): string | null {
    return fav.vehicle_plate;
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
