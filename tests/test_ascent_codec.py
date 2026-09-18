#!/usr/bin/env python3
# ASCENT codec vector tests - plain asserts, runnable without pytest.
# py -3 tests/test_ascent_codec.py
# ASCII hyphens only.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "ref"
if str(REF) not in sys.path:
    sys.path.insert(0, str(REF))

from ascent_codec import (  # noqa: E402
    AscentCodecError,
    ASCENT_V_LONG_MIN,
    FLAG_CRITICAL,
    HELLO_UNIVERSE_HEX,
    encode_agent_frame,
    encode_text,
    encode_text_ascent7,
    encode_scalar,
    escape_agent_args,
    unescape_agent_args,
    decode_ascent_v_at,
    decode_stream,
    events_to_jsonable,
    hello_universe_bytes,
    long_form_required,
    Cont,
    cont_byte,
    cont_val,
)


VECTORS_PATH = Path(__file__).with_name("test_vectors.json")
GUARD_PATH = Path(__file__).with_name("encoding_guard_vectors.json")


def load_vectors():
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def test_vectors_encode_hex():
    cases = load_vectors()
    for case in cases:
        name = case["name"]
        if case.get("product"):
            built = hello_universe_bytes()
            expected = bytes.fromhex(case["hex"])
            assert built == expected, f"{name}: product bytes mismatch"
            assert built.hex().upper() == HELLO_UNIVERSE_HEX.upper()
            continue
        if case.get("expect_error"):
            try:
                encode_text(
                    case["text"],
                    header=case.get("header", False),
                    role=case.get("role"),
                    non_ascii=case.get("mode", "v"),
                )
                raise AssertionError(f"{name}: expected error, got success")
            except AscentCodecError as ex:
                msg = str(ex).lower()
                assert "surrogate" in msg, f"{name}: unexpected error {ex}"
            continue
        got = encode_text(
            case["text"],
            header=case.get("header", False),
            role=case.get("role"),
            non_ascii=case.get("mode", "v"),
        )
        if "hex" in case:
            exp = bytes.fromhex(case["hex"])
            assert got == exp, (
                f"{name}: hex mismatch\n got {got.hex().upper()}\n exp {case['hex'].upper()}"
            )
    print("PASS test_vectors_encode_hex")


def test_roundtrip_v_mode():
    cases = load_vectors()
    for case in cases:
        if not case.get("roundtrip"):
            continue
        name = case["name"]
        text = case["text"]
        # JSON may expand rocket as surrogate pair string; normalize via encode
        if name == "rocket_emoji_v":
            text = "\U0001F680"
        wire = encode_text(text, non_ascii="v")
        events = decode_stream(wire)
        texts = [e for e in events if e["kind"] == "text"]
        assert texts, f"{name}: no text events"
        merged = "".join(e["text"] for e in texts)
        assert merged == text, f"{name}: roundtrip {merged!r} != {text!r}"
    print("PASS test_roundtrip_v_mode")


def test_hello_universe_three_units():
    data = hello_universe_bytes()
    events = decode_stream(data)
    kinds = [e["kind"] for e in events]
    assert kinds == ["text", "agent", "multimodal"], f"kinds={kinds}"
    assert "Hello, Universe" in events[0]["text"]
    assert events[1].get("name") == "guide"
    assert events[2].get("kind_name") == "REF"
    assert events[2].get("mm_kind") == 1
    assert events[2]["kind"] == "multimodal"
    print("PASS test_hello_universe_three_units")


def test_surrogate_raises():
    try:
        encode_scalar(0xD800)
        raise AssertionError("encode_scalar surrogate should raise")
    except AscentCodecError:
        pass
    try:
        encode_text("\ud800", non_ascii="v")
        raise AssertionError("encode_text surrogate should raise")
    except AscentCodecError:
        pass
    print("PASS test_surrogate_raises")


def test_ascent7_rejects_non_ascii():
    try:
        encode_text_ascent7("caf\u00e9")
        raise AssertionError("ASCENT-7 should reject non-ascii")
    except AscentCodecError as ex:
        assert "ASCENT-7" in str(ex) or "non-ASCII" in str(ex)
    # identity for pure ascii
    s = "Hello, Universe.\n"
    assert encode_text_ascent7(s) == s.encode("ascii")
    print("PASS test_ascent7_rejects_non_ascii")


def test_events_kind_strings_only():
    data = hello_universe_bytes()
    events = decode_stream(data)
    for e in events:
        assert isinstance(e["kind"], str), f"kind not str: {e['kind']!r}"
        assert e["kind"] in (
            "text",
            "agent",
            "multimodal",
            "def",
            "crypto",
            "pad",
            "pathhint",
            "skip",
        )
    j = events_to_jsonable(events)
    for row in j:
        assert row["kind"] in (
            "text",
            "agent",
            "multimodal",
            "def",
            "crypto",
            "pad",
            "pathhint",
            "skip",
        )
        # mm wire kind must not overwrite event kind
        if row["kind"] == "multimodal":
            assert row.get("mm_kind") == 1
            assert row["kind"] == "multimodal"
    # bridge cafe has multimodal INLINE
    bridge = encode_text("caf\u00e9", non_ascii="bridge")
    bevs = decode_stream(bridge)
    kinds = [e["kind"] for e in bevs]
    assert "text" in kinds and "multimodal" in kinds
    mm = [e for e in bevs if e["kind"] == "multimodal"][0]
    assert mm["mm_kind"] == 2
    assert mm.get("kind_name") == "INLINE"
    print("PASS test_events_kind_strings_only")


def test_encoding_guard_long():
    guard = json.loads(GUARD_PATH.read_text(encoding="utf-8"))
    assert ASCENT_V_LONG_MIN == 0x2C280
    assert long_form_required(0x2C280)
    assert not long_form_required(0x2C27F)
    assert not long_form_required(0x41)
    assert not long_form_required(0xE9)
    assert not long_form_required(0x1F680)

    for name, case in guard.items():
        if name == "note" or not isinstance(case, dict):
            continue
        raw = bytes.fromhex(case["hex"])
        if case.get("reject"):
            try:
                decode_ascent_v_at(raw, 0)
                raise AssertionError(f"{name}: expected reject, decoded")
            except AscentCodecError as ex:
                msg = str(ex).lower()
                needle = case["reject"]
                assert needle in msg, f"{name}: wanted {needle!r} in {ex}"
            try:
                decode_stream(raw)
                raise AssertionError(f"{name}: decode_stream should reject")
            except AscentCodecError:
                pass
            if case.get("shortest_hex"):
                # shortest form still decodes
                short = bytes.fromhex(case["shortest_hex"])
                cp, end = decode_ascent_v_at(short, 0)
                assert end == len(short)
                assert cp > 0x7F
            continue
        cp, end = decode_ascent_v_at(raw, 0)
        assert cp == case["cp"], f"{name}: cp {cp:#x} != {case['cp']:#x}"
        assert end == len(raw)
        assert bytes(encode_scalar(cp)) == raw, f"{name}: encode/decode lock"

    # last 4-byte must not be emitted as LONG
    last4 = bytes.fromhex(guard["last_4byte_2c27f"]["hex"])
    assert bytes(encode_scalar(0x2C27F)) == last4
    print("PASS test_encoding_guard_long")


def test_cont_frozen():
    assert cont_byte(0) == 0xA0
    assert cont_byte(0x1F) == 0xBF
    assert cont_val(0xA0) == 0
    assert cont_val(0xBF) == 0x1F
    assert Cont.is_cont(0xA5)
    assert not Cont.is_cont(0x9F)
    try:
        cont_val(0x80)
        raise AssertionError("cont_val should reject non-cont")
    except AscentCodecError:
        pass
    print("PASS test_cont_frozen")


def test_4byte_surrogate_decode_rejects():
    """Parse law: 4-byte residual covers U+D800..DFFF; decoder must hard-fault."""
    raw = bytes.fromhex("F1A5ACA0")
    try:
        decode_ascent_v_at(raw, 0)
        raise AssertionError("4-byte U+D800 should reject")
    except AscentCodecError as ex:
        assert "surrogate" in str(ex).lower()
    try:
        decode_stream(raw)
        raise AssertionError("decode_stream 4-byte surrogate should reject")
    except AscentCodecError as ex:
        assert "surrogate" in str(ex).lower()
    # Must not emit a text unit containing a surrogate
    mixed = b"Hi" + raw + b"!"
    try:
        decode_stream(mixed)
        raise AssertionError("mixed 4-byte surrogate should reject")
    except AscentCodecError:
        pass
    print("PASS test_4byte_surrogate_decode_rejects")


def test_agent_fence_escape_roundtrip():
    payload = bytes([0x00, 0x9A, 0x9B, 0xC1, 0x1B, 0x41])
    wire = encode_agent_frame(opcode_name="THINK", payload=payload)
    assert wire[0] == 0x9A and wire[-1] == 0x9B
    alen = (wire[6] << 8) | wire[7]
    args_wire = wire[8 : 8 + alen]
    i = 0
    while i < len(args_wire):
        if (
            args_wire[i] == 0xC1
            and i + 2 < len(args_wire)
            and args_wire[i + 1] == 0x1B
        ):
            i += 3
            continue
        assert args_wire[i] not in (0x9A, 0x9B), "raw fence outside escape"
        i += 1
    evs = decode_stream(wire)
    assert len(evs) == 1 and evs[0]["kind"] == "agent"
    assert evs[0]["skipped"] is False
    assert evs[0]["opcode_name"] == "THINK"
    assert bytes.fromhex(evs[0]["args_hex"]) == payload
    # unescape of the escaped form is injective
    assert unescape_agent_args(escape_agent_args(payload)) == payload
    print("PASS test_agent_fence_escape_roundtrip")


def test_bare_fence_and_truncated_escape():
    # Bare OPEN inside declared args (nested fence)
    nested = bytes.fromhex("9AC10100040000019A9B")
    try:
        decode_stream(nested)
        raise AssertionError("bare 9A in args should reject")
    except AscentCodecError as ex:
        assert "bare fence" in str(ex).lower()
    # Truncated C1 1B at end of args
    trunc = bytes.fromhex("9AC1010004000002C11B9B")
    try:
        decode_stream(trunc)
        raise AssertionError("truncated fence escape should reject")
    except AscentCodecError as ex:
        assert "truncated fence escape" in str(ex).lower()
    print("PASS test_bare_fence_and_truncated_escape")


def test_agent_name_charset_and_critical_unknown():
    guide = encode_agent_frame(opcode_name="ROLE", name="guide")
    assert guide.hex().upper() == "9AC10100020000060567756964659B"
    ev = decode_stream(guide)[0]
    assert ev["name"] == "guide" and ev["skipped"] is False

    try:
        encode_agent_frame(opcode_name="ROLE", name="bad name")
        raise AssertionError("space in ROLE name should reject")
    except AscentCodecError as ex:
        assert "charset" in str(ex).lower()

    try:
        encode_agent_frame(opcode_name="ROLE", name="")
        raise AssertionError("empty ROLE name should reject")
    except AscentCodecError:
        pass

    # name_len=0 on the wire
    empty = bytes.fromhex("9AC1010002000001009B")
    try:
        decode_stream(empty)
        raise AssertionError("name_len 0 should reject")
    except AscentCodecError:
        pass

    # unknown opcode, CRITICAL clear => skip (never execute)
    unk = encode_agent_frame(opcode=0x00AA, payload=b"x")
    evu = decode_stream(unk)[0]
    assert evu["kind"] == "agent"
    assert evu["skipped"] is True
    assert evu["reason"] == "unknown_opcode"

    # unknown opcode, CRITICAL set => hard-fault
    crit = encode_agent_frame(opcode=0x00AA, flags=FLAG_CRITICAL, payload=b"x")
    try:
        decode_stream(crit)
        raise AssertionError("CRITICAL unknown opcode should reject")
    except AscentCodecError as ex:
        msg = str(ex).lower()
        assert "critical" in msg and "opcode" in msg

    # unknown ver: skip-by-length, do not execute
    badver = bytes.fromhex("9AC10200020000060567756964659B")
    evv = decode_stream(badver)[0]
    assert evv["skipped"] is True
    assert evv["reason"] == "unknown_ver"
    assert evv.get("name") is None

    # sequential frames are not nested
    two = encode_agent_frame(opcode_name="ROLE", name="guide") + encode_agent_frame(
        opcode_name="STOP"
    )
    kinds = [e["kind"] for e in decode_stream(two)]
    assert kinds == ["agent", "agent"]
    print("PASS test_agent_name_charset_and_critical_unknown")


def test_p2_skip_by_length_keeps_ascii():
    """Unknown length-declared P2 must skip; following P0 stays ASCII."""
    body = b"NOPE"
    c2 = bytes([0xC2]) + (len(body)).to_bytes(2, "big") + body
    c3 = bytes([0xC3]) + (len(body)).to_bytes(4, "big") + body
    cf = bytes([0xCF]) + (0x8001).to_bytes(2, "big") + (len(body)).to_bytes(4, "big") + body
    stream = b"Hi" + c2 + b"ok" + c3 + b"!" + cf + b"end"
    evs = decode_stream(stream)
    kinds = [e["kind"] for e in evs]
    assert kinds == ["text", "skip", "text", "skip", "text", "skip", "text"]
    texts = [e["text"] for e in evs if e["kind"] == "text"]
    assert texts == ["Hi", "ok", "!", "end"]
    assert evs[1]["lead_name"] == "VERSION_BUMP"
    assert evs[3]["lead_name"] == "REGISTRY_DELTA"
    assert evs[5]["lead_name"] == "PRIVATE_OP"
    assert evs[5]["plane"] == 0x8001
    for s in evs:
        if s["kind"] == "skip":
            assert s["skipped"] is True
    # truncated C2 is a hard-fault, not a swallow of later ASCII
    try:
        decode_stream(bytes([0xC2, 0x00, 0x05, 0x41]))
        raise AssertionError("truncated VERSION_BUMP should reject")
    except AscentCodecError as ex:
        assert "truncated" in str(ex).lower()
    print("PASS test_p2_skip_by_length_keeps_ascii")


def main() -> int:
    test_vectors_encode_hex()
    test_roundtrip_v_mode()
    test_hello_universe_three_units()
    test_surrogate_raises()
    test_ascent7_rejects_non_ascii()
    test_events_kind_strings_only()
    test_encoding_guard_long()
    test_cont_frozen()
    test_4byte_surrogate_decode_rejects()
    test_agent_fence_escape_roundtrip()
    test_bare_fence_and_truncated_escape()
    test_agent_name_charset_and_critical_unknown()
    test_p2_skip_by_length_keeps_ascii()
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
