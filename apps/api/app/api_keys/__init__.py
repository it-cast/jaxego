"""Public API authentication + idempotency (Phase 12).

Holds the area-scoped API keys (argon2id hash, never plaintext), the 24h
idempotency snapshot store, and the dependency that resolves a Bearer/X-API-Key
header to an `(area_id, scopes)` scope (mirroring `MerchantScopeDep`).
"""
