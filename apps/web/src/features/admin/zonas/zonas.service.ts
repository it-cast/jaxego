import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface Zona {
  id: number;
  area_id: number;
  name: string;
  boundary: object | null;
  created_at: string;
}

export interface ZonaCreate {
  name: string;
  boundary?: object | null;
}

export interface ZonaUpdate {
  name?: string;
  boundary?: object | null;
}

@Injectable({ providedIn: 'root' })
export class AdminZonasService {
  private readonly http = inject(HttpClient);

  async list(): Promise<Zona[]> {
    return firstValueFrom(this.http.get<Zona[]>('/v1/admin/area/zonas'));
  }

  async create(body: ZonaCreate): Promise<Zona> {
    return firstValueFrom(this.http.post<Zona>('/v1/admin/area/zonas', body));
  }

  async update(id: number, body: ZonaUpdate): Promise<Zona> {
    return firstValueFrom(this.http.patch<Zona>(`/v1/admin/area/zonas/${id}`, body));
  }

  async remove(id: number): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`/v1/admin/area/zonas/${id}`));
  }
}
