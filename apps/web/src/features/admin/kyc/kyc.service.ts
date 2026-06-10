import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { ReviewDecision } from './review-row.component';

export interface ViewUrlResponse {
  url: string;
  expires_in: number;
}

export interface ReviewResponse {
  document_id: number;
  status: 'approved' | 'rejected';
  courier_status: 'pending_kyc' | 'active' | 'suspended' | 'banned';
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

  async review(
    courierId: number,
    documentId: number,
    decision: ReviewDecision
  ): Promise<ReviewResponse | null> {
    try {
      return await firstValueFrom(
        this.http.patch<ReviewResponse>(
          `/v1/admin/couriers/${courierId}/documents/${documentId}`,
          decision
        )
      );
    } catch {
      return null; // caller rolls back the optimistic update + shows an error
    }
  }
}
