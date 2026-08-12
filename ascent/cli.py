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
        canonical_pathhint_bytes,
        decode_stream,
        encode_pathhint,
        encode_text,
        events_to_jsonable,
        hello_universe_bytes,
        HELLO_UNIVERSE_HEX,
        recommend_integrity,
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
    ph = sub.add_parser("pathhint", help="Encode/decode a SkyPulse PATHHINT unit")
    ph.add_argument("--decode", metavar="HEX", help="Decode PATHHINT hex")
    ph.add_argument("--crc", action="store_true", help="Attach light CRC (LEO-IP)")
    ph.add_argument("--path-id", type=int, default=66)
    ph.add_argument("--cap-bps", type=int, default=50_000_000)
    ph.add_argument("--freeze-ms", type=int, default=15000)
    ph.add_argument("--confidence", type=float, default=0.8)
    ph.add_argument("--ttl-ms", type=int, default=30000)
    ph.add_argument("--obstruction", type=float, default=0.2)
    ph.add_argument("--elev", type=float, default=42.0)
    ph.add_argument("--profile", default="ASCENT-E-LEO", help="Integrity profile note")

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
        hint = canonical_pathhint_bytes()
        hev = decode_stream(hint)
        assert hev[0]["kind"] == "pathhint" and hev[0]["applied"] is True
        print("SELF-TEST PASS", len(data), "bytes", kinds, "+ PATHHINT", len(hint), "B")
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
                elif kind == "pathhint":
                    print(
                        "PATHHINT:",
                        "applied=" + str(ev.get("applied")),
                        "path_id=" + str(ev.get("path_id")),
                        "cap_bps=" + str(ev.get("next_capacity_bps")),
                        "reason=" + str(ev.get("reason") or ""),
                    )
                else:
                    print(kind.upper() + ":", ev)
        return 0

    if args.cmd == "pathhint":
        pol = recommend_integrity(args.profile) if recommend_integrity else {}
        if args.decode:
            clean = args.decode.replace(" ", "").replace("\n", "").replace("0x", "")
            events = decode_stream(bytes.fromhex(clean))
            print(json.dumps(events_to_jsonable(events), indent=2))
            return 0
        use_crc = args.crc or (pol.get("use_pathhint_crc") if pol else False)
        wire = encode_pathhint(
            path_id=args.path_id,
            next_capacity_bps=args.cap_bps,
            freeze_ms=args.freeze_ms,
            confidence=args.confidence,
            ttl_ms=args.ttl_ms,
            obstruction=args.obstruction,
            elev_deg=args.elev,
            crc=bool(use_crc),
        )
        print(wire.hex().upper())
        if pol:
            print(
                "# profile",
                pol.get("profile"),
                "mode",
                pol.get("mode"),
                "wrap_p9",
                pol.get("wrap_p9"),
                file=sys.stderr,
            )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
