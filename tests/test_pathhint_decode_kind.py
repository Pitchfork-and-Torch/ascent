#!/usr/bin/env python3
"""pathhint --decode must reject non-PATHHINT ASCENT streams."""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ascent.cli import main  # noqa: E402


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


def test_decode_hello_is_rejected() -> None:
    rc, hello, _ = _run(["hello"])
    assert rc == 0
    hx = hello.strip()
    rc, out, err = _run(["pathhint", "--decode", hx])
    assert rc == 2, (rc, out, err)
    assert "no PATHHINT unit" in err
    assert out == ""
    print("PASS test_decode_hello_is_rejected")


def test_decode_real_pathhint_ok() -> None:
    rc, hx, err = _run(["pathhint", "--path-id", "66", "--cap-bps", "50000000"])
    assert rc == 0, err
    wire = hx.strip().splitlines()[0]
    rc, out, err = _run(["pathhint", "--decode", wire])
    assert rc == 0, err
    assert '"kind": "pathhint"' in out or '"kind":"pathhint"' in out
    assert "TEXT" not in out
    print("PASS test_decode_real_pathhint_ok")


if __name__ == "__main__":
    test_decode_hello_is_rejected()
    test_decode_real_pathhint_ok()
    print("ALL pathhint decode-kind tests passed")
