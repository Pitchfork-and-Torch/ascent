"""ASCENT wire standard - installable Python package.

Vendors the reference modules from ``ref/`` (monorepo) or ``ascent/_ref/`` (wheel).
"""
from __future__ import annotations

import sys
from pathlib import Path

__version__ = "2.1.0"


def _vendor_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "_ref",
        here.parent / "ref",
    ]
    for c in candidates:
        if (c / "ascent_codec.py").is_file():
            return c
    raise ImportError(
        "ASCENT reference modules not found. Expected ref/ascent_codec.py "
        "next to the package or ascent/_ref/ inside the wheel."
    )


_REF = _vendor_dir()
if str(_REF) not in sys.path:
    sys.path.insert(0, str(_REF))

from ascent_codec import (  # noqa: E402,F401
    AscentCodecError,
    Cont,
    HELLO_UNIVERSE_HEX,
    canonical_pathhint_bytes,
    cont_byte,
    cont_val,
    decode_skystate,
    decode_stream,
    encode_pathhint,
    encode_scalar,
    encode_text,
    encode_text_ascent7,
    events_to_jsonable,
    hello_universe_bytes,
)

try:
    from ascent_d import (  # noqa: E402,F401
        AscentDError,
        decode_p9,
        encode_p9,
        strip_to_earth,
    )
except Exception:  # reedsolo optional for minimal installs
    encode_p9 = None  # type: ignore
    decode_p9 = None  # type: ignore
    strip_to_earth = None  # type: ignore
    AscentDError = Exception  # type: ignore

try:
    from ascent_skypulse import (  # noqa: E402,F401
        PathHint,
        format_pathhint_meter,
        recommend_integrity,
        should_queue_session,
        wrap_pathhint_p9,
        evaluate_pathhint,
        pathhint_overhead_bytes,
    )
except Exception:  # pragma: no cover
    PathHint = None  # type: ignore
    recommend_integrity = None  # type: ignore
    should_queue_session = None  # type: ignore
    wrap_pathhint_p9 = None  # type: ignore
    format_pathhint_meter = None  # type: ignore
    evaluate_pathhint = None  # type: ignore
    pathhint_overhead_bytes = None  # type: ignore

__all__ = [
    "__version__",
    "AscentCodecError",
    "Cont",
    "HELLO_UNIVERSE_HEX",
    "cont_byte",
    "cont_val",
    "decode_stream",
    "encode_scalar",
    "encode_text",
    "encode_text_ascent7",
    "events_to_jsonable",
    "hello_universe_bytes",
    "encode_pathhint",
    "decode_skystate",
    "canonical_pathhint_bytes",
    "PathHint",
    "recommend_integrity",
    "should_queue_session",
    "evaluate_pathhint",
    "pathhint_overhead_bytes",
    "wrap_pathhint_p9",
    "format_pathhint_meter",
    "encode_p9",
    "decode_p9",
    "strip_to_earth",
    "AscentDError",
]
