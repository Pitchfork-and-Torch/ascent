"""encode_pathhint: non-finite next_capacity raises AscentCodecError (not ValueError)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ascent" / "_ref"))
sys.path.insert(0, str(ROOT))

from ascent_codec import AscentCodecError, encode_pathhint  # noqa: E402


def test_next_capacity_bps_nan_raises_codec_error() -> None:
    try:
        encode_pathhint(next_capacity_bps=float("nan"))
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "next_capacity" in str(exc).lower() or "finite" in str(exc).lower()


def test_next_capacity_bps_inf_raises_codec_error() -> None:
    try:
        encode_pathhint(next_capacity_bps=float("inf"))
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "finite" in str(exc).lower() or "next_capacity" in str(exc).lower()


def test_next_capacity_kbps_neginf_raises_codec_error() -> None:
    try:
        encode_pathhint(next_capacity_kbps=float("-inf"))
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "finite" in str(exc).lower() or "next_capacity" in str(exc).lower()


def test_path_id_float_raises_codec_error() -> None:
    try:
        encode_pathhint(path_id=1.5)  # type: ignore[arg-type]
        assert False, "expected AscentCodecError"
    except AscentCodecError as exc:
        assert "path_id" in str(exc).lower()


def test_finite_capacity_still_encodes() -> None:
    wire = encode_pathhint(next_capacity_bps=50_000_000, freeze_ms=1000, ttl_ms=5000)
    assert isinstance(wire, (bytes, bytearray)) and len(wire) > 0
