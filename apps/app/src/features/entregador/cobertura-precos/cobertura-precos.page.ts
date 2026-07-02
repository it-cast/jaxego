import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faCircleExclamation, faXmark } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { PageHeaderComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import { CoberturaPrecosService, ZonaItem } from './cobertura-precos.service';
import { ZonaMapComponent } from './zona-map.component';

interface ZonaRow extends ZonaItem {
  editing: boolean;
  editValue: number | string;
  saving: boolean;
  saveOk: boolean;
}

@Component({
  selector: 'jx-cobertura-precos',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, IonContent, PageHeaderComponent, DotsLoaderComponent, FaIconComponent, ZonaMapComponent],
  templateUrl: './cobertura-precos.page.html',
  styleUrl: './cobertura-precos.page.scss',
})
export class CoberturaPrecosPage implements OnInit {
  private readonly svc = inject(CoberturaPrecosService);
  private readonly auth = inject(AuthService);

  private get courierId(): number {
    return this.auth.me()?.courier_id ?? 0;
  }

  protected readonly iconInfo = faCircleExclamation;
  protected readonly iconClose = faXmark;

  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly zones = signal<ZonaRow[]>([]);
  protected readonly mapZona = signal<ZonaRow | null>(null);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      const items = await this.svc.listZonas(this.courierId);
      this.zones.set(
        items.map(z => ({
          ...z,
          editing: false,
          editValue: z.courier_preco_cents !== null
            ? z.courier_preco_cents / 100
            : (z.team_preco_cents !== null ? z.team_preco_cents / 100 : 0),
          saving: false,
          saveOk: false,
        }))
      );
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected openMap(z: ZonaRow): void {
    this.mapZona.set(z);
  }

  protected closeMap(): void {
    this.mapZona.set(null);
  }

  protected startEdit(z: ZonaRow): void {
    this.zones.update(rows =>
      rows.map(r => ({
        ...r,
        editing: r.zona_id === z.zona_id,
        saveOk: false,
        editValue: r.zona_id === z.zona_id
          ? (r.courier_preco_cents !== null ? r.courier_preco_cents / 100 : (r.team_preco_cents !== null ? r.team_preco_cents / 100 : 0))
          : r.editValue,
      }))
    );
  }

  protected cancelEdit(z: ZonaRow): void {
    this.zones.update(rows =>
      rows.map(r => r.zona_id === z.zona_id ? { ...r, editing: false } : r)
    );
  }

  protected async save(z: ZonaRow): Promise<void> {
    const val = typeof z.editValue === 'number' ? z.editValue : parseFloat(String(z.editValue).replace(',', '.'));
    if (isNaN(val) || val < 0) return;
    const cents = Math.round(val * 100);

    this.zones.update(rows =>
      rows.map(r => r.zona_id === z.zona_id ? { ...r, saving: true } : r)
    );
    try {
      await this.svc.setZonaPreco(this.courierId, z.zona_id, cents);
      this.zones.update(rows =>
        rows.map(r =>
          r.zona_id === z.zona_id
            ? { ...r, saving: false, editing: false, saveOk: true, courier_preco_cents: cents }
            : r
        )
      );
    } catch {
      this.zones.update(rows =>
        rows.map(r => r.zona_id === z.zona_id ? { ...r, saving: false } : r)
      );
    }
  }

  protected formatBrl(cents: number): string {
    return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }
}
