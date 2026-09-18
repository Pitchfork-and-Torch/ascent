#!/usr/bin/env python3
"""ascent decode must reject empty/whitespace input (exit 2)."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ascent.cli import main  # noqa: E402


def run(argv: list[str], stdin: str | None = None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    saved = sys.stdin
    try:
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = main(argv)
    finally:
        sys.stdin = saved
    return rc, out.getvalue(), err.getvalue()


def test_decode_empty_arg() -> None:
    rc, out, err = run(["decode", ""])
    assert rc == 2, (rc, err)
    assert "empty" in err.lower() or "non-empty" in err.lower(), err
    assert out == ""
    print("PASS test_decode_empty_arg")


def test_decode_whitespace_stdin() -> None:
    rc, out, err = run(["decode"], stdin="   \n\t  ")
    assert rc == 2, (rc, err)
    assert "empty" in err.lower() or "non-empty" in err.lower(), err
    print("PASS test_decode_whitespace_stdin")


def test_decode_empty_file() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    try:
        rc, out, err = run(["decode", "--file", path])
        assert rc == 2, (rc, err)
        assert "empty" in err.lower(), err
        print("PASS test_decode_empty_file")
    finally:
        Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_decode_empty_arg()
    test_decode_whitespace_stdin()
    test_decode_empty_file()
    print("ALL PASS")
