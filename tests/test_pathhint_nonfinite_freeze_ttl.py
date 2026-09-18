"""encode_pathhint: non-finite freeze_ms/ttl_ms raise AscentCodecError (not ValueError)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ascent"))

from ascent import encode_pathhint, AscentCodecError  # noqa: E402


def test_nonfinite_freeze_ms_raises_codec_error() -> None:
    for v in (float("nan"), float("inf"), float("-inf")):
        try:
            encode_pathhint(freeze_ms=v)  # type: ignore[arg-type]
            raise AssertionError(f"expected AscentCodecError for freeze_ms={v}")
        except AscentCodecError as exc:
            assert "finite" in str(exc).lower() or "freeze" in str(exc).lower()
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"expected AscentCodecError, got {type(exc).__name__}: {exc}"
            ) from exc


def test_nonfinite_ttl_ms_raises_codec_error() -> None:
    for v in (float("nan"), float("inf")):
        try:
            encode_pathhint(ttl_ms=v)  # type: ignore[arg-type]
            raise AssertionError(f"expected AscentCodecError for ttl_ms={v}")
        except AscentCodecError:
            pass
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(
                f"expected AscentCodecError, got {type(exc).__name__}: {exc}"
            ) from exc


def test_nonfinite_freeze_until_ms_raises_codec_error() -> None:
    try:
        encode_pathhint(freeze_until_ms=float("nan"))  # type: ignore[arg-type]
        raise AssertionError("expected AscentCodecError for freeze_until_ms=nan")
    except AscentCodecError:
        pass
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"expected AscentCodecError, got {type(exc).__name__}: {exc}"
        ) from exc


def test_finite_freeze_still_encodes() -> None:
    wire = encode_pathhint(freeze_ms=1500, ttl_ms=3000, confidence=0.5)
    assert isinstance(wire, (bytes, bytearray)) and len(wire) > 0


if __name__ == "__main__":
    test_nonfinite_freeze_ms_raises_codec_error()
    test_nonfinite_ttl_ms_raises_codec_error()
    test_nonfinite_freeze_until_ms_raises_codec_error()
    test_finite_freeze_still_encodes()
    print("PASS test_pathhint_nonfinite_freeze_ttl")
