# ASCENT

**ASCII Successor with Compatible Encoding of Named Text**

[![Live](https://img.shields.io/badge/live-ascent.jonbailey.xyz-00e5a0)](https://ascent.jonbailey.xyz/)
[![PyPI](https://img.shields.io/pypi/v/ascent-wire?color=00e5a0)](https://pypi.org/project/ascent-wire/)
[![npm](https://img.shields.io/npm/v/ascent-wire?color=3dd6ff)](https://www.npmjs.com/package/ascent-wire)
[![Release](https://img.shields.io/github/v/release/Pitchfork-and-Torch/ascent?color=7c5cff)](https://github.com/Pitchfork-and-Torch/ascent/releases/latest)
[![CI](https://github.com/Pitchfork-and-Torch/ascent/actions/workflows/ci.yml/badge.svg)](https://github.com/Pitchfork-and-Torch/ascent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-1e2a36)](LICENSE)

> Keep every classic ASCII byte sacred. Ascend the rest without burning the stairs.

<p align="center">
  <a href="https://ascent.jonbailey.xyz/">
    <img src="docs/ascent-infographic.png?v=3.0.0" alt="ASCENT Nexus v3.0.0 Crystal Wire infographic: parse law, SkyPulse PATHHINT, dual-mode Starlink usable-goodput, Wire Lab 3.0, agents, multimodal, ASCENT-D" width="100%">
  </a>
</p>

<p align="center"><em>ASCENT Nexus v3.0.0 Crystal Wire architecture card · <a href="docs/ascent-infographic.png">PNG</a> · <a href="docs/ascent-infographic.jpg">JPG</a> · <a href="https://ascent.jonbailey.xyz/infographic.png?v=3.0.0">live</a></em></p>

---

## What it is

ASCENT is a **wire encoding and control grammar** for text, agents, multimodal references, quantum-safe control envelopes, and deep-space ECC profiles. It is a future-facing successor spirit to classic 7-bit ASCII (ANSI X3.4 / 1963):

| Pillar | Contract |
|--------|----------|
| **Eternal identity** | Every byte less than `0x80` is classic ASCII, bit-identical, forever |
| **Agent-native** | Fenced control tokens (`ROLE`, `TOOL`, `THINK`, ...) share the stream with prose |
| **Multimodal** | Content-addressed refs and length-declared media units (no surrogate-pair hacks) |
| **Quantum-safe control** | Append-only algorithm registry; no silent downgrade |
| **Deep-space (ASCENT-D)** | Outer ECC frames; parity fail erases the unit (no mojibake) |
| **SkyPulse (PATHHINT)** | LEO path foresight for **usable session bandwidth**; fail-closed skip; not an RF Mbps upgrade |
| **Self-describing** | A valid document can carry plane maps, registries, and version history |

This is **not** "Unicode but better." It is a stream contract greppers can still trust.

## Live

**https://ascent.jonbailey.xyz/**

**ASCENT Nexus Wire Lab 3.0 Crystal Wire** (architecture card **v3.0.0**): dual text/hex live sync, command palette, mission HUD, stream timeline, agent + multimodal composers, **SkyPulse PATHHINT** panel (LEO-IP vs D), ASCENT-D bit-error / erase-on-fail simulator, AEGIR sketch, interactive eleven-plane explorer, 2-minute tour, SPEC try-this, and codegen. Dual-mode Grok+Starlink plan (CLOUD / EDGE / QUEUE) with **usable session bandwidth** honesty. Sacred P0 meter and Hello, Universe sample included.

Follow: [@suddenlyjon](https://x.com/suddenlyjon)

| Surface | Version |
|---------|---------|
| Nexus site / architecture card | **3.0.0** |
| SPEC | **1.0.0-rc1** (+ SkyPulse appendix) |
| Frozen Cont packing (ASCENT-V) | Cont `0xA0-0xBF` (5-bit) |
| Python package (PyPI) | **ascent-wire 2.1.0** |
| JS package (npm) | **ascent-wire 2.1.0** |

## Quick start

### Browser

Open the live site and click **Decode Hello, Universe**.

### Python reference decoder

```bash
python ref/ascent_decode.py --self-test
python ref/ascent_decode.py --hello
python ref/ascent_decode.py examples/hello-universe.ascent.bin --json
```

### Golden tests (shared codec)

```bash
# from repo root
set PYTHONPATH=ref
python tests/test_ascent_codec.py
```

Shared library: `ref/ascent_codec.py` (ASCENT-7, frozen ASCENT-V, UTF-8 MM bridge). Lab non-ASCII modes on the live site: **ASCENT-V** / **UTF-8 bridge** / **ASCENT-7 reject**.

### ASCENT-D + real satellite lab (ISS)

P9 outer frame with RS(255,223), erase-on-fail. Uses **public Celestrak ISS TLE** and a LEO BER channel model. **No RF transmit.**

```bash
set PYTHONPATH=ref
python tests/test_ascent_d_satellite.py
```

Module: `ref/ascent_d.py`.

### SkyPulse PATHHINT (usable session bandwidth)

Fail-closed path hint for Starlink-class IP. Improves **usable session bandwidth**
and continuity under LEO. **Does not raise RF Mbps.** Not a bare "bandwidth upgrade."

```bash
set PYTHONPATH=ref
python tests/test_skypulse.py
python -m ascent pathhint --profile ASCENT-E-LEO
python examples/ascent_starlink_client/daemon.py --pathhint
```

Docs: [docs/SKYPULSE.md](docs/SKYPULSE.md). Profile note: **ASCENT-E-LEO** (light CRC or short RS, no full P9 on interactive IP) vs **ASCENT-D** (spool/deep-space). Ship order: SPEC appendix + goldens + wire 2.1.0, then Wire Lab, then publish codec, LeoAware later.

### AEGIR (ASCENT-native encryption companion)

**AEGIR** is a first-class P7 encryption suite: dual-core hybrid KEM (ML-KEM + X25519), History-Bound Outer Pad, agent-fenced ceremony (ROLE/CAP), Ghost Continuum IMS seals, and append-only registry (no silent downgrade). Design: [design/AEGIR.md](design/AEGIR.md). Registry seeds: SPEC.md C.3.3.

```bash
set PYTHONPATH=ref
python ref/aegir_sketch.py --self-test
python ref/aegir_sketch.py --list-algs
python tests/test_aegir.py
# optional DCH-768 (requires: pip install kyber-py)
python ref/aegir_sketch.py --self-test
```

## Parse law

```
if byte < 0x80:
    emit classic 7-bit ASCII (width 1)
    never recombine into a multi-byte unit
else:
    enter ASCENT extension grammar
```

Overlong encodings of `0x00-0x7F` are **illegal forever**.

## Hello, Universe (132 bytes)

One valid ASCENT-E stream:

1. Greppable header `ASCENT/1.0`
2. Human text `Hello, Universe.`
3. Agent frame `ROLE=guide`
4. Multimodal `REF` with SHA-256 binding

Agent frame alone:

```
9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B
```

Full hex map: [SPEC.md section E](SPEC.md).

## Profiles

| Profile | Role |
|---------|------|
| `ASCENT-7` | Pure classic ASCII identity |
| `ASCENT-E` | Earth / general interchange |
| `ASCENT-E-LEO` | Usage of E: PATHHINT + light integrity on LEO IP |
| `ASCENT-D` | Deep-space outer ECC |
| `ASCENT-A` | Archive / self-description heavy |

## Install (Python package)

Full guide: [INSTALL.md](INSTALL.md) · **PyPI:** https://pypi.org/project/ascent-wire/

```bash
pip install ascent-wire
ascent self-test
ascent encode --header --role guide "Hello, Universe."
python -m ascent hello
```

Package name: **`ascent-wire`** (import `ascent`). Requires Python 3.10+. Optional: `pip install "ascent-wire[deep-space]"`.

### Golden lock (JS must match Python)

```bash
set PYTHONPATH=ref
python tests/test_ascent_codec.py
node tests/run_js_lock.js
python tests/test_js_python_lock.py
python tests/test_skypulse.py
```

## Agent loops

See [docs/AGENT-LOOP.md](docs/AGENT-LOOP.md) for ROLE/TOOL/THINK/SAFETY recipes and [docs/SPEC-FREEZE-1.0-RC.md](docs/SPEC-FREEZE-1.0-RC.md) for the 1.0-RC freeze checklist.

## Repository layout

```
SPEC.md                 Normative draft (sections A-F)
ABSTRACT.md             One-page abstract
ascent/                 Installable package (ascent-wire)
pyproject.toml          Packaging
docs/                   Infographic, SkyPulse, agent-loop, SPEC freeze RC
ref/ascent_decode.py    Earth-profile reference decoder
ref/ascent_skypulse.py  PATHHINT policy + LEO-IP vs D integrity
ref/aegir_sketch.py     AEGIR encrypt/decrypt sketch (DEMO + optional DCH-768)
examples/               Canonical .bin samples (incl. skypulse-pathhint)
site/public/            Live Nexus Wire Lab 2.0 (Cloudflare Pages)
tests/                  Python goldens + JS lock
design/                 Non-normative design provenance (incl. AEGIR)
assets/masters/         Source OG + infographic masters
```

| File | Purpose |
|------|---------|
| [SPEC.md](SPEC.md) | Full normative draft |
| [ABSTRACT.md](ABSTRACT.md) | RFC-style one-pager |
| [docs/ascent-infographic.png](docs/ascent-infographic.png) | Architecture infographic v2.1.0 (SkyPulse; PNG may still show 2.0.3 until regen) |
| [docs/SKYPULSE.md](docs/SKYPULSE.md) | SkyPulse PATHHINT what/why/non-claims |
| [docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md](docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md) | Grok over ASCENT over Starlink design package |
| [docs/ORBITSTACK-LEOAWARE-BRIDGE.md](docs/ORBITSTACK-LEOAWARE-BRIDGE.md) | How LeoAware should consume PATHHINT |
| [docs/ascent-starlink-interface.png](docs/ascent-starlink-interface.png) | Horizontal ASCENT x Starlink interface map (2400x1100) |
| [examples/ascent_starlink_client/](examples/ascent_starlink_client/) | Dual-mode CLI skeleton (cloud / edge / queue) |
| [docs/AGENT-LOOP.md](docs/AGENT-LOOP.md) | LLM agent loop guide |
| [docs/SPEC-FREEZE-1.0-RC.md](docs/SPEC-FREEZE-1.0-RC.md) | 1.0-RC freeze checklist |
| [ref/ascent_decode.py](ref/ascent_decode.py) | Python decoder |
| [ref/aegir_sketch.py](ref/aegir_sketch.py) | AEGIR encryption sketch |
| [design/AEGIR.md](design/AEGIR.md) | AEGIR companion design (full) |
| [examples/hello-universe.ascent.bin](examples/hello-universe.ascent.bin) | Sample stream |
| [examples/agent-loop-demo.ascent.bin](examples/agent-loop-demo.ascent.bin) | Multi-frame agent sample |
| [examples/hello-universe-aegir.ascent.bin](examples/hello-universe-aegir.ascent.bin) | Encrypted Hello (AEGIR-DEMO) |

## License

MIT - see [LICENSE](LICENSE).

## Support

GitHub Issues only. No personal contact required.

---

*Pitchfork and Torch · open standards experiments*
