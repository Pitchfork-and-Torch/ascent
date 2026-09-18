#!/usr/bin/env python3
# ASCENT CLI must report codec errors cleanly (no Traceback) and exit 2.
# python tests/test_cli_codec_errors.py

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "ascent", *argv],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_encode_reject_non_ascii_clean() -> None:
    rc, out, err = run(["encode", "--mode", "reject", "café"])
    assert rc == 2, (rc, out, err)
    assert out == ""
    assert err.startswith("ascent encode: "), err
    assert "Traceback" not in err
    print("PASS test_encode_reject_non_ascii_clean")


def test_decode_truncated_agent_clean() -> None:
    rc, out, err = run(["decode", "9AC1"])
    assert rc == 2, (rc, out, err)
    assert out == ""
    assert err.startswith("ascent decode: "), err
    assert "Traceback" not in err
    print("PASS test_decode_truncated_agent_clean")


def test_pathhint_bad_confidence_clean() -> None:
    rc, out, err = run(["pathhint", "--confidence", "2"])
    assert rc == 2, (rc, out, err)
    assert out == ""
    assert err.startswith("ascent pathhint: "), err
    assert "Traceback" not in err
    print("PASS test_pathhint_bad_confidence_clean")


def main() -> int:
    test_encode_reject_non_ascii_clean()
    test_decode_truncated_agent_clean()
    test_pathhint_bad_confidence_clean()
    print("ALL CLI CODEC ERROR TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
