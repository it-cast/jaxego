import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface TeamZonaItem {
  zona_id: number;
  zona_nome: string;
  preco_minimo_cents: number | null;
}

@Injectable({ providedIn: 'root' })
export class EquipeZonasService {
  private readonly http = inject(HttpClient);
  private readonly base = '/v1/team-admin';

  async listZonas(): Promise<TeamZonaItem[]> {
    return firstValueFrom(this.http.get<TeamZonaItem[]>(`${this.base}/zonas`));
  }

  async setPreco(zonaId: number, precoCents: number): Promise<void> {
    await firstValueFrom(
      this.http.put(`${this.base}/zonas/${zonaId}`, { preco_minimo_cents: precoCents })
    );
  }
}
