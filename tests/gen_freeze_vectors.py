#!/usr/bin/env python3
"""Regenerate tests/freeze_vectors.json from Python reference."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ref"))
from ascent_codec import encode_text, decode_stream, HELLO_UNIVERSE_HEX
from ascent_d import encode_p9, CRC_NAME

def agent(op, name=None, payload=None, flags=0):
    out = bytearray([0x9A, 0xC1, 0x01])
    out += struct.pack(">H", op)
    out.append(flags)
    if name is not None:
        nb = name.encode("ascii")
        args = bytes([len(nb)]) + nb
    elif payload is not None:
        args = payload.encode("utf-8") if isinstance(payload, str) else payload
    else:
        args = b""
    out += struct.pack(">H", len(args))
    out += args
    out.append(0x9B)
    return bytes(out)

ROLE, TOOL, THINK, STOP, SAFETY = 2, 3, 4, 1, 7
vectors = {
    "crc_name": CRC_NAME,
    "agent_role_guide": agent(ROLE, name="guide").hex(),
    "agent_tool_ephemeris": agent(TOOL, name="ephemeris.query").hex(),
    "agent_stop": agent(STOP).hex(),
    "agent_think": agent(THINK, payload="delta-v ok").hex(),
    "agent_safety": agent(SAFETY, payload="untrusted:tool").hex(),
    "cafe_v": encode_text("caf\u00e9", non_ascii="v").hex(),
    "rocket_v": encode_text("\U0001F680", non_ascii="v").hex(),
    "hello_universe": HELLO_UNIVERSE_HEX.lower(),
}
u = encode_text("Hello, Universe.\n", header=True, non_ascii="v")
f = encode_p9(u)
vectors["p9_hello_unit_hex"] = u.hex()
vectors["p9_hello_frame_hex"] = f.hex()
vectors["p9_hello_frame_len"] = len(f)
vectors["hello_kinds"] = [e["kind"] for e in decode_stream(bytes.fromhex(HELLO_UNIVERSE_HEX))]
out = ROOT / "tests" / "freeze_vectors.json"
out.write_text(json.dumps(vectors, indent=2) + "\n", encoding="utf-8")
print("wrote", out)
