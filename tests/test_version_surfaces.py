#!/usr/bin/env python3
# Advertised version surfaces must stay honest and split.
# Do not bump these constants unless the change earns that number.
# python tests/test_version_surfaces.py
# ASCII hyphens only.

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SPEC = "1.0.0-rc1"
NEXUS = "3.0.0"
WIRE = "2.1.0"

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def test_package_versions() -> None:
    pyproject = _read("pyproject.toml")
    assert f'version = "{WIRE}"' in pyproject, pyproject[:200]
    pkg = json.loads(_read("packages/ascent-js/package.json"))
    assert pkg["name"] == "ascent-wire"
    assert pkg["version"] == WIRE
    init = _read("ascent/__init__.py")
    assert f'__version__ = "{WIRE}"' in init
    js_index = _read("packages/ascent-js/index.js")
    assert f'version: "{WIRE}"' in js_index
    print("PASS test_package_versions")


def test_spec_header() -> None:
    spec = _read("SPEC.md")
    assert f"**Version:** {SPEC}" in spec
    assert f"**Nexus / architecture card:** {NEXUS} Crystal Wire" in spec
    assert f"**Wire packages (PyPI/npm ascent-wire):** {WIRE}" in spec
    assert "**Nexus / architecture card:** 2.1.0" not in spec
    print("PASS test_spec_header")


def test_readme_and_install() -> None:
    readme = _read("README.md")
    assert f"| Nexus site / architecture card | **{NEXUS}** |" in readme
    assert f"| SPEC | **{SPEC}**" in readme
    assert f"**ascent-wire {WIRE}**" in readme
    assert "Live Nexus Wire Lab 2.0" not in readme
    assert "PNG may still show 2.0.3" not in readme
    inst = _read("INSTALL.md")
    assert f"**SPEC:** {SPEC}" in inst
    assert f"**Nexus:** {NEXUS} Crystal Wire" in inst
    assert f"**ascent-wire:** {WIRE}" in inst
    assert "Nexus / packages:** 2.1.0" not in inst
    assert "In-repo 2.1.0" not in inst
    print("PASS test_readme_and_install")


def test_llms_and_site() -> None:
    llms = _read("site/public/llms.txt")
    assert f"Architecture card: **v{NEXUS}**" in llms
    assert f"SPEC: **{SPEC}**" in llms
    assert f"ascent-wire {WIRE} published" in llms
    assert "after publish" not in llms
    assert "Which version should I cite?" in llms
    assert "Does ASCENT unlock OrbitStack dual-gate?" in llms
    html = _read("site/public/index.html")
    assert f"v{NEXUS}" in html
    assert f">{WIRE}<" in html or f">{WIRE}</strong>" in html
    assert "publish gated" not in html
    assert "Which version should I cite?" in html
    assert "Does ASCENT unlock OrbitStack dual-gate?" in html
    assert '"softwareVersion": "3.0.0"' in html
    print("PASS test_llms_and_site")


def test_docs_current_card() -> None:
    docs = _read("docs/README.md")
    assert f"architecture **v{NEXUS}**" in docs
    assert "architecture **v2.1.0**" not in docs
    sky = _read("docs/SKYPULSE.md")
    assert f"ascent-wire **{WIRE}**" in sky
    assert f"Nexus architecture card **{NEXUS}** Crystal Wire" in sky
    bridge = _read("docs/ORBITSTACK-LEOAWARE-BRIDGE.md")
    assert f"wire **{WIRE}**" in bridge
    assert f"Nexus architecture card **{NEXUS}** Crystal Wire" in bridge
    print("PASS test_docs_current_card")


def test_dual_gate_stays_fenced() -> None:
    bridge = _read("docs/ORBITSTACK-LEOAWARE-BRIDGE.md")
    assert "**Does not** implement, enable, or claim dual-gate wins in this repo." in bridge
    assert 'Do not market "ASCENT unlocks dual-gate"' in bridge
    html = _read("site/public/index.html")
    assert "This lab does not implement, enable, or claim dual-gate wins." in html
    llms = _read("site/public/llms.txt")
    assert "This repo does not implement, enable, or claim dual-gate wins." in llms
    # Do not introduce closed-write VELA into this repo.
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".git/") or "/__pycache__/" in rel:
            continue
        if rel == "tests/test_version_surfaces.py":
            continue
        if path.suffix.lower() not in {".md", ".html", ".txt", ".js", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "closed-write VELA" in text or "closed write VELA" in text:
            hits.append(rel)
    assert not hits, hits
    print("PASS test_dual_gate_stays_fenced")


def test_surfaces_are_distinct() -> None:
    assert SPEC != NEXUS
    assert SPEC != WIRE
    assert NEXUS != WIRE
    print("PASS test_surfaces_are_distinct")


def main() -> int:
    test_package_versions()
    test_spec_header()
    test_readme_and_install()
    test_llms_and_site()
    test_docs_current_card()
    test_dual_gate_stays_fenced()
    test_surfaces_are_distinct()
    print("ALL VERSION SURFACE TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
