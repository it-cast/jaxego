import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '../../../shared/components/data-table/data-table.component';
import { NeighborhoodRowComponent } from './neighborhood-row.component';
import { ErrorStateComponent } from '../../../shared/state/error-state.component';
import {
  AdminNeighborhoodsService,
  Neighborhood,
} from './neighborhoods.service';

/**
 * Tela 21B — Catálogo de bairros (UI-SPEC §3.2–3.4, REQ-003).
 *
 * Lists the area's catalog over jx-data-table; adds a neighborhood by name with
 * an optional GeoJSON polygon (textarea mono, validated on blur — UX; the backend
 * is the authority). Removal blocked by active deliveries surfaces the backend's
 * 409 message (role=alert) citing the neighborhood. Empty = jx-empty-state with a
 * CTA. Tokens only; AA light+dark.
 */
@Component({
  selector: 'jx-neighborhoods-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    DataTableComponent,
    NeighborhoodRowComponent,
    ErrorStateComponent,
  ],
  templateUrl: './neighborhoods.page.html',
  styleUrl: './neighborhoods.page.scss',
})
export class NeighborhoodsPage implements OnInit {
  private readonly service = inject(AdminNeighborhoodsService);

  protected readonly columns: DataTableColumn[] = [
    { key: 'name', label: 'Nome' },
    { key: 'polygon', label: 'Polígono' },
    { key: 'actions', label: 'Ações', numeric: true },
  ];

  protected readonly rows = signal<Neighborhood[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');
  protected readonly removeError = signal<string | null>(null);

  // Add form.
  protected newName = '';
  protected geojsonText = '';
  protected readonly geojsonError = signal<string | null>(null);
  protected readonly adding = signal(false);

  protected readonly trackById = (item: unknown): number => (item as Neighborhood).id;

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  private async reload(): Promise<void> {
    this.tableState.set('loading');
    try {
      const list = await this.service.list();
      this.rows.set(list);
      this.tableState.set(list.length === 0 ? 'empty' : 'ready');
    } catch {
      this.tableState.set('error');
    }
  }

  /** Client-side GeoJSON syntax/range check (UX only — backend is authority). */
  protected validateGeojson(): unknown | null {
    this.geojsonError.set(null);
    const text = this.geojsonText.trim();
    if (text === '') {
      return null; // name-only is valid
    }
    let parsed: { type?: string; coordinates?: number[][][] };
    try {
      parsed = JSON.parse(text);
    } catch {
      this.geojsonError.set('GeoJSON inválido. Cole um Polygon com pares lng,lat.');
      return undefined;
    }
    if (parsed.type !== 'Polygon' || !Array.isArray(parsed.coordinates)) {
      this.geojsonError.set('GeoJSON inválido. Cole um Polygon com pares lng,lat.');
      return undefined;
    }
    for (const ring of parsed.coordinates) {
      for (const pair of ring) {
        const [lng, lat] = pair;
        if (lng < -180 || lng > 180) {
          this.geojsonError.set('Coordenada fora de faixa. Use lng entre −180 e 180.');
          return undefined;
        }
        if (lat < -90 || lat > 90) {
          this.geojsonError.set('Coordenada fora de faixa. Use lat entre −90 e 90.');
          return undefined;
        }
      }
    }
    return parsed;
  }

  async add(): Promise<void> {
    const name = this.newName.trim();
    if (name === '') {
      return;
    }
    const polygon = this.validateGeojson();
    if (polygon === undefined) {
      return; // geojsonError already set
    }
    this.adding.set(true);
    try {
      await this.service.create({
        name,
        polygon_geojson: polygon ?? undefined,
      });
      this.newName = '';
      this.geojsonText = '';
      await this.reload();
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 422) {
        this.geojsonError.set(
          err.error?.error?.message ??
            'GeoJSON inválido. Cole um Polygon com pares lng,lat.'
        );
      } else {
        this.geojsonError.set('Não conseguimos adicionar o bairro. Tente de novo.');
      }
    } finally {
      this.adding.set(false);
    }
  }

  async remove(id: number): Promise<void> {
    this.removeError.set(null);
    try {
      await this.service.remove(id);
      await this.reload();
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 409) {
        this.removeError.set(
          err.error?.error?.message ??
            'Não é possível remover: há entregas ativas nesse bairro. Arquive primeiro.'
        );
      } else {
        this.removeError.set('Não conseguimos remover o bairro. Tente de novo.');
      }
    }
  }
}
