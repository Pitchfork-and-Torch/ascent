"""ascent decode/pathhint: invalid hex must exit 2 with a clean message."""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ascent.cli import main  # noqa: E402


def _run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def test_decode_odd_length_hex() -> None:
    code, out, err = _run(["decode", "abc"])
    assert code == 2
    assert out == ""
    assert "invalid hex" in err
    assert "Traceback" not in err


def test_decode_non_hex_chars() -> None:
    code, out, err = _run(["decode", "zz"])
    assert code == 2
    assert "invalid hex" in err


def test_pathhint_decode_invalid_hex() -> None:
    code, out, err = _run(["pathhint", "--decode", "gg"])
    assert code == 2
    assert "invalid hex" in err
    assert "Traceback" not in err


def test_decode_missing_file() -> None:
    code, out, err = _run(["decode", "--file", "/no/such/ascent-input.bin"])
    assert code == 2
    assert "cannot read" in err
    assert "Traceback" not in err


if __name__ == "__main__":
    test_decode_odd_length_hex()
    test_decode_non_hex_chars()
    test_pathhint_decode_invalid_hex()
    test_decode_missing_file()
    print("PASS test_cli_invalid_hex")
