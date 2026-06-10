"""Image reprocessing: validate → resize → WebP → strip EXIF → SHA-256 (T-03).

The server NEVER serves the raw uploaded byte. After download it: validates by
magic bytes, opens with Pillow (capped by MAX_IMAGE_PIXELS — anti
decompression-bomb), converts to RGB (drops alien channels/metadata), resizes the
longest side to ≤1920, and re-encodes to WebP WITHOUT passing `exif=` — which
produces a derivative with NO EXIF at all (full GPS/serial strip — TH-exif/LGPD).
The SHA-256 returned is the hash of the DERIVATIVE: the anti-tamper source of
truth (TH-07).
"""

from __future__ import annotations

import hashlib
import io

from PIL import Image

from app.couriers.constants import (
    MAX_DIMENSION_PX,
    MAX_IMAGE_PIXELS,
    WEBP_QUALITY,
)
from app.media.validation import UnsupportedMediaError, sniff_content_type

# Anti decompression-bomb (DoS): Pillow raises/​warns above this pixel count.
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def reprocess_to_webp(data: bytes) -> tuple[bytes, str]:
    """Validate + reprocess raw image bytes → (webp_bytes, sha256_hex).

    Raises UnsupportedMediaError if the bytes are not an allowed image family
    (magic-byte check — the declared content-type is ignored). The returned
    SHA-256 is over the DERIVATIVE (TH-07).
    """
    if sniff_content_type(data) is None:
        raise UnsupportedMediaError()

    try:
        with Image.open(io.BytesIO(data)) as im:
            # Decompression-bomb guard fires inside load(); convert drops EXIF
            # carriers, alpha and alien channels.
            im = im.convert("RGB")
            im.thumbnail((MAX_DIMENSION_PX, MAX_DIMENSION_PX))  # keeps aspect
            out = io.BytesIO()
            # NO exif= kwarg → the WebP derivative carries no EXIF (full strip).
            im.save(out, format="WEBP", quality=WEBP_QUALITY)
    except Image.DecompressionBombError:
        # A bomb is hostile input, not a server fault — treat as unsupported.
        raise UnsupportedMediaError() from None
    except (OSError, ValueError):
        # Corrupt / truncated / undecodable image.
        raise UnsupportedMediaError() from None

    derived = out.getvalue()
    return derived, hashlib.sha256(derived).hexdigest()


def has_exif(data: bytes) -> bool:
    """True if the image carries any EXIF (used by tests to assert a clean strip)."""
    with Image.open(io.BytesIO(data)) as im:
        return bool(im.getexif())
