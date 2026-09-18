#!/usr/bin/env python3
# ASCENT CLI tests - plain asserts, runnable without pytest.
# python tests/test_cli.py
# Covers the human-readable `ascent decode` labels and the encode/decode
# round trip. Locks the Python event keys (kind_name / opcode_name) the CLI
# must read; the JS camelCase spellings are not emitted by the Python codec.
# ASCII hyphens only.

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ascent.cli import main  # noqa: E402

HELLO_BIN = ROOT / "examples" / "hello-universe.ascent.bin"
AGENT_LOOP_BIN = ROOT / "examples" / "agent-loop-demo.ascent.bin"
PATHHINT_BIN = ROOT / "examples" / "skypulse-pathhint.ascent.bin"


def run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(argv)
    return rc, buf.getvalue()


def test_decode_hello_labels_every_unit() -> None:
    rc, out = run(["decode", str(HELLO_BIN)])
    assert rc == 0
    lines = out.strip().splitlines()
    assert lines[0] == "TEXT: 'ASCENT/1.0\\nHello, Universe.\\n'", lines[0]
    assert lines[1] == "AGENT: ROLE name= guide", lines[1]
    assert lines[2].startswith("MM: REF cid:sha256:"), lines[2]
    assert "None" not in out, out
    print("PASS test_decode_hello_labels_every_unit")


def test_decode_agent_loop_opcodes() -> None:
    rc, out = run(["decode", str(AGENT_LOOP_BIN)])
    assert rc == 0
    ops = [ln.split()[1] for ln in out.splitlines() if ln.startswith("AGENT:")]
    assert ops == ["ROLE", "THINK", "TOOL", "SAFETY", "STOP"], ops
    print("PASS test_decode_agent_loop_opcodes")


def test_decode_pathhint_summary() -> None:
    rc, out = run(["decode", str(PATHHINT_BIN)])
    assert rc == 0
    assert out.startswith("PATHHINT: applied=True path_id=66 bottleneck_bps=50000000"), out
    print("PASS test_decode_pathhint_summary")


def test_bridge_inline_is_labeled() -> None:
    rc, hexout = run(["encode", "caf\u00e9", "--mode", "bridge"])
    assert rc == 0
    rc, out = run(["decode", hexout.strip()])
    assert rc == 0
    mm = [ln for ln in out.splitlines() if ln.startswith("MM:")]
    assert mm == ["MM: INLINE \u00e9"], mm
    print("PASS test_bridge_inline_is_labeled")


def test_encode_decode_roundtrip_hex() -> None:
    rc, hexout = run(["encode", "--header", "--role", "guide", "Hello, Universe."])
    assert rc == 0
    wire = hexout.strip()
    assert wire.startswith("415343454E542F312E300A"), wire  # "ASCENT/1.0\n"
    rc, out = run(["decode", wire])
    assert rc == 0
    assert "TEXT: 'ASCENT/1.0\\nHello, Universe.'" in out, out
    assert "AGENT: ROLE name= guide" in out, out
    print("PASS test_encode_decode_roundtrip_hex")


def test_hello_matches_sample_file() -> None:
    rc, out = run(["hello"])
    assert rc == 0
    assert bytes.fromhex(out.strip()) == HELLO_BIN.read_bytes()
    print("PASS test_hello_matches_sample_file")


def main_tests() -> int:
    test_decode_hello_labels_every_unit()
    test_decode_agent_loop_opcodes()
    test_decode_pathhint_summary()
    test_bridge_inline_is_labeled()
    test_encode_decode_roundtrip_hex()
    test_hello_matches_sample_file()
    print("ALL CLI TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_tests())
