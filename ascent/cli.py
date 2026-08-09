#!/usr/bin/env python3
"""ASCENT CLI - encode / decode / self-test / hello."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    from ascent import (
        __version__,
        decode_stream,
        encode_text,
        events_to_jsonable,
        hello_universe_bytes,
        HELLO_UNIVERSE_HEX,
    )

    p = argparse.ArgumentParser(
        prog="ascent",
        description="ASCENT wire codec (ASCII-successor stream grammar)",
    )
    p.add_argument("--version", action="version", version=f"ascent-wire {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("encode", help="Encode text to hex or binary")
    e.add_argument("text", nargs="?", default=None, help="Text (or stdin)")
    e.add_argument("--header", action="store_true", help="Prefix ASCENT/1.0")
    e.add_argument("--role", default=None, help="Attach ROLE name")
    e.add_argument(
        "--mode",
        choices=("v", "bridge", "reject"),
        default="v",
        help="Non-ASCII mode",
    )
    e.add_argument("--bin", action="store_true", help="Write raw bytes to stdout")

    d = sub.add_parser("decode", help="Decode hex or .bin file")
    d.add_argument("input", nargs="?", default=None, help="Hex string or path")
    d.add_argument("--json", action="store_true", help="JSON events")
    d.add_argument("--file", action="store_true", help="Treat input as binary file path")

    sub.add_parser("hello", help="Print Hello, Universe sample hex")
    sub.add_parser("self-test", help="Decode Hello, Universe and check units")
    sub.add_parser("version", help="Print package version")

    args = p.parse_args(argv)

    if args.cmd == "version":
        print(f"ascent-wire {__version__}")
        return 0

    if args.cmd == "hello":
        print(HELLO_UNIVERSE_HEX)
        return 0

    if args.cmd == "self-test":
        data = hello_universe_bytes()
        events = decode_stream(data)
        kinds = [ev["kind"] for ev in events]
        assert kinds == ["text", "agent", "multimodal"], kinds
        assert data.hex().upper() == HELLO_UNIVERSE_HEX.upper()
        print("SELF-TEST PASS", len(data), "bytes", kinds)
        return 0

    if args.cmd == "encode":
        text = args.text
        if text is None:
            text = sys.stdin.read()
        wire = encode_text(
            text,
            header=args.header,
            role=args.role,
            non_ascii=args.mode,
        )
        if args.bin:
            sys.stdout.buffer.write(wire)
        else:
            print(wire.hex().upper())
        return 0

    if args.cmd == "decode":
        raw = args.input
        if raw is None:
            raw = sys.stdin.read().strip()
        if args.file or (raw and Path(raw).is_file()):
            data = Path(raw).read_bytes()
        else:
            clean = raw.replace(" ", "").replace("\n", "").replace("0x", "")
            data = bytes.fromhex(clean)
        events = decode_stream(data)
        if args.json:
            print(json.dumps(events_to_jsonable(events), indent=2))
        else:
            for ev in events:
                kind = ev.get("kind")
                if kind == "text":
                    print("TEXT:", repr(ev.get("text") or ev.get("ascii")))
                elif kind == "agent":
                    print(
                        "AGENT:",
                        ev.get("opcodeName") or ev.get("opcode_name") or ev.get("opcode"),
                        "name=",
                        ev.get("name"),
                    )
                elif kind == "multimodal":
                    print(
                        "MM:",
                        ev.get("kindName"),
                        ev.get("ref") or ev.get("text") or "",
                    )
                else:
                    print(kind.upper() + ":", ev)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
