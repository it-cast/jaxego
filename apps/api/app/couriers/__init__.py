"""Courier onboarding + KYC domain (F-02, Phase 5).

Two entities: `Courier` (area-scoped, state machine pending_kyc/active/
suspended/banned + mei_pending flag) and `CourierDocument` (per-item KYC status
with storage_key/sha256/expires_at). Documents live in a PRIVATE B2 bucket; the
bytes never transit the backend on upload (presigned PUT). See RESEARCH §
Architecture and the threat model in the PLAN.
"""
