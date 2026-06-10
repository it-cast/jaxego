"""Auth API contracts (Pydantic v2, extra='forbid' — anti mass-assignment, A03).

`TokenPair` defines the shape the Phase 3 UI consumes. Password minimum is 10
chars with no arbitrary composition rules (NIST 800-63B / A07).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginBody(BaseModel):
    """Login request. `totp` is optional (required only when enrolled)."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    totp: str | None = Field(default=None, max_length=10)


class TokenPair(BaseModel):
    """Issued tokens. Access in body; refresh also set as httpOnly cookie (web)."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime, seconds


class RefreshBody(BaseModel):
    """Refresh request (raw opaque token from body or cookie)."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str | None = Field(default=None, max_length=256)


class LogoutBody(BaseModel):
    """Logout request — revokes the presented refresh token."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str | None = Field(default=None, max_length=256)


class TotpEnrollResponse(BaseModel):
    """One-time enrolment payload. The secret/URI is shown ONCE, never re-fetched."""

    model_config = ConfigDict(extra="forbid")

    provisioning_uri: str
    secret: str


class TotpVerifyBody(BaseModel):
    """Confirm TOTP enrolment with a code from the authenticator app."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=6, max_length=10)
