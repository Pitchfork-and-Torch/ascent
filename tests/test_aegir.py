#!/usr/bin/env python3
# AEGIR golden + property tests. Run from repo root with PYTHONPATH=ref.
# ASCII hyphens only.

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "ref"
sys.path.insert(0, str(REF))

import aegir_sketch as aegir  # noqa: E402

GOLDEN_JSON = ROOT / "tests" / "aegir_vectors.json"
GOLDEN_BIN = ROOT / "examples" / "hello-universe-aegir.ascent.bin"


class TestAegirRegistry(unittest.TestCase):
    def test_registered_names(self):
        self.assertEqual(aegir.ALG_NAMES[0x0100], "AEGIR-SUITE-1")
        self.assertEqual(aegir.ALG_NAMES[0x0101], "AEGIR-DCH-KEM-768")
        self.assertEqual(aegir.ALG_NAMES[0x010B], "AEGIR-DEMO-X25519-GCM")
        self.assertEqual(aegir.ALG_NAMES[0x010A], "AEGIR-IMS-SEAL")


class TestAegirDemo(unittest.TestCase):
    def test_round_trip(self):
        stream, info = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO)
        pt = aegir.decrypt_stream(stream)
        self.assertEqual(pt, aegir.PLAINTEXT_HELLO)
        self.assertTrue(stream.startswith(aegir.SUITE_MAGIC))
        self.assertNotIn(aegir.PLAINTEXT_HELLO, stream[len(aegir.SUITE_MAGIC) :])
        self.assertEqual(info["mode"], "demo")

    def test_deterministic_stable(self):
        s1, i1 = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, deterministic=True)
        s2, i2 = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, deterministic=True)
        self.assertEqual(s1, s2)
        self.assertEqual(i1["freeze_hash"], i2["freeze_hash"])
        self.assertEqual(aegir.decrypt_stream(s1), aegir.PLAINTEXT_HELLO)

    def test_wrong_ephys_fails(self):
        stream, _ = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, deterministic=True)
        with self.assertRaises(ValueError):
            aegir.decrypt_stream(stream, e_phys=bytes([0x00]) * 32)

    def test_greppable_p0(self):
        stream, _ = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, deterministic=True)
        self.assertTrue(stream.startswith(b"ASCENT/1.0\n"))
        self.assertIn(b"AEGIR/1.0\n", stream[:32])
        # sacred P0 bytes of magic are all < 0x80
        for b in aegir.SUITE_MAGIC:
            self.assertLess(b, 0x80)

    def test_ims_frame(self):
        fr = aegir.build_ims_frame(aegir.sha256(b"s"), aegir.sha256(b"e"))
        self.assertEqual(fr[:2], b"\x9c\x4b")
        alg = int.from_bytes(fr[2:4], "big")
        self.assertEqual(alg, aegir.ALG_AEGIR_IMS_SEAL)


class TestAegirGolden(unittest.TestCase):
    def test_golden_matches_file(self):
        if not GOLDEN_JSON.is_file():
            self.skipTest("aegir_vectors.json missing; run aegir_sketch --write-golden")
        data = json.loads(GOLDEN_JSON.read_text(encoding="utf-8"))
        built = aegir.make_golden_demo()
        self.assertEqual(built["wire_hex"], data["wire_hex"])
        self.assertEqual(built["freeze_hash_hex"], data["freeze_hash_hex"])
        self.assertEqual(built["wire_len"], data["wire_len"])
        wire = bytes.fromhex(data["wire_hex"])
        self.assertEqual(aegir.decrypt_stream(wire), aegir.PLAINTEXT_HELLO)

    def test_golden_bin(self):
        if not GOLDEN_BIN.is_file():
            self.skipTest("hello-universe-aegir.ascent.bin missing")
        wire = GOLDEN_BIN.read_bytes()
        self.assertTrue(wire.startswith(aegir.SUITE_MAGIC))
        self.assertEqual(aegir.decrypt_stream(wire), aegir.PLAINTEXT_HELLO)


@unittest.skipUnless(aegir.has_ml_kem(), "kyber_py not installed")
class TestAegirDch768(unittest.TestCase):
    def test_dch_round_trip(self):
        stream, info = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, use_dch768=True)
        self.assertEqual(info["mode"], "dch-768")
        pt = aegir.decrypt_stream(stream, mlkem_dk=info["_mlkem_dk"])
        self.assertEqual(pt, aegir.PLAINTEXT_HELLO)
        # no silent demo fallback without key
        with self.assertRaises(ValueError):
            aegir.decrypt_stream(stream)

    def test_wrong_mlkem_fails(self):
        stream, info = aegir.encrypt_stream(aegir.PLAINTEXT_HELLO, use_dch768=True)
        _ek, wrong_dk = aegir._mlkem768_keygen()
        with self.assertRaises(Exception):
            aegir.decrypt_stream(stream, mlkem_dk=wrong_dk)


if __name__ == "__main__":
    # regenerate golden if missing
    if not GOLDEN_JSON.is_file() or not GOLDEN_BIN.is_file():
        g = aegir.make_golden_demo()
        GOLDEN_JSON.write_text(json.dumps(g, indent=2) + "\n", encoding="utf-8", newline="\n")
        GOLDEN_BIN.write_bytes(bytes.fromhex(g["wire_hex"]))
        print(f"wrote {GOLDEN_JSON} and {GOLDEN_BIN}")
    raise SystemExit(unittest.main(verbosity=2))
