#!/usr/bin/env python3
# Run JS golden lock via node; fail if node missing or tests fail.
# py -3 tests/test_js_python_lock.py
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("SKIP test_js_python_lock: node not on PATH")
        return 0
    script = ROOT / "tests" / "run_js_lock.js"
    r = subprocess.run([node, str(script)], cwd=str(ROOT))
    if r.returncode != 0:
        print("FAIL test_js_python_lock")
        return 1
    print("PASS test_js_python_lock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
