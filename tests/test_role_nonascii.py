"""ROLE frame must raise AscentCodecError for non-ASCII / control names (not UnicodeEncodeError)."""
from __future__ import annotations

import subprocess
import sys
import unittest

from ascent import AscentCodecError, encode_text


class RoleNonAsciiTests(unittest.TestCase):
    def test_encode_text_non_ascii_role(self) -> None:
        with self.assertRaises(AscentCodecError):
            encode_text("hi", role="café")

    def test_encode_text_role_with_whitespace(self) -> None:
        with self.assertRaises(AscentCodecError):
            encode_text("hi", role="bad role")

    def test_cli_encode_non_ascii_role_exit_2(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "ascent", "encode", "hi", "--role", "café"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("role must be a non-empty ASCII name", proc.stderr)
        self.assertNotIn("UnicodeEncodeError", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
