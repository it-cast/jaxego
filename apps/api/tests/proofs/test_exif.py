"""extract_gps_from_raw reads GPS from the RAW EXIF (the opposite of the KYC strip).

A JPEG written WITH a GPS block yields the decoded (lat, lng) within rounding; a
plain JPEG (or a non-image) yields None. The decoded sign honours the S/W refs.
"""

from __future__ import annotations

import pytest
from app.proofs.exif import extract_gps_from_raw

from tests.proofs.conftest import (
    NEAR_LAT,
    NEAR_LNG,
    TARGET_LAT,
    TARGET_LNG,
    make_jpeg_no_gps,
    make_jpeg_with_gps,
)


def test_reads_gps_from_exif() -> None:
    raw = make_jpeg_with_gps(TARGET_LAT, TARGET_LNG)
    gps = extract_gps_from_raw(raw)
    assert gps is not None
    lat, lng = gps
    assert lat == pytest.approx(TARGET_LAT, abs=1e-3)
    assert lng == pytest.approx(TARGET_LNG, abs=1e-3)
    # Southern + Western hemisphere → both negative (ref handling).
    assert lat < 0 and lng < 0


def test_reads_gps_near_point() -> None:
    gps = extract_gps_from_raw(make_jpeg_with_gps(NEAR_LAT, NEAR_LNG))
    assert gps is not None
    assert gps[0] == pytest.approx(NEAR_LAT, abs=1e-3)


def test_no_gps_returns_none() -> None:
    assert extract_gps_from_raw(make_jpeg_no_gps()) is None


def test_non_image_returns_none() -> None:
    assert extract_gps_from_raw(b"not an image at all") is None
