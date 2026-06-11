import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { BlockedRow, FavoriteRow } from './favoritos.models';

/**
 * FavoritosService — the store's favorites/blocks client (Phase 8, RN-014). Two
 * SEPARATE lists. Reorder persists the cascade priority (D-01). The block reason
 * is the store's private note (never sent to the courier). NEVER logs PII.
 */
@Injectable({ providedIn: 'root' })
export class FavoritosService {
  private readonly http = inject(HttpClient);
  private readonly base = '/v1/merchants/dispatch';

  listFavorites(): Promise<FavoriteRow[]> {
    return firstValueFrom(this.http.get<FavoriteRow[]>(`${this.base}/favorites`));
  }

  addFavorite(courierId: number): Promise<FavoriteRow> {
    return firstValueFrom(
      this.http.post<FavoriteRow>(`${this.base}/favorites`, { courier_id: courierId }),
    );
  }

  reorderFavorites(courierIds: number[]): Promise<void> {
    return firstValueFrom(
      this.http.put<void>(`${this.base}/favorites/reorder`, { courier_ids: courierIds }),
    );
  }

  removeFavorite(courierId: number): Promise<void> {
    return firstValueFrom(this.http.delete<void>(`${this.base}/favorites/${courierId}`));
  }

  listBlocks(): Promise<BlockedRow[]> {
    return firstValueFrom(this.http.get<BlockedRow[]>(`${this.base}/blocks`));
  }

  removeBlock(courierId: number): Promise<void> {
    return firstValueFrom(this.http.delete<void>(`${this.base}/blocks/${courierId}`));
  }
}
