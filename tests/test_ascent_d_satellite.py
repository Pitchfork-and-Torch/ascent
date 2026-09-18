#!/usr/bin/env python3
"""ASCENT-D P9 tests with a real satellite scenario (ISS).

Legal rails:
- Uses public Celestrak TLE for ISS (ZARYA).
- Models a LEO downlink BER and exercises ASCENT-D RS(255,223) erase-on-fail.
- Does NOT transmit RF. No satellite commanding. Receive-side / lab simulation only.

Run from repo root:
  set PYTHONPATH=ref
  py -3 tests/test_ascent_d_satellite.py
"""
from __future__ import annotations

import math
import random
import struct
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ref"))

from ascent_codec import encode_text, decode_stream, hello_universe_bytes  # noqa: E402
from ascent_d import (  # noqa: E402
    CRC_NAME,
    PROFILE_D,
    SYNC,
    decode_p9,
    encode_p9,
)


def fetch_iss_tle() -> tuple[str, str, str]:
    """Return (name, line1, line2) for ISS from Celestrak."""
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
    req = urllib.request.Request(url, headers={"User-Agent": "ASCENT-D-lab/2.0.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if ln.startswith("ISS") and i + 2 < len(lines):
            return ln, lines[i + 1], lines[i + 2]
    raise RuntimeError("ISS TLE not found in Celestrak stations feed")


def parse_mean_motion(line2: str) -> float:
    # Mean motion rev/day is columns 53-63 in classic TLE line 2 (1-based)
    # Python slice: [52:63]
    return float(line2[52:63].strip())


def parse_inclination(line2: str) -> float:
    return float(line2[8:16].strip())


def leo_scenario(tle_name: str, line2: str) -> dict:
    """Build a simple LEO link scenario from real TLE fields."""
    n = parse_mean_motion(line2)  # rev/day
    period_min = 1440.0 / n if n else 0.0
    # Approximate semi-major axis from mean motion (Earth mu)
    # n_rad_s = n * 2pi / 86400; a = (mu / n^2)^(1/3)
    mu = 3.986004418e14
    n_rad = n * 2.0 * math.pi / 86400.0
    a_m = (mu / (n_rad ** 2)) ** (1.0 / 3.0) if n_rad > 0 else 0.0
    earth_r = 6371e3
    alt_km = (a_m - earth_r) / 1000.0
    # Lab BER tiers inspired by LEO S-band / UHF amateur-class links (order-of-magnitude)
    return {
        "satellite": tle_name,
        "inclination_deg": parse_inclination(line2),
        "period_min": period_min,
        "approx_altitude_km": alt_km,
        "mean_motion_rev_per_day": n,
        "ber_clear": 1e-5,
        "ber_degraded": 5e-3,
        "ber_blackout": 5e-2,
        "utc": datetime.now(timezone.utc).isoformat(),
        "crc_algo": CRC_NAME,
        "note": "RF TX not performed. Public TLE + channel model only.",
    }


def inject_bit_errors(data: bytes, ber: float, rng: random.Random) -> tuple[bytes, int]:
    if ber <= 0:
        return data, 0
    out = bytearray(data)
    flips = 0
    for i in range(len(out) * 8):
        if rng.random() < ber:
            byte_i, bit = divmod(i, 8)
            out[byte_i] ^= 1 << bit
            flips += 1
    return bytes(out), flips


def build_iss_payload(tle_name: str, line1: str, line2: str) -> bytes:
    """Inner ASCENT-E unit: header + telemetry text + ROLE beacon."""
    msg = (
        f"ASCENT-D beacon via {tle_name}\n"
        f"TLE1 {line1[:40]}...\n"
        f"period_lab_test\n"
    )
    return encode_text(msg, header=True, role="beacon", non_ascii="reject")


def run() -> int:
    print("=== ASCENT-D + real satellite (ISS) lab ===")
    print("Legal: public TLE + simulated downlink BER. No RF transmit.\n")

    name, l1, l2 = fetch_iss_tle()
    scenario = leo_scenario(name, l2)
    print("Satellite:", scenario["satellite"])
    print("Inclination deg:", round(scenario["inclination_deg"], 4))
    print("Period min:", round(scenario["period_min"], 3))
    print("Approx altitude km:", round(scenario["approx_altitude_km"], 1))
    print("Mean motion rev/day:", scenario["mean_motion_rev_per_day"])
    print("CRC:", scenario["crc_algo"])
    print("UTC:", scenario["utc"])
    print()

    # Clean path: Hello Universe also works as unit
    unit = build_iss_payload(name, l1, l2)
    frame = encode_p9(unit, profile=PROFILE_D, interleave=1)
    assert frame.startswith(SYNC)
    fr, nxt, status = decode_p9(frame)
    assert status == "ok" and fr is not None
    assert fr.unit == unit
    print("CLEAN encode/decode: OK  frame_len=%d unit_len=%d" % (len(frame), len(unit)))

    # Also wrap product Hello Universe
    hello = hello_universe_bytes()
    hf = encode_p9(hello, profile=PROFILE_D, interleave=1)
    fr2, _, st2 = decode_p9(hf)
    assert st2 == "ok" and fr2 and fr2.unit == hello
    kinds = [e["kind"] for e in decode_stream(fr2.unit)]
    assert kinds == ["text", "agent", "multimodal"]
    print("CLEAN Hello-Universe inside P9: OK  kinds=%s" % kinds)
    print()

    rng = random.Random(1963)
    results = []
    for label, ber in [
        ("LEO_clear", scenario["ber_clear"]),
        ("LEO_degraded", scenario["ber_degraded"]),
        ("LEO_blackout", scenario["ber_blackout"]),
    ]:
        ok = 0
        erased = 0
        trials = 40
        total_flips = 0
        for t in range(trials):
            noisy, flips = inject_bit_errors(frame, ber, rng)
            total_flips += flips
            # prepend junk + frame + junk (sync hunt)
            stream = bytes([0x00, 0xFF, 0x55]) + noisy + bytes([0xAA, 0x00])
            frx, _, st = decode_p9(stream, 0)
            if st == "ok" and frx and frx.unit == unit:
                ok += 1
            else:
                erased += 1
        results.append((label, ber, ok, erased, trials, total_flips))
        print(
            "%s ber=%.1e recovered=%d/%d erased=%d flips~%d"
            % (label, ber, ok, trials, erased, total_flips)
        )

    # Expectations: clear mostly recovers; blackout mostly erases (no mojibake)
    clear_ok = results[0][2]
    black_erase = results[2][3]
    assert clear_ok >= 30, "clear LEO should usually recover (got %d/40)" % clear_ok
    assert black_erase >= 20, "blackout should erase often (got %d/40)" % black_erase

    # Explicit uncorrectable: corrupt beyond RS capability without hunting false OK
    bad = bytearray(frame)
    # flip many bytes inside first codeword region (after header+unit)
    # header: 4 sync + 1 prof + 5 ecc + 4 len + unit
    off = 4 + 1 + 5 + 4 + len(unit)
    for k in range(40):
        bad[off + k] ^= 0xFF
    frb, _, stb = decode_p9(bytes(bad))
    assert stb == "erased" and frb is None
    print("Hard corruption => erased (no mojibake): OK")

    print()
    print("ASCENT-D SATELLITE LAB PASS")
    print(
        "Summary: real ISS TLE used for scenario; ASCENT-D RS(255,223) recovers clear LEO noise and erases blackout frames."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as ex:
        print("FAIL:", ex)
        raise
