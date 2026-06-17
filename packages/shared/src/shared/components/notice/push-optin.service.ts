import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * PushOptInService — contextual Web Push opt-in (push-notifications-architecture).
 *
 * The prompt is NEVER shown on first load: `shouldPrompt()` only returns true once a
 * contextual trigger has fired (e.g. after the first delivery) AND permission is still
 * 'default'. A denied permission degrades SILENTLY (the app falls back to email — no
 * nagging). On grant, the subscription is registered server-side (push_subscriptions).
 */
@Injectable({ providedIn: 'root' })
export class PushOptInService {
  private readonly http = inject(HttpClient);
  /** Set by a contextual trigger (e.g. first delivery completed). */
  private readonly _triggered = signal(false);

  markContextualTrigger(): void {
    this._triggered.set(true);
  }

  /** Only prompt after a trigger AND while permission is still undecided. */
  shouldPrompt(): boolean {
    if (!this._triggered()) return false;
    if (typeof Notification === 'undefined') return false;
    return Notification.permission === 'default';
  }

  /** Request permission + register the subscription. Degrades silently on denial. */
  async optIn(areaId: number, deliveryId: number | null): Promise<boolean> {
    if (typeof Notification === 'undefined' || !('serviceWorker' in navigator)) return false;
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') return false; // silent fallback (email)
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (!sub) return false;
      const json = sub.toJSON();
      await firstValueFrom(
        this.http.post('/v1/push-subscriptions', {
          area_id: areaId,
          delivery_id: deliveryId,
          endpoint: json.endpoint,
          keys: json.keys ?? {},
        }),
      );
      return true;
    } catch {
      return false; // never block on a subscription hiccup
    }
  }
}
