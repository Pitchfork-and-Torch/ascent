#!/usr/bin/env python3
# ASCENT CLI decode input tests - plain asserts, runnable without pytest.
# python tests/test_cli_decode_input.py
#
# Locks two decode-path crashes:
#   1. `ascent decode <hex>` with hex longer than NAME_MAX (255 chars, i.e. any
#      stream over 127 bytes) raised OSError ENAMETOOLONG from Path.is_file on
#      Python 3.10-3.12. `ascent hello | ascent decode` was the shipped repro.
#   2. `ascent decode --json` on a ROLE/TOOL/HANDOFF frame with zero-length
#      args leaked raw bytes into the event and json.dumps raised TypeError.
# ASCII hyphens only.

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ascent import HELLO_UNIVERSE_HEX, hello_universe_bytes  # noqa: E402
from ascent.cli import main  # noqa: E402

HELLO_BIN = ROOT / "examples" / "hello-universe.ascent.bin"
HELLO_KINDS = ["text", "agent", "multimodal"]

# 9A C1 ver=1 opcode=ROLE flags=0 len=0 9B  (SPEC says name is 1..64 B; the
# decoder must still produce a JSON-safe event instead of crashing).
EMPTY_ROLE_HEX = "9AC1010002000000" + "9B"


def run(argv: list[str], stdin: str | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    saved_stdin = sys.stdin
    try:
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = main(argv)
    finally:
        sys.stdin = saved_stdin
    return rc, out.getvalue(), err.getvalue()


def _assert_hello_text_output(out: str) -> None:
    lines = out.strip().splitlines()
    assert len(lines) == 3, lines
    assert lines[0].startswith("TEXT: "), lines[0]
    assert lines[1] == "AGENT: ROLE name= guide", lines[1]
    assert lines[2].startswith("MM: "), lines[2]


def test_hello_hex_exceeds_name_max() -> None:
    # Guard the premise: the shipped sample is long enough to hit the bug.
    assert len(HELLO_UNIVERSE_HEX) > 255, len(HELLO_UNIVERSE_HEX)
    print("PASS test_hello_hex_exceeds_name_max")


def test_decode_long_hex_argument() -> None:
    rc, out, err = run(["decode", HELLO_UNIVERSE_HEX])
    assert rc == 0, (rc, err)
    assert err == "", err
    _assert_hello_text_output(out)
    print("PASS test_decode_long_hex_argument")


def test_decode_long_hex_stdin() -> None:
    # `ascent hello | ascent decode` - includes a trailing newline like a pipe.
    rc, hello_out, _ = run(["hello"])
    assert rc == 0
    rc, out, err = run(["decode"], stdin=hello_out)
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    print("PASS test_decode_long_hex_stdin")


def test_decode_long_hex_json() -> None:
    rc, out, err = run(["decode", "--json", HELLO_UNIVERSE_HEX])
    assert rc == 0, (rc, err)
    events = json.loads(out)
    assert [ev["kind"] for ev in events] == HELLO_KINDS, events
    assert events[1]["name"] == "guide", events[1]
    print("PASS test_decode_long_hex_json")


def test_decode_very_long_hex() -> None:
    # Well past any filesystem limit: 8 KiB of P0 text + one ROLE frame.
    body = ("The quick brown fox jumps over the lazy dog. " * 200).encode("ascii")
    assert len(body) > 8000
    rc, enc_out, _ = run(["encode", "--role", "scribe", body.decode("ascii")])
    assert rc == 0
    wire_hex = enc_out.strip()
    assert len(wire_hex) > 16000, len(wire_hex)
    rc, out, err = run(["decode", "--json", wire_hex])
    assert rc == 0, (rc, err)
    events = json.loads(out)
    assert [ev["kind"] for ev in events] == ["text", "agent"], [ev["kind"] for ev in events]
    assert events[0]["text"].encode("ascii") == body
    assert events[1]["name"] == "scribe"
    print("PASS test_decode_very_long_hex")


def test_decode_hex_with_whitespace_and_prefixes() -> None:
    hexstr = HELLO_UNIVERSE_HEX
    spaced = "\r\n".join(hexstr[i : i + 32] for i in range(0, len(hexstr), 32))
    rc, out, err = run(["decode", spaced])
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    prefixed = " ".join("0x" + hexstr[i : i + 2] for i in range(0, len(hexstr), 2))
    rc, out, err = run(["decode", prefixed])
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    print("PASS test_decode_hex_with_whitespace_and_prefixes")


def test_decode_file_path_still_detected() -> None:
    rc, out, err = run(["decode", str(HELLO_BIN)])
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    rc, out, err = run(["decode", "--file", str(HELLO_BIN)])
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    # A relative path that resolves to a file wins over hex parsing.
    cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        rc, out, err = run(["decode", "examples/hello-universe.ascent.bin"])
    finally:
        os.chdir(cwd)
    assert rc == 0, (rc, err)
    _assert_hello_text_output(out)
    print("PASS test_decode_file_path_still_detected")


def test_decode_file_written_from_long_hex_matches() -> None:
    # Round trip: hex arg -> bytes -> temp file -> decode; same events either way.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "hello.bin"
        path.write_bytes(bytes.fromhex(HELLO_UNIVERSE_HEX))
        assert path.read_bytes() == hello_universe_bytes()
        rc, via_file, _ = run(["decode", "--json", str(path)])
        rc2, via_hex, _ = run(["decode", "--json", HELLO_UNIVERSE_HEX])
    assert rc == 0 and rc2 == 0
    assert json.loads(via_file) == json.loads(via_hex)
    print("PASS test_decode_file_written_from_long_hex_matches")


def test_decode_bad_input_is_clean_error() -> None:
    rc, out, err = run(["decode", "this-is-not-hex-and-not-a-file"])
    assert rc == 2, rc
    assert out == "", out
    assert err.startswith("ascent decode: "), err
    assert "Traceback" not in err, err
    # Odd-length hex is also a clean error, not a ValueError traceback.
    rc, out, err = run(["decode", "ABC"])
    assert rc == 2 and out == "" and err.startswith("ascent decode: "), (rc, out, err)
    # --file on a missing path reports the OSError instead of raising.
    rc, out, err = run(["decode", "--file", "/nonexistent/ascent/path.bin"])
    assert rc == 2 and out == "" and err.startswith("ascent decode: "), (rc, out, err)
    print("PASS test_decode_bad_input_is_clean_error")


def test_decode_empty_role_args_json_safe() -> None:
    rc, out, err = run(["decode", "--json", EMPTY_ROLE_HEX])
    assert rc == 0, (rc, err)
    events = json.loads(out)
    assert len(events) == 1, events
    ev = events[0]
    assert ev["kind"] == "agent" and ev["opcode_name"] == "ROLE", ev
    assert ev["name"] == "" and ev["name_bytes"] == "" and ev["rest_hex"] == "", ev
    assert "rest" not in ev, ev
    # Human-readable path prints the empty name rather than failing.
    rc, out, err = run(["decode", EMPTY_ROLE_HEX])
    assert rc == 0, (rc, err)
    assert out.rstrip("\n") == "AGENT: ROLE name= ", repr(out)
    print("PASS test_decode_empty_role_args_json_safe")


def main_tests() -> int:
    test_hello_hex_exceeds_name_max()
    test_decode_long_hex_argument()
    test_decode_long_hex_stdin()
    test_decode_long_hex_json()
    test_decode_very_long_hex()
    test_decode_hex_with_whitespace_and_prefixes()
    test_decode_file_path_still_detected()
    test_decode_file_written_from_long_hex_matches()
    test_decode_bad_input_is_clean_error()
    test_decode_empty_role_args_json_safe()
    print("ALL CLI DECODE INPUT TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_tests())
