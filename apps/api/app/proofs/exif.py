"""Extract GPS from the RAW EXIF — the OPPOSITE of the KYC strip (Pitfall 1).

`media/reprocess.py` (Phase 5) deliberately DESTROYS EXIF (privacy). For proof of
delivery the GPS is the antifraud evidence, so it must be read from the ORIGINAL
byte BEFORE any reprocess. This module does exactly that and nothing else: it never
trusts the value (the geofence is the authority — RN-017 / TH-1), it just reads it.

`get_ifd(IFD.GPSInfo)` is the public Pillow ≥6 API (the old `_getexif()` is private
and deprecated — State of the Art). GPS is DMS rationals + N/S/E/W refs; the helper
converts to signed decimal degrees. Any malformed/absent EXIF → None (the caller
then relies on the client `{lat,lng}` or rejects with `gps_missing`).
"""

from __future__ import annotations

import io

from PIL import Image
from PIL.ExifTags import GPS, IFD


def _dms_to_deg(dms: tuple[float, float, float], ref: str) -> float:
    """Convert DMS rationals + hemisphere ref to signed decimal degrees."""
    deg, minutes, sec = (float(x) for x in dms)
    val = deg + minutes / 60 + sec / 3600
    return -val if ref in ("S", "W") else val


def extract_gps_from_raw(raw: bytes) -> tuple[float, float] | None:
    """Read (lat, lng) from the RAW EXIF, or None if absent/illegible.

    MUST be called BEFORE `reprocess_to_webp` (which strips EXIF). The value is
    EVIDENCE the geofence validates, NEVER authority (RN-017 / ADR-008).
    """
    try:
        with Image.open(io.BytesIO(raw)) as im:
            gps = im.getexif().get_ifd(IFD.GPSInfo)
    except (OSError, ValueError, SyntaxError):
        # Corrupt/truncated/undecodable — treat as "no GPS" (the caller decides).
        return None
    if not gps:
        return None
    lat = gps.get(GPS.GPSLatitude)
    lat_ref = gps.get(GPS.GPSLatitudeRef)
    lng = gps.get(GPS.GPSLongitude)
    lng_ref = gps.get(GPS.GPSLongitudeRef)
    if not (lat and lat_ref and lng and lng_ref):
        return None
    try:
        return _dms_to_deg(lat, lat_ref), _dms_to_deg(lng, lng_ref)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
