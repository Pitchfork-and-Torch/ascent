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
    HELLO_UNIVERSE_HEX,
    encode_text,
    encode_text_ascent7,
    encode_scalar,
    decode_stream,
    events_to_jsonable,
    hello_universe_bytes,
    Cont,
    cont_byte,
    cont_val,
)


VECTORS_PATH = Path(__file__).with_name("test_vectors.json")


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


def main() -> int:
    test_vectors_encode_hex()
    test_roundtrip_v_mode()
    test_hello_universe_three_units()
    test_surrogate_raises()
    test_ascent7_rejects_non_ascii()
    test_events_kind_strings_only()
    test_cont_frozen()
    print("ALL TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
