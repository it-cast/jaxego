import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface CourierListItem {
  id: number;
  full_name: string;
  status: string;
  vehicle_type: string;
  is_online: boolean;
  documents: { id: number; kind: string; status: string; reject_reason: string | null }[];
}

export interface CourierDetail {
  id: number;
  full_name: string;
  cpf_masked: string;
  status: string;
  kyc_level: string;
  vehicle_type: string;
  vehicle_plate: string | null;
  created_at: string | null;
  documents: {
    id: number;
    kind: string;
    status: string;
    reject_reason: string | null;
    reject_detail: string | null;
    created_at: string | null;
  }[];
}

@Injectable({ providedIn: 'root' })
export class EquipeKycService {
  private readonly http = inject(HttpClient);
  private readonly base = '/v1/team-admin';

  async listCouriers(): Promise<CourierListItem[]> {
    return firstValueFrom(this.http.get<CourierListItem[]>(`${this.base}/couriers`));
  }

  async getCourier(courierId: number): Promise<CourierDetail | null> {
    try {
      return await firstValueFrom(this.http.get<CourierDetail>(`${this.base}/couriers/${courierId}`));
    } catch { return null; }
  }

  async viewUrl(courierId: number, documentId: number): Promise<string | null> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ url: string }>(`${this.base}/couriers/${courierId}/documents/${documentId}/view-url`)
      );
      return res.url;
    } catch { return null; }
  }

  async approve(courierId: number, documentId: number): Promise<boolean> {
    try {
      await firstValueFrom(this.http.post(`${this.base}/couriers/${courierId}/documents/${documentId}/approve`, {}));
      return true;
    } catch { return false; }
  }

  async reject(courierId: number, documentId: number, reason: string, detail?: string): Promise<boolean> {
    try {
      await firstValueFrom(this.http.post(`${this.base}/couriers/${courierId}/documents/${documentId}/reject`, { reason, detail }));
      return true;
    } catch { return false; }
  }
}
