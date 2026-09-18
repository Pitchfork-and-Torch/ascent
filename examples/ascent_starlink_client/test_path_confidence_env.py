#!/usr/bin/env python3
"""ASCENT_PATH_CONFIDENCE=0 must stay 0.0 (not coerced by `or 0.5`)."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import daemon  # noqa: E402


class FakeDish:
    obstruction = None
    elev_deg = None
    state = "SKIP"


class TestPathConfidenceEnv(unittest.TestCase):
    def test_zero_confidence_honored(self) -> None:
        env = {
            "ASCENT_PATH_CONFIDENCE": "0",
            "ASCENT_PATH_CAP_BPS": "1000",
            "ASCENT_FREEZE_MS": "100",
            "ASCENT_PATH_TTL_MS": "1000",
            "ASCENT_PATH_ID": "7",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            # Clear obstruction overrides that would rewrite confidence.
            for k in ("ASCENT_OBSTRUCTION", "ASCENT_DISH_STATE"):
                os.environ.pop(k, None)
            _blob, hint = daemon.make_pathhint(FakeDish())
        self.assertIsNotNone(hint)
        self.assertEqual(hint.confidence, 0.0)

    def test_unset_defaults_to_half(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ASCENT_PATH_CONFIDENCE", None)
            os.environ.pop("ASCENT_OBSTRUCTION", None)
            os.environ.pop("ASCENT_DISH_STATE", None)
            _blob, hint = daemon.make_pathhint(FakeDish())
        self.assertIsNotNone(hint)
        self.assertEqual(hint.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
