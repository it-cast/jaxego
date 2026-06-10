"""Media pipeline security tests (T-03 / TH-02, TH-07, TH-exif).

Covers: magic-byte validation rejects a fake extension; the WebP derivative
carries NO EXIF (GPS strip); resize caps the longest side at 1920; the SHA-256 of
the derivative is stable; a decompression-bomb is rejected. NEVER touches B2 — the
pipeline is pure bytes.
"""

from __future__ import annotations

import io

import pytest
from app.media.reprocess import has_exif, reprocess_to_webp
from app.media.validation import (
    FileTooLargeError,
    UnsupportedMediaError,
    assert_size,
    sniff_content_type,
)
from PIL import Image


def _jpeg_with_exif(size: tuple[int, int] = (800, 600)) -> bytes:
    """A JPEG carrying EXIF (camera make/model) — proves the strip removes it."""
    im = Image.new("RGB", size, (120, 64, 32))
    exif = Image.Exif()
    exif[0x010F] = "TestCam Make"  # Make
    exif[0x0110] = "TestCam Model"  # Model
    exif[0x9003] = "2026:06:10 12:00:00"  # DateTimeOriginal
    out = io.BytesIO()
    im.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def _png(size: tuple[int, int] = (640, 480)) -> bytes:
    im = Image.new("RGB", size, (10, 20, 30))
    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()


def test_magic_bytes_accept_image_families() -> None:
    assert sniff_content_type(_jpeg_with_exif()) == "image/jpeg"
    assert sniff_content_type(_png()) == "image/png"
    webp = io.BytesIO()
    Image.new("RGB", (32, 32)).save(webp, format="WEBP")
    assert sniff_content_type(webp.getvalue()) == "image/webp"


def test_magic_bytes_reject_fake_extension() -> None:
    """A PDF/script renamed .jpg is rejected — extension is ignored, bytes decide."""
    fake = b"%PDF-1.7\n payload pretending to be a jpg"
    assert sniff_content_type(fake) is None
    with pytest.raises(UnsupportedMediaError):
        reprocess_to_webp(fake)


def test_exif_is_fully_stripped() -> None:
    """The reprocessed WebP carries NO EXIF (GPS/camera removed — TH-exif/LGPD)."""
    raw = _jpeg_with_exif()
    assert has_exif(raw) is True  # the source DID carry EXIF
    derived, _sha = reprocess_to_webp(raw)
    assert has_exif(derived) is False  # the derivative is clean


def test_resize_caps_longest_side() -> None:
    """A 4000px image is downscaled so the longest side is ≤1920."""
    raw = _png((4000, 2000))
    derived, _sha = reprocess_to_webp(raw)
    with Image.open(io.BytesIO(derived)) as im:
        assert max(im.size) <= 1920


def test_sha256_of_derivative_is_stable() -> None:
    """The same input yields the same derivative SHA-256 (anti-tamper, TH-07)."""
    raw = _png()
    _d1, sha1 = reprocess_to_webp(raw)
    _d2, sha2 = reprocess_to_webp(raw)
    assert sha1 == sha2
    assert len(sha1) == 64  # hex sha256


def test_decompression_bomb_rejected() -> None:
    """An image above MAX_IMAGE_PIXELS is rejected (anti-DoS — Pitfall 4)."""
    from app.couriers import constants

    # Build a PNG whose declared pixel count exceeds the ceiling. We patch the
    # ceiling low so the test image stays small but still trips the guard.
    original = Image.MAX_IMAGE_PIXELS
    import app.media.reprocess as reprocess_mod

    try:
        reprocess_mod.Image.MAX_IMAGE_PIXELS = 1000  # tiny ceiling for the test
        big = _png((100, 100))  # 10_000 px > 1000 ceiling
        with pytest.raises(UnsupportedMediaError):
            reprocess_to_webp(big)
    finally:
        reprocess_mod.Image.MAX_IMAGE_PIXELS = original
    assert constants.MAX_IMAGE_PIXELS == 40_000_000


def test_size_guard() -> None:
    """assert_size raises on bytes above the raw upload ceiling."""
    from app.couriers.constants import MAX_UPLOAD_BYTES

    assert_size(b"x" * 100)  # ok
    with pytest.raises(FileTooLargeError):
        assert_size(b"x" * (MAX_UPLOAD_BYTES + 1))
