"""ASCENT wire standard - installable Python package.

Vendors the reference modules from ``ref/`` (monorepo) or ``ascent/_ref/`` (wheel).
"""
from __future__ import annotations

import sys
from pathlib import Path

__version__ = "2.0.2"


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
    cont_byte,
    cont_val,
    decode_stream,
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
    "encode_p9",
    "decode_p9",
    "strip_to_earth",
    "AscentDError",
]
