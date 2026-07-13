import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface ViewUrlResponse {
  url: string;
  expires_in: number;
}

export interface ReviewResponse {
  document_id: number;
  status: 'approved' | 'rejected';
  courier_status: 'pending_kyc' | 'active' | 'suspended' | 'banned';
}

export interface CourierListItem {
  id: number;
  full_name: string;
  cpf_masked: string;
  status: string;
  kyc_level: string;
  created_at: string | null;
}

export interface CourierListOut {
  items: CourierListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CourierDocumentAdmin {
  id: number;
  kind: string;
  status: string;
  reject_reason: string | null;
  reject_detail: string | null;
  created_at: string | null;
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
  documents: CourierDocumentAdmin[];
}

/**
 * AdminKycService — consumes the area-admin KYC endpoints (T-11). The thumbnail
 * is a SHORT-LIVED presigned GET (≤180s); a failure surfaces as a retry that
 * regenerates the URL. Approve/reject post the item-a-item decision; the backend
 * audits and (when complete) activates the courier. No PII is ever logged.
 */
@Injectable({ providedIn: 'root' })
export class AdminKycService {
  private readonly http = inject(HttpClient);

  async getCourier(courierId: number): Promise<CourierDetail | null> {
    try {
      return await firstValueFrom(
        this.http.get<CourierDetail>(`/v1/admin/couriers/${courierId}`)
      );
    } catch {
      return null;
    }
  }

  /** List couriers in the admin's area (F2.0). `status` filters the KYC queue. */
  async listCouriers(status?: string): Promise<CourierListOut> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    try {
      return await firstValueFrom(
        this.http.get<CourierListOut>(`/v1/admin/couriers${qs}`)
      );
    } catch {
      return { items: [], total: 0, limit: 0, offset: 0 };
    }
  }

  async viewUrl(courierId: number, documentId: number): Promise<string | null> {
    try {
      const res = await firstValueFrom(
        this.http.get<ViewUrlResponse>(
          `/v1/admin/couriers/${courierId}/documents/${documentId}/view-url`
        )
      );
      return res.url;
    } catch {
      return null; // caller shows an error + retry (regenerates the URL)
    }
  }

  // A revisão de documentos (approve/reject) é do admin da EQUIPE — ver
  // features/equipe/equipe-kyc.service.ts. O admin da cidade só visualiza.
}
