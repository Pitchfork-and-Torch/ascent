#!/usr/bin/env python3
# ASCENT SkyPulse / PATHHINT goldens + LEO-IP policy.
# PYTHONPATH=ref python tests/test_skypulse.py
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
    canonical_pathhint_bytes,
    decode_stream,
    encode_pathhint,
    encode_text,
)
from ascent_skypulse import (  # noqa: E402
    PathHint,
    format_pathhint_meter,
    recommend_integrity,
    should_queue_session,
    wrap_pathhint_p9,
    evaluate_pathhint,
    pathhint_overhead_bytes,
)

VECTORS = json.loads(
    Path(__file__).with_name("skypulse_vectors.json").read_text(encoding="utf-8")
)


def test_canonical_plain_hex():
    got = canonical_pathhint_bytes(crc=False)
    exp = bytes.fromhex(VECTORS["plain"]["hex"])
    assert got == exp, f"plain hex\n got {got.hex()}\n exp {exp.hex()}"
    assert len(got) == VECTORS["plain"]["len"]
    ev = decode_stream(got)
    assert len(ev) == 1 and ev[0]["kind"] == "pathhint"
    f = VECTORS["plain"]["fields"]
    assert ev[0]["applied"] is True
    assert ev[0]["path_id"] == f["path_id"]
    assert ev[0]["next_capacity_bps"] == f["next_capacity_bps"]
    assert ev[0]["freeze_ms"] == f["freeze_ms"]
    assert abs(ev[0]["confidence"] - f["confidence"]) < 1e-9
    assert ev[0]["ttl_ms"] == f["ttl_ms"]
    assert abs(ev[0]["obstruction"] - f["obstruction"]) < 1e-9
    assert abs(ev[0]["elev_deg"] - f["elev_deg"]) < 1e-9
    assert ev[0]["crc"] is False
    assert ev[0]["next_capacity_meaning"] == "predicted_bottleneck_bps_sender"
    print("PASS test_canonical_plain_hex")


def test_canonical_crc_hex():
    got = canonical_pathhint_bytes(crc=True)
    exp = bytes.fromhex(VECTORS["crc"]["hex"])
    assert got == exp, f"crc hex\n got {got.hex()}\n exp {exp.hex()}"
    ev = decode_stream(got)[0]
    assert ev["applied"] is True
    assert ev["crc"] is True
    print("PASS test_canonical_crc_hex")


def test_roundtrip_fields():
    wire = encode_pathhint(
        path_id=7,
        next_capacity_kbps=20000,
        freeze_ms=12000,
        confidence=0.25,
        ttl_ms=8000,
        obstruction=0.0,
        elev_deg=-5.5,
        crc=True,
    )
    ev = decode_stream(wire)[0]
    assert ev["applied"] is True
    assert ev["path_id"] == 7
    assert ev["next_capacity_bps"] == 20_000_000
    assert ev["freeze_ms"] == 12000
    assert abs(ev["confidence"] - 0.25) < 1e-9
    assert ev["obstruction"] == 0.0
    assert abs(ev["elev_deg"] - (-5.5)) < 1e-9
    hint = PathHint.from_event(ev)
    assert hint.encode() == wire
    print("PASS test_roundtrip_fields")


def test_fail_closed_unknown_schema():
    raw = bytes.fromhex(VECTORS["unknown_schema"]["hex"])
    ev = decode_stream(raw)[0]
    assert ev["kind"] == "pathhint"
    assert ev["applied"] is False
    assert ev["reason"] == "unknown_schema"
    # rest of stream still decodes
    mixed = encode_text("hi\n", header=False) + raw + encode_text("ok\n")
    kinds = [e["kind"] for e in decode_stream(mixed)]
    assert kinds == ["text", "pathhint", "text"]
    assert decode_stream(mixed)[1]["applied"] is False
    print("PASS test_fail_closed_unknown_schema")


def test_fail_closed_crc():
    raw = bytearray(canonical_pathhint_bytes(crc=True))
    raw[-1] ^= 0xFF
    ev = decode_stream(bytes(raw))[0]
    assert ev["applied"] is False
    assert ev["reason"] == "crc_fail"
    print("PASS test_fail_closed_crc")


def test_fail_closed_bad_len_and_flags():
    # schema v1, len=3 garbage body
    raw = bytes([0xC5, 0x01, 0x00, 0x03, 0x00, 0x00, 0x00])
    ev = decode_stream(raw)[0]
    assert ev["applied"] is False
    assert ev["reason"] == "bad_body_len"
    # reserved flag bits
    body = bytearray(canonical_pathhint_bytes(crc=False))
    body[4] = body[4] | 0x80  # flags byte (after C5 schema len)
    ev = decode_stream(bytes(body))[0]
    assert ev["applied"] is False
    assert ev["reason"] == "unknown_flags"
    print("PASS test_fail_closed_bad_len_and_flags")


def test_truncated_hard_fault():
    try:
        decode_stream(bytes([0xC5, 0x01, 0x00, 0x1A, 0x00]))
        raise AssertionError("truncated SKYSTATE should hard-fault")
    except AscentCodecError as ex:
        assert "truncated" in str(ex).lower()
    print("PASS test_truncated_hard_fault")


def test_confidence_range_encode():
    try:
        encode_pathhint(confidence=1.2)
        raise AssertionError("confidence > 1 should raise")
    except AscentCodecError:
        pass
    try:
        encode_pathhint(obstruction=-0.1)
        raise AssertionError("obstruction < 0 should raise")
    except AscentCodecError:
        pass
    print("PASS test_confidence_range_encode")


def test_leo_ip_vs_d_integrity():
    leo = recommend_integrity("ASCENT-E-LEO")
    deep = recommend_integrity("ASCENT-D")
    star = recommend_integrity("starlink")
    earth = recommend_integrity("ASCENT-E")
    assert leo["wrap_p9"] is False
    assert leo["mode"] == "crc"
    assert leo["double_fec"] is False
    assert star["profile"] == "ASCENT-E-LEO"
    assert deep["wrap_p9"] is True
    assert deep["mode"] == "p9"
    assert deep["use_pathhint_crc"] is False
    assert earth["wrap_p9"] is False
    print("PASS test_leo_ip_vs_d_integrity")


def test_queue_policy():
    assert should_queue_session(dish_state="OBSTRUCTED") is True
    assert should_queue_session(obstruction=0.40) is True
    assert should_queue_session(obstruction=0.02, dish_state="ONLINE") is False
    assert should_queue_session(rtt_ms=240) is True
    assert should_queue_session(rtt_ms=48, rtt_prev_ms=40) is False
    assert should_queue_session(rtt_ms=140, rtt_prev_ms=40) is True
    print("PASS test_queue_policy")


def test_optional_p9_wrap():
    unit = canonical_pathhint_bytes(crc=False)
    wrapped = wrap_pathhint_p9(unit)
    if wrapped is None:
        print("SKIP test_optional_p9_wrap (ascent_d/reedsolo missing)")
        return
    assert wrapped[:4] == bytes([0xD5, 0xE5, 0xC0, 0xDE])
    from ascent_d import decode_p9  # noqa: E402

    frame, _, status = decode_p9(wrapped)
    assert status == "ok" and frame is not None
    inner = decode_stream(frame.unit)
    assert inner[0]["kind"] == "pathhint" and inner[0]["applied"] is True
    print("PASS test_optional_p9_wrap")


def test_meter_honesty():
    hint = PathHint.from_event(decode_stream(canonical_pathhint_bytes())[0])
    line = format_pathhint_meter(hint)
    assert "RF" not in line
    assert "bottleneck_hint=" in line
    assert "freeze_until=" in line
    skip = format_pathhint_meter(PathHint(applied=False, reason="crc_fail"))
    assert "erase" in skip
    print("PASS test_meter_honesty")


def test_ttl_and_missing_freeze_erase():
    from ascent_skypulse import evaluate_pathhint

    ev = decode_stream(canonical_pathhint_bytes())[0]
    live = evaluate_pathhint(ev, now_ms=10_000, received_at_ms=0)
    assert live["applied"] is True
    stale = evaluate_pathhint(ev, now_ms=40_000, received_at_ms=0)
    assert stale["applied"] is False
    assert stale["reason"] == "ttl_expired"
    # v1 requires FLAG_RELATIVE_FREEZE; clear it => erase
    raw = bytearray(canonical_pathhint_bytes(crc=False))
    raw[4] = raw[4] & ~0x08
    ev2 = decode_stream(bytes(raw))[0]
    assert ev2["applied"] is False
    assert ev2["reason"] == "missing_freeze_until"
    print("PASS test_ttl_and_missing_freeze_erase")


def test_ship_metrics_not_rf():
    from ascent_skypulse import pathhint_overhead_bytes

    plain = canonical_pathhint_bytes(crc=False)
    crc = canonical_pathhint_bytes(crc=True)
    assert len(plain) == pathhint_overhead_bytes(crc=False) == 30
    assert len(crc) == pathhint_overhead_bytes(crc=True) == 34
    applied = 0
    rejected = 0
    samples = [
        plain,
        crc,
        bytes.fromhex("c599000401020304"),
        bytes([0xC5, 0x01, 0x00, 0x03, 0x00, 0x00, 0x00]),
    ]
    for s in samples:
        ev = decode_stream(s)[0]
        if ev.get("applied"):
            applied += 1
        else:
            rejected += 1
    assert applied == 2 and rejected == 2
    print("PASS test_ship_metrics_not_rf")


def test_mixed_hello_still_three_plus_hint():
    from ascent_codec import hello_universe_bytes

    data = hello_universe_bytes() + canonical_pathhint_bytes()
    kinds = [e["kind"] for e in decode_stream(data)]
    assert kinds == ["text", "agent", "multimodal", "pathhint"]
    print("PASS test_mixed_hello_still_three_plus_hint")


def main() -> int:
    test_canonical_plain_hex()
    test_canonical_crc_hex()
    test_roundtrip_fields()
    test_fail_closed_unknown_schema()
    test_fail_closed_crc()
    test_fail_closed_bad_len_and_flags()
    test_truncated_hard_fault()
    test_confidence_range_encode()
    test_leo_ip_vs_d_integrity()
    test_queue_policy()
    test_optional_p9_wrap()
    test_meter_honesty()
    test_ttl_and_missing_freeze_erase()
    test_ship_metrics_not_rf()
    test_mixed_hello_still_three_plus_hint()
    print("ALL SKYPULSE TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
