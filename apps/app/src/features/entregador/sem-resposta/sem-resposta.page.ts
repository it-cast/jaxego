import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faBoxOpen, faCircle, faLocationDot } from '@fortawesome/free-solid-svg-icons';
import { PageHeaderComponent, MoneyComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import {
  EmptyStateComponent,
  ErrorStateComponent,
} from '@jaxego/shared/state';
import { PoolItemOut } from './pool.models';
import { PoolService } from './pool.service';

/**
 * Entregas sem resposta — pool de entregas que a cascata de despacho esgotou
 * (todo entregador elegível recusou ou deixou expirar até o limite). Qualquer
 * entregador elegível (mesma cobertura/equipe que a cascata aplicaria) pode
 * navegar aqui e se autoatribuir uma — primeiro a tocar "Aceitar" ganha
 * (mesma proteção de corrida do aceite de oferta normal, sem penalidade em
 * caso de perda de corrida).
 */
@Component({
  selector: 'jx-entregador-sem-resposta',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    PageHeaderComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    MoneyComponent,
    FaIconComponent,
    DotsLoaderComponent,
  ],
  template: `
    <ion-content>
      @if (loading()) {
        <jx-dots-loader />
      } @else {
        <jx-page-header title="Entregas sem resposta" backLink="/entregador/inicio" />

        @if (lostMessage()) {
          <div class="jx-pool__lost-banner" role="alert">
            {{ lostMessage() }}
          </div>
        }

        <div class="jx-pool">
          @if (error()) {
            <jx-error-state
              message="Não foi possível carregar a lista."
              (retry)="reload()"
            />
          } @else if (!items().length) {
            <jx-empty-state
              imgSrc="delivery-amico.svg"
              title="Nenhuma entrega sem resposta"
              message="Quando uma entrega ficar sem ninguém para aceitar, ela aparece aqui."
            />
          } @else {
            <ul class="jx-pool__list">
              @for (d of items(); track d.delivery_id) {
                <li class="jx-pool__card">
                  <div class="jx-pool__card-head">
                    <div class="jx-pool__card-icon">
                      <fa-icon [icon]="iconBox" aria-hidden="true" />
                    </div>
                    <span class="jx-pool__card-title">{{ d.loja_nome }}</span>
                    <span class="jx-pool__waiting">{{ waitingSince(d.created_at) }}</span>
                  </div>
                  <div class="jx-pool__timeline">
                    <div class="jx-pool__tl-step">
                      <fa-icon [icon]="iconCircle" class="jx-pool__tl-dot jx-pool__tl-dot--pickup" aria-hidden="true" />
                      <div>
                        <strong class="jx-pool__tl-label">{{ d.pickup_address }}</strong>
                        @if (d.pickup_neighborhood) {
                          <p class="jx-pool__tl-sub">{{ d.pickup_neighborhood }}</p>
                        }
                      </div>
                    </div>
                    <div class="jx-pool__tl-line"></div>
                    <div class="jx-pool__tl-step">
                      <fa-icon [icon]="iconPin" class="jx-pool__tl-dot jx-pool__tl-dot--drop" aria-hidden="true" />
                      <div>
                        <strong class="jx-pool__tl-label">{{ d.dropoff_address }}{{ d.dropoff_number ? ', ' + d.dropoff_number : '' }}</strong>
                        <p class="jx-pool__tl-sub">{{ d.dropoff_neighborhood }}{{ d.distance_m ? ' · ' + formatKm(d.distance_m) : '' }}</p>
                      </div>
                    </div>
                  </div>
                  <div class="jx-pool__card-footer">
                    <jx-money [cents]="d.value_cents ?? 0" />
                    <button
                      type="button"
                      class="jx-pool__accept-btn"
                      [disabled]="processingId() === d.delivery_id"
                      (click)="accept(d)"
                    >
                      {{ processingId() === d.delivery_id ? 'Aceitando...' : 'Aceitar' }}
                    </button>
                  </div>
                  @if (lostId() === d.delivery_id) {
                    <p class="jx-pool__lost">Essa entrega acabou de ser aceita por outro entregador.</p>
                  }
                </li>
              }
            </ul>
          }
        </div>
      }
    </ion-content>
  `,
  styles: [`
    .jx-pool { padding: var(--jx-space-3) var(--jx-space-4); }
    .jx-pool__list {
      list-style: none; margin: 0; padding: 0;
      display: flex; flex-direction: column; gap: var(--jx-space-3);
    }
    .jx-pool__card {
      background: #fff; border: 1px solid var(--border, #eee);
      border-radius: 16px; padding: var(--jx-space-3);
      display: flex; flex-direction: column; gap: var(--jx-space-3);
    }
    .jx-pool__card-head { display: flex; align-items: center; gap: var(--jx-space-2); }
    .jx-pool__card-icon {
      width: 40px; height: 40px; border-radius: 50%;
      background: var(--brand-wash, hsl(24 80% 95%));
      display: flex; align-items: center; justify-content: center;
      font-size: 16px; color: var(--brand, #e8722a); flex-shrink: 0;
    }
    .jx-pool__card-title { flex: 1; font-size: var(--jx-text-sm); font-weight: 600; color: var(--text); }
    .jx-pool__waiting {
      font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
      padding: 4px 10px; border-radius: 999px;
      background: hsl(40 80% 92%); color: hsl(40 80% 35%);
    }
    .jx-pool__timeline { display: flex; flex-direction: column; padding-left: var(--jx-space-2); }
    .jx-pool__tl-step { display: flex; align-items: flex-start; gap: var(--jx-space-2); }
    .jx-pool__tl-dot { font-size: 10px; margin-top: 4px; flex-shrink: 0; }
    .jx-pool__tl-dot--pickup { color: var(--brand, #e8722a); }
    .jx-pool__tl-dot--drop { color: hsl(0 70% 55%); }
    .jx-pool__tl-label { font-size: var(--jx-text-sm); color: var(--text); }
    .jx-pool__tl-sub { margin: 0; font-size: var(--jx-text-xs); color: var(--text-muted, #888); }
    .jx-pool__tl-line { width: 1px; height: 16px; background: var(--border, #ddd); margin-left: 4px; }
    .jx-pool__card-footer {
      display: flex; align-items: center; justify-content: space-between;
      padding-top: var(--jx-space-2); border-top: 1px solid var(--border, #f0f0f0);
    }
    .jx-pool__accept-btn {
      min-height: 40px; padding: 0 var(--jx-space-4);
      background: var(--brand, #e8722a); border: 0; border-radius: 999px;
      color: #fff; font-size: var(--jx-text-sm); font-weight: 700; cursor: pointer;
    }
    .jx-pool__accept-btn:disabled { opacity: 0.6; cursor: default; }
    .jx-pool__lost { margin: 0; font-size: var(--jx-text-xs); color: hsl(0 60% 45%); }
    .jx-pool__lost-banner {
      margin: var(--jx-space-3) var(--jx-space-4) 0;
      padding: var(--jx-space-3);
      background: hsl(0 70% 96%);
      border: 1px solid hsl(0 70% 80%);
      border-radius: 12px;
      font-size: var(--jx-text-sm);
      font-weight: 600;
      color: hsl(0 60% 40%);
    }
  `],
})
export class EntregadorSemRespostaPage implements OnInit {
  private readonly svc = inject(PoolService);
  private readonly router = inject(Router);

  protected readonly items = signal<PoolItemOut[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly processingId = signal<number | null>(null);
  protected readonly lostId = signal<number | null>(null);
  protected readonly lostMessage = signal<string | null>(null);

  private lostTimer: ReturnType<typeof setTimeout> | null = null;

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      this.items.set(await this.svc.list());
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected async accept(d: PoolItemOut): Promise<void> {
    this.processingId.set(d.delivery_id);
    this.lostId.set(null);
    const result = await this.svc.accept(d.delivery_id);
    this.processingId.set(null);
    if (result === 'won') {
      void this.router.navigate(['/entregador/entrega-ativa']);
      return;
    }
    if (result === 'lost') {
      this.lostId.set(d.delivery_id);
      this.lostMessage.set('Lamentamos, mas essa entrega já foi aceita por outro entregador.');
      if (this.lostTimer) clearTimeout(this.lostTimer);
      this.lostTimer = setTimeout(() => this.lostMessage.set(null), 6000);
    }
    // Either way the card is stale now — refresh the list.
    await this.reload();
  }

  protected readonly iconBox = faBoxOpen;
  protected readonly iconCircle = faCircle;
  protected readonly iconPin = faLocationDot;

  protected formatKm(m: number): string {
    return `~${(m / 1000).toFixed(1).replace('.', ',')} km`;
  }

  protected waitingSince(iso: string): string {
    const ms = Date.now() - new Date(iso).getTime();
    const minutes = Math.max(0, Math.floor(ms / 60000));
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    return `${hours} h`;
  }
}
