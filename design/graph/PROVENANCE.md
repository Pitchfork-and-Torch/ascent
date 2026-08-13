# ASCENT SPEC.md graph provenance

Synthesizer node merge for `.\SPEC.md` (v1.0 Draft).
ASCII hyphen only. Conflict rule: judge locks > planes-encoding (wire) > agents-multimodal (opcodes) > deep-space (D profile) > governance (A/B/D/F prose).

## Artifacts

| Path | Contribution |
|------|----------------|
| `artifacts/wave1-judge.md` | Winner name ASCENT + expansion; locked manifesto; parse law; plane table P0-P10+; profile labels 7/E/D/A; hybrid note (A heritage, B agents, C ECC, D DEF); syntax sketches for agent/MM/crypto/DEF/P9; Wave 2 handoffs; rejected alternatives. |
| `artifacts/wave2-planes-encoding.md` | Normative freeze for section C: allocation philosophy; eternal parse law; P1/P2 lead tables; private plane rules; ASCENT-V clean-room primary + UTF-8 bridge; BE integers; BOM/signature table; STRICT_C1 vs LEGACY_PASS; skip-unknown + max-frame caps; efficiency; conformance checklist. |
| `artifacts/wave2-agents-multimodal.md` | Agent frame wire + opcode registry 0x0001-0x0007; fence escape `C1 1B <byte>`; ROLE/TOOL/THINK/HANDOFF/CAP/SAFETY semantics; MM marker `9D 4D` kinds/flags/hash; reassembly caps; P7 `9C 4B` quantum-safe control; injection model; Hello Universe seed bytes (synthesizer completed hash + 42-byte ref). |
| `artifacts/wave2-deep-space.md` | ASCENT-D profile: P9 outer frame layout and sync; ECC families RS/LDPC by profile; erase-on-fail parity; compress->CRC->ECC layering; HE=1 no-compress; ref-only MM preference; DEF-kernel/beacon/session lock; D constants. |
| `artifacts/wave2-governance-origin.md` | Sections A/B/D/F source prose: official name polish; origin story; letter-by-letter acronym; AJMG/ISO/IETF maintainers; add-process table; compat guarantees; PQ mid-cruise freeze; DEF bootstrap circularity; trademark/registry; profile + semver rules. |
| `graph/RUBRIC.md` | Pass bar (ASCII 20/20, total >= 85); anti-patterns rejected in synthesis (no 0-127 break, no surrogate emoji, concrete self-desc and MM syntax). |

## Upstream (not re-read by synthesizer; cited via judge)

| Path | Role |
|------|------|
| `artifacts/wave1-invent-A.md` | ASCENT name + heritage (via judge) |
| `artifacts/wave1-invent-B.md` | Agent opcodes + skip-unknown (via judge) |
| `artifacts/wave1-invent-C.md` | Deep-space ECC + binary markers (via judge) |
| `artifacts/wave1-invent-D.md` | DEF self-map + content-addressed MM (via judge) |

## Resolutions applied

- Agent args max: **8192** wire (agents-multimodal) over planes soft 4096.
- MM/crypto tags: `0x9D 0x4D` and `0x9C 0x4B` (explicit ASCII M/K) aligned with judge `M`/`K` sketches.
- D MAX_UNIT **8192**; erase unit on parity fail (deep-space lock).
- Native wire **ASCENT-V**; UTF-8 bridge only (planes-encoding lock).
- Hello Universe: sample media SHA-256 of `ASCENT Hello Universe sample media v1`; ref `cid:sha256:aabbccddeeff0011223344556677889` (42 B).

## Graph path

wave1 inventors (A/B/C/D) -> name-judge -> wave2 specialists (planes-encoding, agents-multimodal, deep-space, governance-origin) -> synthesizer -> `SPEC.md`.
