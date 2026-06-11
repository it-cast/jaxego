"""Proof endpoint contracts (Pydantic v2, extra='forbid' — A03).

The courier uploads the photo to B2 via a presigned PUT (reusing the StoragePort
contract), then POSTs the proof with the `storage_key` + an explicit client
`{lat,lng}` (A3 contract: client GPS is the primary path, EXIF is reinforcement).
The response carries the resulting state + the geofence verdict so the UI knows
whether to advance or to show the "fora do raio / low_confidence" path (E1).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProofPresignRequest(BaseModel):
    """Ask for a presigned PUT to upload a proof photo to B2."""

    model_config = ConfigDict(extra="forbid")
    content_type: str = Field(pattern=r"^image/(jpeg|png|webp)$")


class ProofPresignResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    storage_key: str
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_in: int


class SubmitProofRequest(BaseModel):
    """Submit a pickup/delivery photo proof after the B2 upload completed."""

    model_config = ConfigDict(extra="forbid")
    proof_kind: str = Field(pattern=r"^(pickup|delivery|refusal)$")
    storage_key: str = Field(min_length=1, max_length=255)
    # A3 contract: explicit client GPS is the primary evidence (EXIF = reinforcement).
    # Optional so the EXIF-only path still works; absent + no EXIF → gps_missing.
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    refusal_reason: str | None = Field(default=None, max_length=255)


class SubmitReferenceRequest(BaseModel):
    """Submit a reference number as proof of delivery (photo_reference method)."""

    model_config = ConfigDict(extra="forbid")
    reference_number: str = Field(min_length=1, max_length=64)


class ProofResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delivery_id: int
    state: str
    geofence_ok: bool
    low_confidence: bool
    # When the geofence fails and low_confidence is not yet reached, the UI shows
    # "fora do raio (tentativa N)"; failed_attempts lets it render the counter.
    failed_attempts: int = 0
