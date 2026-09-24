# Delay Hull

**Nexus:** 4.0.0  
**Wire:** ascent-wire 2.2.0  
**SPEC:** 1.0.0-rc1 plus this appendix (also in SPEC.md)  
**Cont / P9:** frozen

ASCII hyphens only.

## What it is

A delayed session is one request document and one response document. The head of each document is a TURN unit, lead `0xC6`, schema `0x01`. Correlation is `session` + `turn` + `corr`. A duplicate correlation is a no-op, not a second TOOL. Lifetime expiry drops the document.

The contact lab is an injected clock and a list of windows `[open, close)`. It is not a Bundle Protocol Agent. It is not an ASCENT convergence layer. CI does not install uD3TN, ION, or HDTN.

## What it is not

- Interactive Grok across a multi-hour gap
- A faster Starlink radio
- BP/LTP on the Starlink IP path
- A thaw of Cont `0xA0-0xBF` or of P9
- SPEC 1.0.0 final
- AEGIR production, LDPC, or a LeoAware cook

Starlink IP stays **ASCENT-E-LEO** (PATHHINT CRC or short RS, not both, no full P9). The delay spool may use **ASCENT-D**. Do not stack CRC and RS on the same bytes as a requirement.

## Honesty on errors

PATHHINT and TURN use a CRC. A flipped CRC byte erases the unit.

ASCENT-D is RS(255,223). One symbol error is corrected. Erase happens when the outer decode fails (more errors than the code can correct, or a broken frame). The contact lab smash uses 17 trailing symbol errors so the spool erases and emits no TOOL.

## Old decoders

ascent-wire 2.1.0 and earlier hard-fault on lead `0xC6`. They never implemented skip for that reserved lead. 2.2.0 skips an unknown TURN schema by length. Do not tell a 2.1.0 caller that the unit is ignored.

## CHUNK

SPEC C.3.2 was already normative. 2.2.0 adds goldens: reorder by `chunk_index`, two stream ids, duplicate index is malformed, a gap still open at END is incomplete, missing END discards the buffer and does not treat the hash as valid. The browser reassembly matches that structure. sha-256 FINAL_HASH is checked in the Python golden.

## Run

```bash
set PYTHONPATH=ref
python tests/test_delay_hull.py
node tests/run_js_lock.js
```

Lab: https://ascent.jonbailey.xyz/#delay-hull  
The panel is sim.
