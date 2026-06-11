"""Public integrator API (Phase 12 — REQ-041/042, F-04).

`POST /v1/deliveries` authenticated by an area API key, idempotent (24h snapshot),
rate-limited per key (429 + Retry-After). It resolves the target store within the
key's area (404 cross-area — TH-03) and calls the SAME `create_delivery` service
as the internal router — zero state-machine duplication.
"""
