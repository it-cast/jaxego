import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faBoxOpen } from '@fortawesome/free-solid-svg-icons';
import { PageHeaderComponent, MoneyComponent } from '@jaxego/shared/components';
import { deliveryStateLabel } from '@jaxego/shared/util/delivery-format';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';
import { CourierDelivery, CourierDeliveryListItem, EntregadorService } from './entregador.service';

@Component({
  selector: 'jx-entregador-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    PageHeaderComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingSkeletonComponent,
    MoneyComponent,
    FaIconComponent,
  ],
  template: `
    <ion-content>
      <jx-page-header title="Entregas" />

      <div class="jx-entregas">
        @if (loading()) {
          <jx-loading-skeleton />
        } @else if (error()) {
          <jx-error-state
            message="Nao foi possivel carregar suas entregas."
            (retry)="reload()"
          />
        } @else if (!items().length) {
          <jx-empty-state
            icon="📦"
            title="Nenhuma corrida ainda"
            message="Quando voce aceitar uma corrida, ela aparece aqui."
          />
        } @else {
          <div class="jx-entregas__filter">
            <label class="jx-entregas__filter-label">
              <span>Filtrar por data</span>
              <input
                type="date"
                class="jx-entregas__filter-input"
                [value]="filterDate()"
                (input)="onFilterDate($event)"
              />
            </label>
            @if (filterDate()) {
              <button type="button" class="jx-entregas__filter-clear" (click)="clearFilter()">Limpar</button>
            }
          </div>
          <ul class="jx-entregas__list">
            @for (d of filtered(); track d.id) {
              <li
                class="jx-entregas__item"
                [class.jx-entregas__item--active]="isActive(d.state)"
                (click)="open(d)"
              >
                <div class="jx-entregas__icon">
                  <fa-icon [icon]="iconBox" aria-hidden="true" />
                </div>
                <div class="jx-entregas__info">
                  <strong class="jx-entregas__state">{{ stateLabel(d.state) }}</strong>
                  <p class="jx-entregas__meta">
                    {{ shortDate(d.created_at) }} · #{{ d.id }}
                  </p>
                </div>
                <div class="jx-entregas__value">
                  <jx-money [cents]="d.estimate_min_cents ?? d.fee_cents" />
                </div>
              </li>
            }
          </ul>
        }
      </div>

      @if (selectedDelivery(); as d) {
        <div class="jx-detail-backdrop" (click)="closeDetail()"></div>
        <div class="jx-detail-modal" role="dialog" aria-modal="true">
          <div class="jx-detail-modal__handle"></div>
          <h2 class="jx-detail-modal__title">Entrega #{{ d.id }}</h2>
          <span class="jx-detail-modal__status" [class.jx-detail-modal__status--done]="d.state === 'FINALIZADA'">
            {{ stateLabel(d.state) }}
          </span>

          <div class="jx-detail-modal__section">
            <span class="jx-detail-modal__label">Coleta</span>
            <p class="jx-detail-modal__value">{{ d.pickup_address }}</p>
            @if (d.pickup_neighborhood) {
              <p class="jx-detail-modal__sub">{{ d.pickup_neighborhood }}</p>
            }
          </div>

          @if (d.dropoff_address) {
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Destino</span>
              <p class="jx-detail-modal__value">
                {{ d.dropoff_address }}@if (d.dropoff_number) {, {{ d.dropoff_number }}}
              </p>
            </div>
          }

          @if (d.recipient_name) {
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Destinatario</span>
              <p class="jx-detail-modal__value">{{ d.recipient_name }}</p>
            </div>
          }

          @if (d.items_description) {
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Itens</span>
              <p class="jx-detail-modal__value">{{ d.items_description }} (x{{ d.items_quantity }})</p>
            </div>
          }

          @if (d.receipt_method) {
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Recebimento</span>
              <p class="jx-detail-modal__value">{{ receiptLabel(d.receipt_method) }}</p>
            </div>
          }

          @if (d.notes) {
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Observacoes</span>
              <p class="jx-detail-modal__value">{{ d.notes }}</p>
            </div>
          }

          <div class="jx-detail-modal__row">
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Valor</span>
              <p class="jx-detail-modal__value jx-detail-modal__value--mono">
                <jx-money [cents]="d.estimate_min_cents ?? d.fee_cents" />
              </p>
            </div>
            <div class="jx-detail-modal__section">
              <span class="jx-detail-modal__label">Data</span>
              <p class="jx-detail-modal__value">{{ shortDate(d.created_at) }}</p>
            </div>
          </div>

          <button type="button" class="jx-detail-modal__close" (click)="closeDetail()">Fechar</button>
        </div>
      }
    </ion-content>
  `,
  styles: [`
    .jx-entregas {
      padding: var(--jx-space-3) var(--jx-space-4);
    }
    .jx-entregas__filter {
      display: flex;
      align-items: flex-end;
      gap: var(--jx-space-2);
      margin-bottom: var(--jx-space-2);
    }
    .jx-entregas__filter-label {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: var(--jx-text-xs);
      color: var(--text-muted, #888);
      flex: 1;
    }
    .jx-entregas__filter-input {
      min-height: 40px;
      padding: 0 var(--jx-space-3);
      background: #fff;
      border: 1px solid var(--border, hsl(0 0% 90%));
      border-radius: var(--jx-radius-lg, 12px);
      color: var(--text);
      font-size: var(--jx-text-sm);
    }
    .jx-entregas__filter-clear {
      min-height: 40px;
      padding: 0 var(--jx-space-3);
      background: transparent;
      border: 1px solid var(--border, hsl(0 0% 90%));
      border-radius: var(--jx-radius-lg, 12px);
      color: var(--text-muted, #888);
      font-size: var(--jx-text-xs);
      cursor: pointer;
    }
    .jx-entregas__list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
    }
    .jx-entregas__item {
      display: flex;
      align-items: center;
      gap: var(--jx-space-3);
      padding: var(--jx-space-3) 0;
      border-bottom: 1px solid var(--border, hsl(0 0% 90%));
      cursor: pointer;
    }
    .jx-entregas__icon {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: var(--brand-wash, hsl(24 80% 95%));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: var(--brand, #e8722a);
      flex-shrink: 0;
    }
    .jx-entregas__info {
      flex: 1;
      min-width: 0;
    }
    .jx-entregas__state {
      display: block;
      font-size: var(--jx-text-sm);
      font-weight: 600;
      color: var(--text);
    }
    .jx-entregas__meta {
      margin: 0;
      font-size: var(--jx-text-xs);
      color: var(--text-muted, #888);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .jx-entregas__value {
      flex-shrink: 0;
    }

    /* Detail bottom-sheet */
    .jx-detail-backdrop {
      position: fixed; inset: 0; z-index: 60;
      background: rgba(0,0,0,0);
      animation: jx-fade-in 0.25s ease forwards;
    }
    @keyframes jx-fade-in {
      to { background: rgba(0,0,0,0.5); }
    }
    .jx-detail-modal {
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 70;
      background: #fff;
      border-radius: 20px 20px 0 0;
      padding: var(--jx-space-4);
      padding-bottom: max(var(--jx-space-5), env(safe-area-inset-bottom));
      display: flex; flex-direction: column; gap: var(--jx-space-3);
      max-height: 80vh; overflow-y: auto;
      animation: jx-slide-up 0.3s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes jx-slide-up {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
    .jx-detail-modal__handle {
      width: 40px; height: 4px; border-radius: 2px;
      background: var(--border, #ddd); align-self: center;
    }
    .jx-detail-modal__title {
      margin: 0; font-size: var(--jx-text-lg, 18px); font-weight: 700; text-align: center;
    }
    .jx-detail-modal__status {
      text-align: center; font-size: var(--jx-text-xs, 12px);
      font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;
      color: var(--brand, #e8722a);
    }
    .jx-detail-modal__status--done { color: var(--success, #2e7d32); }
    .jx-detail-modal__section {
      display: flex; flex-direction: column; gap: 2px;
    }
    .jx-detail-modal__label {
      font-size: var(--jx-text-2xs, 10px); font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.06em;
      color: var(--text-muted, #888);
    }
    .jx-detail-modal__value {
      margin: 0; font-size: var(--jx-text-sm, 14px); color: var(--text, #222);
    }
    .jx-detail-modal__value--mono { font-family: var(--jx-font-mono); }
    .jx-detail-modal__sub {
      margin: 0; font-size: var(--jx-text-xs, 12px); color: var(--text-muted, #888);
    }
    .jx-detail-modal__row {
      display: grid; grid-template-columns: 1fr 1fr; gap: var(--jx-space-3);
    }
    .jx-detail-modal__close {
      width: 100%; min-height: 50px;
      background: var(--brand, #e8722a); border: 0;
      border-radius: 999px; color: #fff;
      font-size: var(--jx-text-md, 16px); font-weight: 700;
      cursor: pointer;
    }
  `],
})
export class EntregadorEntregasPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly router = inject(Router);

  protected readonly items = signal<CourierDeliveryListItem[]>([]);
  protected readonly filtered = signal<CourierDeliveryListItem[]>([]);
  protected readonly filterDate = signal('');
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly selectedDelivery = signal<CourierDelivery | null>(null);

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) {
      this.loading.set(false);
      return;
    }
    this.loading.set(true);
    this.error.set(false);
    try {
      const page = await this.svc.listDeliveries(id);
      this.items.set(page.items);
      this.applyFilter();
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected isActive(state: string): boolean {
    return state === 'ACEITA' || state === 'COLETADA';
  }

  protected async open(d: CourierDeliveryListItem): Promise<void> {
    if (this.isActive(d.state)) {
      void this.router.navigate(['/entregador/entrega-ativa']);
      return;
    }
    const courierId = this.auth.me()?.courier_id;
    if (!courierId) return;
    try {
      const detail = await this.svc.getDelivery(courierId, d.id);
      this.selectedDelivery.set(detail);
    } catch { /* ignore */ }
  }

  protected closeDetail(): void {
    this.selectedDelivery.set(null);
  }

  protected receiptLabel(method: string): string {
    const map: Record<string, string> = {
      dinheiro: 'Dinheiro',
      maquina_loja: 'Maquina da loja',
      aplicativo: 'Aplicativo',
    };
    return map[method] ?? method;
  }

  protected readonly iconBox = faBoxOpen;
  protected readonly stateLabel = deliveryStateLabel;

  protected onFilterDate(e: Event): void {
    this.filterDate.set((e.target as HTMLInputElement).value);
    this.applyFilter();
  }

  protected clearFilter(): void {
    this.filterDate.set('');
    this.applyFilter();
  }

  private applyFilter(): void {
    const date = this.filterDate();
    if (!date) {
      this.filtered.set(this.items());
      return;
    }
    this.filtered.set(
      this.items().filter((d) => d.created_at?.startsWith(date)),
    );
  }

  protected shortDate(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' }) + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }
}
