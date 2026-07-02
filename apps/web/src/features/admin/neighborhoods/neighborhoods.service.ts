import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface Neighborhood {
  id: number;
  area_id: number;
  name: string;
  is_informal: boolean;
}

export interface NeighborhoodCreate {
  name: string;
  is_informal?: boolean;
}

@Injectable({ providedIn: 'root' })
export class AdminNeighborhoodsService {
  private readonly http = inject(HttpClient);

  async list(): Promise<Neighborhood[]> {
    return firstValueFrom(this.http.get<Neighborhood[]>('/v1/neighborhoods'));
  }

  async create(body: NeighborhoodCreate): Promise<Neighborhood> {
    return firstValueFrom(this.http.post<Neighborhood>('/v1/neighborhoods', body));
  }

  async update(id: number, body: Partial<NeighborhoodCreate>): Promise<Neighborhood> {
    return firstValueFrom(this.http.patch<Neighborhood>(`/v1/neighborhoods/${id}`, body));
  }

  async remove(id: number): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`/v1/neighborhoods/${id}`));
  }
}
