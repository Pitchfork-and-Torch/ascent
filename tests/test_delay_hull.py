#!/usr/bin/env python3
# Delay Hull goldens: TURN 0xC6, CHUNK reassembly, contact clock.
# ASCII hyphens only. No network.
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ref"))

from ascent_codec import (  # noqa: E402
    AscentCodecError,
    canonical_turn_bytes,
    decode_stream,
    encode_mm_chunk,
    encode_mm_end,
    encode_turn,
    reassemble_chunks,
)
from ascent_delay import ContactLab, sample_adu  # noqa: E402


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("FAIL " + msg)
    print("PASS " + msg)


def test_turn_roundtrip() -> None:
    raw = canonical_turn_bytes(crc=True)
    ev = decode_stream(raw)
    _expect(len(ev) == 1 and ev[0]["kind"] == "turn", "one turn event")
    t = ev[0]
    _expect(t["applied"] is True and t["crc"] is True, "crc turn applied")
    _expect(t["session"] == 0xA5CE47 and t["turn"] == 1, "session and turn")
    _expect(t["corr"] == 0x1001 and t["lifetime_s"] == 3600, "corr and lifetime")
    _expect(t["role"] == 1 and t["role_name"] == "request", "request role")
    _expect(len(raw) == 35, "crc turn is 35 bytes")
    plain = canonical_turn_bytes(crc=False)
    _expect(len(plain) == 31, "plain turn is 31 bytes")
    _expect(decode_stream(plain)[0]["applied"] is True, "plain turn applied")
    flipped = bytearray(raw)
    flipped[-1] ^= 0xFF
    bad = decode_stream(bytes(flipped))[0]
    _expect(bad["applied"] is False and bad["reason"] == "crc_fail", "crc fail erases")
    unknown = bytearray(raw)
    unknown[1] = 0x02
    unk = decode_stream(bytes(unknown))[0]
    _expect(unk["applied"] is False and unk["reason"] == "unknown_schema", "unknown schema skips")
    try:
        encode_turn(session=1, turn=1, corr=1, lifetime_s=1, role=9)
        raise SystemExit("FAIL role 9 should reject")
    except AscentCodecError:
        print("PASS role 9 rejected at encode")
    bad_role = bytearray(plain)
    bad_role[4 + 25] = 9  # lead, schema, len:u16, then body[25] = role
    # plain layout: 0 lead, 1 schema, 2-3 len, body starts at 4. role at body[25] => offset 29
    bad_role = bytearray(plain)
    bad_role[4 + 25] = 9
    role_ev = decode_stream(bytes(bad_role))[0]
    _expect(role_ev["applied"] is False and role_ev["reason"] == "bad_role", "bad role erases")


def _chunks(parts, stream_id=None, end=True, digest=None):
    out = b""
    for i, part in enumerate(parts):
        out += encode_mm_chunk(part, i, stream_id)
    if end:
        if digest is None and parts:
            whole = b"".join(parts)
            digest = hashlib.sha256(whole).digest()
        flags_digest = digest if digest is not None else b""
        out += encode_mm_end(
            stream_id,
            digest=flags_digest if flags_digest else b"",
            hash_alg=1 if flags_digest else 0,
            final_hash=bool(flags_digest),
        )
    return out


def test_chunks() -> None:
    a = b"alpha-"
    b = b"beta"
    raw = _chunks([b, a], stream_id=7)  # wait order is index 0 then 1. I passed [b, a] wrong.
    # redo: parts in index order
    raw = _chunks([a, b], stream_id=7)
    # reorder on the wire: chunk 1 then chunk 0 then end
    c0 = encode_mm_chunk(a, 0, 7)
    c1 = encode_mm_chunk(b, 1, 7)
    whole = a + b
    end = encode_mm_end(7, digest=hashlib.sha256(whole).digest(), hash_alg=1, final_hash=True)
    ev = decode_stream(c1 + c0 + end)
    got = reassemble_chunks(ev)
    _expect(len(got) == 1 and got[0]["status"] == "complete", "reorder completes")
    _expect(got[0]["payload"] == whole and got[0]["hash_valid"] is True, "payload and hash")
    _expect(got[0]["stream_id"] == 7, "stream id 7")

    dup = decode_stream(c0 + c0 + end)
    dgot = reassemble_chunks(dup)
    _expect(dgot[0]["status"] == "malformed" and dgot[0]["reason"] == "duplicate_chunk_index", "duplicate index")
    _expect(dgot[0]["emitted"] is False, "duplicate does not emit")

    missing = decode_stream(c0 + c1)
    mgot = reassemble_chunks(missing)
    _expect(mgot[0]["status"] == "incomplete" and mgot[0]["reason"] == "missing_end", "missing END")
    _expect(mgot[0]["emitted"] is False and mgot[0]["payload"] == b"", "missing END discards")

    gap = decode_stream(encode_mm_chunk(a, 0, 3) + encode_mm_chunk(b, 2, 3) + encode_mm_end(3))
    ggot = reassemble_chunks(gap)
    _expect(ggot[0]["status"] == "incomplete" and ggot[0]["reason"] == "gap_at_end", "gap at END")

    s1 = encode_mm_chunk(b"one", 0, 1) + encode_mm_end(1)
    s2 = encode_mm_chunk(b"two", 0, 2) + encode_mm_end(2)
    both = reassemble_chunks(decode_stream(s2 + s1))
    _expect(len(both) == 2, "two streams")
    by_id = {row["stream_id"]: row["payload"] for row in both}
    _expect(by_id[1] == b"one" and by_id[2] == b"two", "streams stay apart")

    bad_hash = decode_stream(
        encode_mm_chunk(a, 0, 9) + encode_mm_end(9, digest=b"\x00" * 32, hash_alg=1, final_hash=True)
    )
    hgot = reassemble_chunks(bad_hash)
    _expect(hgot[0]["status"] == "malformed" and hgot[0]["reason"] == "hash_mismatch", "hash mismatch")
    _expect(hgot[0]["emitted"] is False, "bad hash does not emit")
    # silence unused
    _expect(len(raw) > 0, "index-order chunk encodes")


def test_contact() -> None:
    lab = ContactLab(windows=[(100, 200)], now=0)
    adu = sample_adu()
    held = lab.enqueue(adu)
    _expect(held["status"] == "held", "window closed holds")
    _expect(lab.advance(50) == [], "still closed")
    delivered = lab.advance(100)
    _expect(len(delivered) == 1 and delivered[0]["status"] == "delivered", "window opens")
    _expect(delivered[0]["tools"] == ["ping"], "one TOOL")
    again = ContactLab(windows=[(0, 10)], now=0)
    again.enqueue(adu)
    again.advance(1)
    dup = again.enqueue(adu)
    _expect(dup["status"] == "held", "second copy spooled")
    second = again.advance(2)
    _expect(len(second) == 1 and second[0]["status"] == "duplicate", "duplicate corr is a no-op")
    _expect(second[0]["tools"] == [], "duplicate emits no TOOL")

    short = ContactLab(windows=[(0, 5000)], now=0)
    short.enqueue(sample_adu(lifetime_s=10))
    dropped = short.advance(11)
    _expect(dropped[0]["status"] == "dropped" and dropped[0]["tools"] == [], "lifetime drops")

    deep = ContactLab(windows=[(0, 50)], now=0)
    deep.enqueue(sample_adu(corr=0x2002), ascent_d=True)
    deep.smash_stored(0, count=17)
    erased = deep.advance(1)
    _expect(erased[0]["status"] == "erased", "flipped P9 spool erases")
    _expect(erased[0]["tools"] == [], "erase emits no TOOL")

    clean = ContactLab(windows=[(0, 50)], now=0)
    clean.enqueue(sample_adu(corr=0x2003, tool="pong"), ascent_d=True)
    ok = clean.advance(1)
    _expect(ok[0]["status"] == "delivered" and ok[0]["tools"] == ["pong"], "clean P9 delivers")


def main() -> int:
    test_turn_roundtrip()
    test_chunks()
    test_contact()
    print("ALL DELAY HULL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
