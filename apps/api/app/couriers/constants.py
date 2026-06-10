"""Numeric limits for the KYC document pipeline (T-03 / LOW-3 → derived here).

Every constant is FIXED with a documented derivation (RESEARCH Open Question 3 /
A4). These are the single source of truth consumed by the presign endpoints, the
reprocess worker and the validation module.
"""

from __future__ import annotations

# Presigned PUT window (seconds). 5 min: enough for a mobile capture + upload on
# a weak connection, short enough that a leaked URL expires fast (TH-06).
PRESIGN_PUT_EXPIRES_S = 300

# Presigned GET window for the admin viewer (seconds). 3 min: one review pass;
# a leaked thumbnail URL expires before it can be widely shared (TH-01/TH-06).
PRESIGN_GET_EXPIRES_S = 180

# Max raw upload size (bytes) pre-compression. 10 MB: a modern phone photo is
# ~3-8 MB; this leaves margin without inviting multi-GB abuse (TH-02 / Pitfall 2).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# Max derivative dimension (px, longest side). 1920: a document stays legible at
# 1080p-class resolution without the bandwidth cost of full-res (integracoes §7).
MAX_DIMENSION_PX = 1920

# Anti decompression-bomb ceiling (total pixels). 40M ≈ 1920*1080*~19, far above
# any legitimate document yet well below a bomb (Pitfall 4 / TH-02).
MAX_IMAGE_PIXELS = 40_000_000

# WebP re-encode quality. 80: visually lossless for documents, good compression.
WEBP_QUALITY = 80

# Allowed magic-byte families. Antecedentes is restricted to IMAGE in M1
# (LOW-2 → TD-016: PDF deferred until a scan pipeline exists). PDF NOT allowed.
ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/png", "image/webp")
