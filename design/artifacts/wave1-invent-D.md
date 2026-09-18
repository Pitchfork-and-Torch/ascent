# invent-D | wave=1 | axis=self-describing-meta

**node:** invent-D  
**wave:** 1  
**axis:** self-describing / meta-recursive / elegant engineering

---

## NAME

**MIRROR** - Meta-Inclusive Recursive Representation of Orthogonal Ranges

**Manifesto:** One byte stream that is both the text and the complete, versioned definition of how to read every later byte, including itself.

---

## Why MIRROR beats obvious alternatives

- **UTF-8 / UTF-Next:** names the past (Unicode text) not the job (self-hosting control + data + agents).
- **ASCII-2 / Extended ASCII:** implies a patch; MIRROR is a closed formal object that *contains* ASCII as plane 0.
- **SELF / BOOT / META:** too vague; MIRROR states the property: the encoding reflects its own grammar.
- **SAGE / OMEGA:** marketing; MIRROR is an engineering metaphor (fixed control mirrors variable data; the standard mirrors itself).

Pronounceable, one word, no trademark collision with charsets of record.

---

## High-level plane map

Philosophy: **fixed-width control planes** (predictable parse, machine-first) + **variable-width data planes** (human text, scripts, media refs) + **one escape lattice** so every extension is addressable without surrogate hacks.

| Plane | Role | Rough layout |
|-------|------|----------------|
| P0 | Classic ASCII | `0x00-0x7F` - bit-identical to 1963/ANSI X3.4 |
| P1 | Fixed control nucleus | `0x80-0x9F` reserved as **C1-MIRROR**: frame, version, plane-select, ECC mode, agent fence (never printable data) |
| P2 | Structured escapes | Lead `0xC0-0xCF` + fixed trailers: length-prefixed opcodes for crypto, multimodality, quantum-safe wrappers |
| P3 | Self-map / registry | Canonical block that embeds the **definition document** (see self-description hook) |
| P4-P7 | Living + historical scripts | Variable-width (UTF-8-like continuation discipline: high bit set, no overlongs); scripts get stable block IDs, not surrogate pairs |
| P8 | Emoji / symbols | Scalar codepoints, one logical unit per glyph sequence start; ZWJ sequences as data, not surrogates |
| P9 | Agent / LLM control | In-band tokens with hard fences (open/close) so they never collide with text planes |
| P10 | Multimodal stream | Typed refs + optional inline payloads (media, tensor stubs, file digests) |
| P11 | Crypto control | Quantum-safe algorithm IDs, nonce/tag frames, key-commit markers (control only; keys stay out of band by default) |
| P12 | Deep-space profile | Low-entropy alphabet option + strong ECC frames (see risks) |
| P13+ | Private / experimental | Require explicit plane-select; must not redefine P0-P3 |

Parse rule (elegance): **if byte < 0x80, it is ASCII forever.** If byte in C1-MIRROR, switch control state. Else enter variable-width data with declared plane from last plane-select (default P4 after BOM-equivalent).

---

## How ASCII is embedded

Codepoints and bytes `0x00` through `0x7F` are **identical in value, width, and meaning** to classic 7-bit ASCII (NUL through DEL). No overlong encoding of ASCII is legal in any data plane. Existing 7-bit and UTF-8-pure-ASCII files are valid MIRROR documents with zero transformation. All new capability is gated through `0x80+` and length-prefixed frames so a pure-ASCII reader can still extract the P0 subset by masking high bytes or treating them as opaque.

---

## Agent control + multimodal markers (minimal sketch)

**Agent fence (fixed control, P1/P2):**

```
0x9A                 # AGENT_OPEN  (C1-MIRROR)
0xC1 0x01 <ver>      # ESC_AGENT, version byte
... payload (UTF-8-compatible text or structured ops) ...
0x9B                 # AGENT_CLOSE
```

Payload must not contain unescaped `0x9A`/`0x9B`; escape with `0xC1 0x1B <byte>`.

**Multimodal ref (streamable, no surrogate):**

```
0xC2                 # ESC_MM
0x01                 # kind: REF (0x02 = INLINE payload follows)
0x04                 # type: image/png (registry ID)
0x20                 # 32-byte digest length
<32-byte hash>       # content-addressed
0x00 0x10            # optional size hint (u16 BE) or 0xFFFF unknown
```

Inline mode: same header then `u32` length + bytes; deep-space profile may force REF-only.

**LLM special tokens:** same AGENT frame with `ver` bit marking `role=system|tool|user` so one stream carries chat, tools, and documents without out-of-band side channels.

---

## Self-description hook

A conforming **boot document** is a valid MIRROR stream that:

1. Starts with P0 ASCII header line: `MIRROR/1.0` (printable, greppable).
2. Emits `PLANE_SELECT(P3)` then a **DEF** frame (`0xC0` + schema version + length) whose body is the full normative grammar: plane map, opcode registry, ECC modes, version history as an append-only table.
3. Optionally signs the DEF body under P11 (crypto control) so agents can pin "this stream's law."
4. May re-emit an updated DEF mid-stream only with `VERSION_BUMP` control; readers keep the first DEF unless an explicit upgrade policy allows the later one.

Thus: **one file can be the standard, the test vectors, and a sample text corpus.** Spec PDFs become derived views; the encoding is the source of truth. Version history lives inside DEF as ordered records `(epoch, semver, hash-of-prior-DEF, changelog-ascii)`.

Mathematical cleanliness: control lengths are fixed or uvarint-declared once; data planes share one continuation rule; no dual coding of the same scalar except forbidden overlongs (reject).

---

## Risks / open questions (for later specialists)

1. **C1 clash:** Bytes `0x80-0x9F` are used as Windows-1252 printables in the wild; pure "byte-identical ASCII files" are safe, but Latin-1-as-binary blobs may misparse. Need a profile flag: `STRICT_C1` vs `LEGACY_PASS`.
2. **UTF-8 coexistence:** Should P4-P7 be wire-compatible with UTF-8 for the Unicode scalar subset, or a cleaner from-scratch varint? Compatibility wins adoption; cleanliness wins proofs. Decide in wave 2.
3. **Agent injection:** In-band fences are a security surface; need mandatory escaping rules + optional out-of-band channel IDs for high-assurance agents.
4. **DEF size vs deep-space:** Full self-description is large; deep-space profile needs a **minimal kernel DEF** (parse tables only) plus deferred full registry by content hash (P10 REF).
5. **ECC choice:** Reed-Solomon vs LDPC vs fountain codes for P12; who owns the code alphabet when entropy is minimized?
6. **Quantum-safe agility:** Algorithm ID registry must allow deprecation without breaking historical signed DEFs (append-only + multi-sig?).
7. **Emoji stability:** One scalar per "user-perceived character" is underspecified; align with UAX #29 or define MIRROR grapheme clusters in DEF.
8. **Governance:** Who may publish plane IDs after P13? IANA-like registry vs hash-named private planes only.

---

**Ship note:** MIRROR prioritizes *one parse law, self-hosted*, fixed control + variable data, and ASCII as the eternal fixed point of the lattice.
