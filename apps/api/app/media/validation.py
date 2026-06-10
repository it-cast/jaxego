"""Magic-byte sniffing + size validation (owasp upload / TH-02, A03).

The declared extension / content-type from the client is a HINT, never authority.
We sniff the first bytes against an allowlist of image families (jpeg/png/webp)
and reject anything else — this is what stops a polyglot or a `.jpg` that is
really a PDF/script. PDF is deliberately NOT in the allowlist in M1 (LOW-2 →
TD-016: antecedentes restricted to image until a scan pipeline exists).
"""

from __future__ import annotations

from app.core.exceptions import AppError
from app.couriers.constants import MAX_UPLOAD_BYTES

# Magic-byte prefixes → canonical content-type (allowlist). WebP is a RIFF
# container with "WEBP" at offset 8, so it needs a two-part check.
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_RIFF_MAGIC = b"RIFF"
_WEBP_TAG = b"WEBP"


class UnsupportedMediaError(AppError):
    """Uploaded bytes are not an allowed image family (magic-byte mismatch)."""

    status_code = 422
    code = "unsupported_media"

    def __init__(self) -> None:
        super().__init__(
            "Esse arquivo não é uma imagem válida. Tire uma foto ou escolha uma da galeria."
        )


class FileTooLargeError(AppError):
    """Uploaded bytes exceed the max raw size (Pitfall 2 / TH-02)."""

    status_code = 422
    code = "file_too_large"

    def __init__(self) -> None:
        super().__init__("A imagem é muito grande. Tente outra ou tire uma foto nova.")


def sniff_content_type(data: bytes) -> str | None:
    """Return the canonical content-type by MAGIC BYTES, or None if not allowed.

    The client's declared extension / content-type is ignored entirely — only the
    actual bytes decide (A03 / upload). PDF and every non-image family return None.
    """
    if data.startswith(_JPEG_MAGIC):
        return "image/jpeg"
    if data.startswith(_PNG_MAGIC):
        return "image/png"
    # WebP: "RIFF" .... "WEBP" (tag at offset 8).
    if data[:4] == _RIFF_MAGIC and data[8:12] == _WEBP_TAG:
        return "image/webp"
    return None


def assert_size(data: bytes) -> None:
    """Raise FileTooLargeError if the raw upload exceeds MAX_UPLOAD_BYTES."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError()
