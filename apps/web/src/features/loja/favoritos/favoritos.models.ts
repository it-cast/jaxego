/** Favorites/blocks contracts (Phase 8 — RN-014). Mirrors the backend rows. */
export interface FavoriteRow {
  courier_id: number;
  priority: number;
  courier_name: string;
  avg_stars: number;
}

export interface BlockedRow {
  courier_id: number;
  courier_name: string;
  /** PRIVATE store-only reason — never exposed to the courier (RN-014). */
  reason: string | null;
  created_at: string | null;
}
