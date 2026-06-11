"""Safe2Pay payment core (Phase 10 — F-03/F-07, REQ-010/011/019/029/034/036).

Everything Safe2Pay lives behind `PaymentPort` (a `typing.Protocol`, ADR-009 v2 /
D-09): an httpx impl (`Safe2PayHttpAdapter`) and a deterministic `PaymentStubAdapter`.
The service depends on the Protocol, never on a concrete impl — the test suite and
local dev wire the Stub (NEVER touch the network nor Safe2Pay sandbox). Money is
integer CENTS everywhere; every charge write is idempotent; card/CVV/token NEVER
appear in plaintext, in a log, or at rest (token at rest is AES-256-GCM).

Contract assumptions (split shape, webhook HMAC, refund endpoints, subaccount API)
are `[ASSUMIDO]` (DEC-003) and isolated in the adapter — confirmed at T-13 against
the real Safe2Pay contract; an ADR then supersedes DEC-003.
"""
