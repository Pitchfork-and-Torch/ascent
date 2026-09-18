"""encode_pathhint: bool confidence must raise AscentCodecError (not serialize as 0/1)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ascent" / "_ref"))
sys.path.insert(0, str(ROOT))

from ascent_codec import AscentCodecError, encode_pathhint  # noqa: E402


def test_confidence_true_raises_codec_error() -> None:
    try:
        encode_pathhint(confidence=True, freeze_ms=100, ttl_ms=100)  # type: ignore[arg-type]
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "confidence" in str(exc).lower()


def test_confidence_false_raises_codec_error() -> None:
    try:
        encode_pathhint(confidence=False, freeze_ms=100, ttl_ms=100)  # type: ignore[arg-type]
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "confidence" in str(exc).lower()


def test_confidence_half_still_encodes() -> None:
    wire = encode_pathhint(confidence=0.5, freeze_ms=100, ttl_ms=100)
    assert isinstance(wire, (bytes, bytearray)) and len(wire) > 0


if __name__ == "__main__":
    test_confidence_true_raises_codec_error()
    test_confidence_false_raises_codec_error()
    test_confidence_half_still_encodes()
    print("PASS")
