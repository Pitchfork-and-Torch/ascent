# ASCENT 1.0 - One-page abstract

**Status:** Release Candidate (1.0.0-rc1)  
**Category:** Proposed encoding / stream grammar  
**Obsoletes:** (none - coexists with ASCII and Unicode)  
**Requires:** Bit-identical classic 7-bit ASCII on `0x00-0x7F`

---

## Abstract

ASCENT (ASCII Successor with Compatible Encoding of Named Text) is a byte-stream encoding and control grammar for text, agent directives, multimodal references, quantum-safe control envelopes, and optional deep-space error-corrected frames. Every byte less than `0x80` is classic 7-bit ASCII, bit-identical to ANSI X3.4 / ISO 646 IRV, forever. Higher capability is introduced only through fixed C1 fences, length-prefixed frames, and a clean-room variable-width data plane (ASCENT-V) that does not use UTF-16 surrogate pairs and does not dual-stack UTF-8 on the native wire.

ASCENT is not a marketing rename of Unicode. It is a wire contract: greppable pure-ASCII subsets remain greppable; agents and media share one stream; unknown length-declared units are skipped under caps; deep-space profile D hard-erases units that fail outer parity rather than inventing mojibake. SkyPulse PATHHINT (appendix) is LEO path foresight for usable application goodput; it does not increase Starlink physical RF Mbps.

---

## 1. Motivation

1. Preserve the 1963 identity plane that still underpins shebangs, SMTP 7-bit paths, and greppers.  
2. Carry LLM/agent control tokens in-band without overloading printable prose.  
3. Attach multimodal refs and short payloads with content hashes.  
4. Ship quantum-safe control sequences with an append-only algorithm registry and no silent downgrade.  
5. Support long-haul links with an outer ECC profile (RS default, optional LDPC).  
6. Remain self-describing: a valid document can embed plane maps, registries, and version history.

---

## 2. Design laws

| Law | Statement |
|-----|-----------|
| Identity | `byte < 0x80` => classic ASCII, width 1, forever |
| No overlongs | Multi-byte forms MUST NOT encode `0x00-0x7F` |
| No surrogates | One scalar = one unit; emoji via scalar sequences (incl. ZWJ) |
| Fixed control | P1 fences + P2 length-declared headers; big-endian integers |
| Skip-unknown | Unknown unit with valid length => skip under max-frame |
| Erase-on-fail (D) | Outer parity/CRC fail => discard unit, hunt next sync |

---

## 3. Plane map (summary)

| ID | Role | Leads / notes |
|----|------|----------------|
| P0 | ASCII identity | `0x00-0x7F` |
| P1 | C1 controls | `0x80-0x9F`; `9A/9B` agent; `9C` crypto; `9D` MM |
| P2 | Escape nucleus | `C0` DEF, `C1` AGENT_OP, `CF` private |
| P3/P4 | Scripts / emoji | ASCENT-V V-width |
| P5-P8 | Agent, MM, PQ, self-map | Frame grammars |
| P9 | Deep-space outer | Sync `D5 E5 C0 DE` |
| P10+ | Private | Cannot redefine P0-P2 |

---

## 4. Profiles

- **ASCENT-7** - pure ASCII identity  
- **ASCENT-E** - Earth interchange (full control)  
- **ASCENT-E-LEO** - usage of E: SkyPulse PATHHINT, light integrity on LEO IP (not a parse fork)  
- **ASCENT-D** - deep-space (RS(255,223) default, MAX_UNIT 8192, ref-prefer MM)  
- **ASCENT-A** - archive / DEF-heavy  

Profile is orthogonal to semver: e.g. `ASCENT-E/1.0`.

---

## 5. Control sketches

```
Agent:  9A | C1 ver opcode flags len args | 9B
MM:     9D 4D kind codec flags hash-alg hash len [body]
Crypto: 9C 4B alg kid nonce ct
DEF:    "ASCENT/1.0\n" | C0 schema len body
OuterD: D5 E5 C0 DE | profile | ecc | len | unit | parity
```

Initial agent opcodes: STOP, ROLE, TOOL, THINK, HANDOFF, CAP, SAFETY.

SkyPulse PATHHINT (P2 `0xC5` schema `0x01`): path_id, next_capacity, freeze_ms, confidence, ttl, optional obstruction/elev. Fail-closed skip. Optional P9 wrap. Usage profile ASCENT-E-LEO vs ASCENT-D.

Registered companion encryption suite **AEGIR** (design/AEGIR.md) occupies P7 alg ids `0x0100-0x010B` (suite envelope, dual-core hybrid KEM, AEAD, HBOP outer pad, IMS seal, DEMO). No silent downgrade; keys out of band.

---

## 6. Compatibility guarantees

1. Pure classic ASCII files are valid ASCENT-7 / identity subset of E.  
2. P0 never remapped; IDs never recycled (append-only deprecation).  
3. Major version only when control grammar breaks.  
4. PQ algorithm freezes allowed for mid-cruise probes.  
5. UTF-8 bridge is import/export only; native wire is ASCENT-V.

---

## 7. Governance (sketch)

ASCENT Joint Maintenance Group (AJMG) dual-liaises ISO/IEC JTC 1 and IETF. Registries public and secret-free. Neither track may weaken P0-P2 parse law alone.

---

## 8. Example

Stream begins `ASCENT/1.0\nHello, Universe.\n`, then agent ROLE=guide (`9A C1 01 00 02 ... 9B`), then multimodal REF (`9D 4D ...`). See SPEC.md section E and `ref/ascent_decode.py`.

---

## 9. Status of this memo

Informative one-page face for the normative draft at `SPEC.md`. Not an IETF RFC number assignment. Ship when implementers stop arguing about the stairs and start climbing them.

---

*ASCENT - keep every classic ASCII byte sacred.*
