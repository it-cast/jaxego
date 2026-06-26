import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faUsers, faCircleCheck, faTruckFast, faUserClock } from '@fortawesome/free-solid-svg-icons';

interface DashboardData {
  team_name: string;
  total_couriers: number;
  online_couriers: number;
  pending_kyc: number;
  deliveries_today: number;
  finalized_today: number;
}

@Component({
  selector: 'jx-equipe-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FaIconComponent],
  template: `
    @if (data(); as d) {
      <h1 class="jx-eq-dash__title">{{ d.team_name }}</h1>
      <div class="jx-eq-dash__grid">
        <div class="jx-eq-dash__card">
          <fa-icon [icon]="iconUsers" class="jx-eq-dash__icon" aria-hidden="true" />
          <span class="jx-eq-dash__value">{{ d.total_couriers }}</span>
          <span class="jx-eq-dash__label">Entregadores</span>
        </div>
        <div class="jx-eq-dash__card">
          <fa-icon [icon]="iconTruck" class="jx-eq-dash__icon jx-eq-dash__icon--green" aria-hidden="true" />
          <span class="jx-eq-dash__value">{{ d.online_couriers }}</span>
          <span class="jx-eq-dash__label">Online agora</span>
        </div>
        <div class="jx-eq-dash__card">
          <fa-icon [icon]="iconPending" class="jx-eq-dash__icon jx-eq-dash__icon--warn" aria-hidden="true" />
          <span class="jx-eq-dash__value">{{ d.pending_kyc }}</span>
          <span class="jx-eq-dash__label">Aguardando validação</span>
        </div>
        <div class="jx-eq-dash__card">
          <fa-icon [icon]="iconCheck" class="jx-eq-dash__icon jx-eq-dash__icon--brand" aria-hidden="true" />
          <span class="jx-eq-dash__value">{{ d.finalized_today }}</span>
          <span class="jx-eq-dash__label">Entregas finalizadas hoje</span>
        </div>
      </div>
    } @else {
      <p>Carregando...</p>
    }
  `,
  styles: [`
    .jx-eq-dash__title { margin: 0 0 var(--jx-space-4); font-family: var(--jx-font-display); font-size: 24px; font-weight: 800; color: var(--text); }
    .jx-eq-dash__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--jx-space-3); }
    .jx-eq-dash__card { background: var(--surface-elevated, #fff); border: 1px solid var(--border, #eee); border-radius: 12px; padding: var(--jx-space-4); display: flex; flex-direction: column; align-items: center; gap: var(--jx-space-2); }
    .jx-eq-dash__icon { font-size: 28px; color: var(--text-muted, #888); }
    .jx-eq-dash__icon--green { color: #2e7d32; }
    .jx-eq-dash__icon--warn { color: #e8722a; }
    .jx-eq-dash__icon--brand { color: var(--brand, #e8722a); }
    .jx-eq-dash__value { font-size: 32px; font-weight: 800; color: var(--text); }
    .jx-eq-dash__label { font-size: 13px; color: var(--text-muted, #888); text-align: center; }
  `],
})
export class EquipeDashboardPage implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly data = signal<DashboardData | null>(null);
  protected readonly iconUsers = faUsers;
  protected readonly iconTruck = faTruckFast;
  protected readonly iconPending = faUserClock;
  protected readonly iconCheck = faCircleCheck;

  async ngOnInit(): Promise<void> {
    const res = await firstValueFrom(this.http.get<DashboardData>('/v1/team-admin/dashboard'));
    this.data.set(res);
  }
}
