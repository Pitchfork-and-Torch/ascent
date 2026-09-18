"""encode_pathhint: negative freeze_until_ms must raise AscentCodecError."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ascent import encode_pathhint, AscentCodecError  # noqa: E402


def test_negative_freeze_until_ms_raises_codec_error() -> None:
    for v in (-1, -100):
        try:
            encode_pathhint(freeze_until_ms=v)
            raise AssertionError(f"expected AscentCodecError for freeze_until_ms={v}")
        except AscentCodecError as exc:
            assert "freeze_ms" in str(exc) or "ttl_ms" in str(exc), exc
        except Exception as exc:  # pragma: no cover
            raise AssertionError(
                f"expected AscentCodecError, got {type(exc).__name__}: {exc}"
            ) from exc


def test_positive_freeze_until_ms_still_encodes() -> None:
    wire = encode_pathhint(freeze_until_ms=1500, confidence=0.5)
    assert isinstance(wire, (bytes, bytearray))
    assert len(wire) >= 4


if __name__ == "__main__":
    test_negative_freeze_until_ms_raises_codec_error()
    test_positive_freeze_until_ms_still_encodes()
    print("PASS test_freeze_until_ms_negative")
