"""Outbound webhooks (Phase 12 — REQ-043 / D-06/D-07/D-08).

An area configures ONE webhook endpoint (URL + secret + subscribed events). On a
delivery state change the `transition()` hook enqueues a `webhook_deliveries` row;
the arq job (T-09) signs the payload (HMAC-SHA256, Stripe scheme) and POSTs it with
an EXACT 8-step backoff, marking `failed` + alerting after the 8th attempt (TH-10).
The payload minimises PII (RN-013) — never the recipient phone, never the full
dropoff address before COLETADA.
"""
