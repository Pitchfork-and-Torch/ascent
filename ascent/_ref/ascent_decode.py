#!/usr/bin/env python3
# ASCENT 1.0 draft - tiny reference decoder (Earth profile subset)
# Decodes: P0 text, greppable ASCENT/ magic, agent frames (9A..9B + C1),
# multimodal markers (9D 4D), crypto markers (9C 4B), DEF (C0), ASCENT-V.
# Shared logic lives in ascent_codec.py. ASCII hyphens only. No network I/O.

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ascent_codec import (
    HELLO_UNIVERSE_HEX,
    OPCODE,
    MM_KIND,
    HASH_ALG,
    HASH_LEN,
    AscentCodecError,
    decode_stream as codec_decode_stream,
    decode_agent as codec_decode_agent,
    decode_mm as codec_decode_mm,
    decode_crypto as codec_decode_crypto,
    decode_def as codec_decode_def,
    decode_ascent_v_at,
    events_to_jsonable as codec_events_to_jsonable,
    hello_universe_bytes,
    unescape_agent_args,
    parse_role_or_name,
    Cont,
    cont_byte,
    cont_val,
    encode_text,
    encode_scalar,
    encode_text_ascent7,
)

# Back-compat alias
SPEC_HELLO_HEX = HELLO_UNIVERSE_HEX
AscentDecodeError = AscentCodecError


@dataclass
class Event:
    kind: str
    detail: dict


def _dict_to_event(d: dict) -> Event:
    """Convert codec event dict to Event; keep kind authoritative."""
    kind = d.get("kind", "unknown")
    detail = {k: v for k, v in d.items() if k != "kind"}
    # Never allow detail to reintroduce kind as a wire number
    detail.pop("kind", None)
    return Event(kind, detail)


def decode_agent(body: bytes, start: int) -> Tuple[Event, int]:
    d, i = codec_decode_agent(body, start)
    return _dict_to_event(d), i


def decode_mm(body: bytes, start: int) -> Tuple[Event, int]:
    """Wire kind is mm_kind / kind_name; Event.kind stays 'multimodal'."""
    d, i = codec_decode_mm(body, start)
    return _dict_to_event(d), i


def decode_crypto(body: bytes, start: int) -> Tuple[Event, int]:
    d, i = codec_decode_crypto(body, start)
    return _dict_to_event(d), i


def decode_def(body: bytes, start: int) -> Tuple[Event, int]:
    d, i = codec_decode_def(body, start)
    return _dict_to_event(d), i


def decode_stream(data: bytes) -> List[Event]:
    """Decode stream; returns list of Event (kind never overwritten by wire fields)."""
    return [_dict_to_event(d) for d in codec_decode_stream(data)]


def events_to_jsonable(events: List[Event]) -> List[dict]:
    """JSON rows with kind first; detail never overwrites kind."""
    return codec_events_to_jsonable(events)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="ASCENT tiny reference decoder")
    p.add_argument("path", nargs="?", help="file to decode (raw bytes)")
    p.add_argument("--hello", action="store_true", help="decode built-in Hello Universe")
    p.add_argument("--self-test", action="store_true", help="verify builder matches SPEC hex")
    p.add_argument("--json", action="store_true", help="emit JSON events")
    args = p.parse_args(argv)

    if args.self_test:
        built = hello_universe_bytes()
        expected = bytes.fromhex(SPEC_HELLO_HEX)
        ok = built == expected
        print(f"builder_len={len(built)} spec_len={len(expected)} match={ok}")
        if not ok:
            print("builder:", built.hex())
            print("spec:   ", expected.hex())
            return 1
        events = decode_stream(expected)
        print(f"events={len(events)}")
        for e in events:
            print(f"  - {e.kind}: {e.detail}")
        texts = [e for e in events if e.kind == "text"]
        agents = [e for e in events if e.kind == "agent"]
        mms = [e for e in events if e.kind == "multimodal"]
        text_blob = " ".join(
            e.detail.get("text") or e.detail.get("ascii", "") for e in texts
        )
        assert "Hello, Universe" in text_blob
        assert agents and agents[0].detail.get("name") == "guide"
        assert mms and mms[0].detail.get("kind_name") == "REF"
        assert mms[0].kind == "multimodal"
        assert mms[0].detail.get("mm_kind") == 1
        # kind must not be overwritten by wire number in JSON flatten
        j = events_to_jsonable(mms)
        assert j[0]["kind"] == "multimodal"
        assert j[0].get("mm_kind") == 1
        print("SELF-TEST PASS")
        return 0

    if args.hello:
        data = hello_universe_bytes()
    elif args.path:
        data = Path(args.path).read_bytes()
    else:
        p.print_help()
        return 2

    try:
        events = decode_stream(data)
    except AscentDecodeError as ex:
        print(f"DECODE ERROR: {ex}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(events_to_jsonable(events), indent=2))
    else:
        for e in events:
            if e.kind == "text":
                t = e.detail.get("text") or e.detail.get("ascii", "")
                print(f"[TEXT] {t!r}")
            elif e.kind == "agent":
                print(
                    f"[AGENT] {e.detail['opcode_name']} "
                    f"name={e.detail.get('name', '')!r} flags={e.detail['flags']}"
                )
            elif e.kind == "multimodal":
                print(
                    f"[MM] {e.detail.get('kind_name', '?')} codec={e.detail.get('codec')} "
                    f"hash={str(e.detail.get('hash_hex', ''))[:16]}... "
                    f"ref={e.detail.get('ref', '')!r}"
                )
            else:
                print(f"[{e.kind.upper()}] {e.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
