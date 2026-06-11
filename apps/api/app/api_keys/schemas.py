"""API key admin contracts (Pydantic v2, extra='forbid' — A03).

The CREATE response carries the FULL secret `jxg_<key_id>_<secret>` ONCE (D-01);
every other surface (`ApiKeyOut`, list) carries only the public `key_id` + label
+ status — never the secret or its hash (TH-09).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Allowed scopes (narrow by default — the public endpoint only needs write).
ALLOWED_SCOPES = frozenset({"deliveries:write", "deliveries:read"})


class CreateApiKeyBody(BaseModel):
    """Create an API key for the area (screen 22)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["deliveries:write"])


class ApiKeyOut(BaseModel):
    """A key row WITHOUT the secret (list / detail). Never leaks the hash (TH-09)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key_id: str
    name: str
    scopes: str
    revoked: bool
    created_at: str | None = None
    last_used_at: str | None = None


class CreateApiKeyResponse(BaseModel):
    """The create response — the FULL secret is shown ONCE here (D-01)."""

    id: int
    key_id: str
    name: str
    scopes: str
    # `jxg_<key_id>_<secret>` — returned exactly once, never persisted in plaintext.
    secret: str


class ApiKeyListOut(BaseModel):
    """Paginated list of the area's keys (screen 22)."""

    items: list[ApiKeyOut]
    total: int
