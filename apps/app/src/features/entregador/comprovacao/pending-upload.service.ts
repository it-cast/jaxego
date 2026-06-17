import { Injectable, computed, signal } from '@angular/core';

/** A proof photo queued for upload when offline (D-04). */
export interface PendingUpload {
  deliveryId: number;
  proofKind: 'pickup' | 'delivery' | 'refusal';
  file: File;
  lat: number | null;
  lng: number | null;
}

/**
 * PendingUploadService — holds proof photos captured offline (D-04 / offline-first).
 *
 * A photo captured with no connection stays in this in-memory queue; the delivery is
 * NOT marked ENTREGUE until the upload + server validation succeed. On reconnect the
 * owning page drains the queue (`drain`) and only removes an item once its upload
 * resolves. The banner (jx-pending-upload-banner) reads `count`/`online`.
 *
 * In-memory for M1 (the proof flow is foreground); a durable IndexedDB queue is a
 * future upgrade if background capture is added (TD-020 territory).
 */
@Injectable({ providedIn: 'root' })
export class PendingUploadService {
  private readonly _queue = signal<PendingUpload[]>([]);
  private readonly _online = signal<boolean>(
    typeof navigator === 'undefined' || navigator.onLine,
  );

  /** Number of photos waiting to upload. */
  readonly count = computed(() => this._queue().length);
  /** Whether the device is currently online. */
  readonly online = this._online.asReadonly();

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this._online.set(true));
      window.addEventListener('offline', () => this._online.set(false));
    }
  }

  /** Queue a photo for later upload (offline) — returns its index. */
  enqueue(item: PendingUpload): void {
    this._queue.update((q) => [...q, item]);
  }

  /** Drain the queue with an uploader; an item is removed only on success. */
  async drain(upload: (item: PendingUpload) => Promise<boolean>): Promise<void> {
    if (!this._online()) return;
    const pending = [...this._queue()];
    for (const item of pending) {
      const ok = await upload(item);
      if (ok) {
        this._queue.update((q) => q.filter((x) => x !== item));
      } else {
        // Stop on the first failure — keep the rest queued (retry next reconnect).
        break;
      }
    }
  }

  /** Whether a given delivery still has a photo pending (UI must NOT show ENTREGUE). */
  hasPending(deliveryId: number): boolean {
    return this._queue().some((x) => x.deliveryId === deliveryId);
  }
}
