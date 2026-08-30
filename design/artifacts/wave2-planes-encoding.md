# planes-encoding | wave 2

**node:** planes-encoding  
**wave:** 2  
**parent:** name-judge  
**standard:** ASCENT  

Normative freeze for SPEC.md section C. Wave1 judge hybrid. ASCII hyphen only.

---

## C.1 Allocation philosophy

1. Control is fixed-width or length-declared; data is variable-width.
2. **P0 eternal:** `0x00-0x7F` never change meaning or width.
3. One encoding per scalar on the native wire; overlongs illegal forever.
4. No UTF-16 surrogates: each scalar is one unit (1-4 bytes). ZWJ/combiners are scalar sequences.
5. Unknown + declared length => skip under max-frame; unknown without length => hard-fault (strict).
6. Private planes cannot redefine P0-P2.

---

## C.2 Eternal parse law

```
if byte < 0x80:
    emit classic 7-bit ASCII (ANSI X3.4 / ISO 646 IRV), width 1
    never recombine into a multi-byte unit
else:
    enter ASCENT extension grammar
```

**Overlong ban:** Any multi-byte encoding of a `0x00-0x7F` scalar is illegal; decoders MUST reject. No best-effort overlong ASCII.

**Alias ban:** Multi-byte forms MUST NOT change the pure-ASCII subset when those bytes are read as single units. Greppers and 7-bit paths stay correct on P0.

---

## C.3 Plane map freeze (P0-P10)

| Plane | ID | Role | Wire / lead |
|-------|-----|------|-------------|
| Identity | **P0** | Classic ASCII | `0x00-0x7F` single-byte forever |
| C1 fixed | **P1** | Non-text stream controls | `0x80-0x9F`; never printable |
| Escape nucleus | **P2** | Length-prefixed opcodes / DEF | Lead `0xC0-0xCF` + header + body |
| Scripts | **P3** | Living + historical scripts | V-width data units |
| Emoji/symbols | **P4** | Pictographs; ZWJ sequences | Same V-width family as P3 |
| Agent | **P5** | LLM/OS in-band control | P1 fences + P2 agent frames |
| Multimodal | **P6** | Refs, inline, chunks | P1 `0x9D` + header + body/ref |
| Crypto | **P7** | Quantum-safe control | P1 `0x9C` + alg/kid/nonce/ct; keys OOB |
| Self-map | **P8** | DEF, registries, history | P0 header and/or `0xC0` DEF |
| Deep outer | **P9** | ECC wrap | Sync `0xD5 0xE5 0xC0 0xDE` + profile + params + len + unit + parity |
| Private | **P10+** | Experimental | Plane-select only; no P0-P2 redefine |

### C.3.1 P1 assigned (initial)

| Byte | Name | Role |
|------|------|------|
| `0x80-0x99` | Reserved CTL | Stream state, soft-sync, profile |
| `0x9A` | AGENT_OPEN | P5 fence open |
| `0x9B` | AGENT_CLOSE | P5 fence close |
| `0x9C` | CRYPTO_MARK | P7 start |
| `0x9D` | MM_MARK | P6 start |
| `0x9E` | PLANE_SELECT | Arg: plane id `u8` |
| `0x9F` | PAD | Ignore in text assembly |

Unknown P1: skip-1 or hard-fault (`unk_c1=skip|fault`).

### C.3.2 P2 leads (initial)

| Lead | Name | Header (all BE) |
|------|------|-----------------|
| `0xC0` | DEF | `schema:u8` `len:u32be` `body` |
| `0xC1` | AGENT_OP | `ver:u8` `opcode:u16be` `flags:u8` `len:u16be` `args` |
| `0xC2` | VERSION_BUMP | `len:u16be` `body` |
| `0xC3` | REGISTRY_DELTA | `len:u32be` `body` |
| `0xC4-0xCE` | Reserved | Skip-by-length when header present |
| `0xCF` | PRIVATE_OP | `plane:u16be` `len:u32be` `body` (P10+) |

### C.3.3 Private planes (P10+)

Hash-named default (`plane_id` from hash of `org||name`, salt on collision); interchange embeds DEF slice. Optional public block `0x8000-0x8FFF` via maintainers. MUST declare `fixed|vwidth`, `max_unit`, `skip`. MUST NOT remap `0x00-0x7F` or P1/P2 leads.

---

## C.4 Classic ASCII embedding

Wire `0x00-0x7F` = classic ASCII (NUL-DEL), bit-identical. Pure-ASCII files are valid **ASCENT-7** and profile E with no header. Shebangs, SMTP 7-bit, greppers remain correct on P0. ASCII is only single-byte P0.

---

## C.5 Encoding path: clean-room primary

### C.5.1 Decision: **ASCENT-V** native; UTF-8 via bridge only

Native ASCENT does **not** share UTF-8 lead/continuation discipline.

**Rationale:** Judge freeze places P1 on `0x80-0x9F` and P2 on `0xC0-0xCF`, which collide with UTF-8 continuations and 2-byte leads. Native dual-stack would demote C1/agent fences or need stateful exceptions that break range-to-plane proofs. Clean-room keeps fixed control, skip-by-length, and P9 sync simple.

### C.5.2 ASCENT-V data units (P3/P4)

| Lead class | Range | Form | Use |
|------------|-------|------|-----|
| Cont-only | `0xA0-0xAF` | Illegal as lead | Optional nibble cont (DEF) |
| Cont-only | `0xB0-0xBF` | Illegal as lead | Primary continuation (64 vals) |
| 2-byte data | `0xD0-0xDF` | lead + 1 cont | Small script/symbol scalars |
| 3-byte data | `0xE0-0xEF` | lead + 2 cont | Core scripts / most emoji bases |
| 4-byte data | `0xF0-0xF4` | lead + 3 cont | Rare scripts, high emoji |
| Ext select | `0xF5` | `0xF5` `plane:u8` + data | Force P3/P4/private data |
| Reserved | `0xF6-0xFF` | Illegal open data lead | Strict hard-fault |

**Continuation:** Trailers MUST be `0xB0-0xBF` (or DEF-enabled `0xA0-0xAF`). MUST NOT be `0x00-0x9F` or `0xC0-0xCF`.

**Scalars:** P8 DEF registry. Bootstrap maps `0x000080..0x10FFFF` excluding surrogates `0xD800-0xDFFF`. No surrogate units on wire. ZWJ/VS/skin = separate scalars (P4). Graphemes are display/agent layer only.

**Default data plane:** P3. `0xF5 0x04` selects P4 until next select. Control select may use `0x9E`.

### C.5.3 Migration: ASCENT-UTF8 bridge

1. **Import:** strict UTF-8 -> map `U+0080+` to ASCENT-V, `U+0000-7F` to P0; strip BOM.
2. **Export:** Unicode-mapped ASCENT-V -> strict UTF-8; strip or side-channel controls per profile.
3. `EF BB BF` is bridge-only, never ASCENT signature; native encoders MUST NOT write it.
4. Corpora enter via bridge; agents/ECC stay ASCENT-native.

---

## C.6 Endianness

Multi-byte integers are **big-endian** (`u16be`/`u32be`/`u64be`) for lengths, opcodes, codec/alg/plane ids in P2/P6/P7/P9. No little-endian fields in 1.0. P0 and ASCENT-V data are stream order only.

---

## C.7 BOM / signature

| Signature | Bytes | Meaning |
|-----------|-------|---------|
| Text magic | `ASCENT/1.0` + LF | P0 greppable self-desc |
| DEF | `0xC0` + schema + len + body | P8 self-map |
| Deep sync | `0xD5 0xE5 0xC0 0xDE` | P9 outer unit |
| UTF-8 BOM | `EF BB BF` | Bridge hint only |

ASCENT-7 needs no magic. Prefer magic + DEF for self-desc. `allow_utf8_bom=1` may treat leading BOM as bridge input; STRICT native otherwise rejects illegal lead.

---

## C.8 STRICT_C1 vs LEGACY_PASS

| Flag | Behavior for `0x80-0x9F` |
|------|--------------------------|
| **STRICT_C1** (default E/D/A) | Always P1, never printable. Unknown: skip-1 or fault. Fences `0x9A-0x9F` always active. |
| **LEGACY_PASS** (import only) | Lone C1 may pass as opaque legacy **except** recognized `0x9A-0x9D`/P2 still control. New content MUST NOT rely on it. Export normalizes to P0 + ASCENT-V. |

DEF or magic pins STRICT_C1. LEGACY_PASS only by explicit option. Profile D is always STRICT_C1.

---

## C.9 Skip-unknown and max-frame

Unknown unit with declared `len` => advance `len` after header (unless `strict_unknown=fault`). Truncation => hard-fault. Unknown P1 => skip 1 (or fault). Bad data lead/cont => hard-fault (strict); soft Earth may U+FFFD-map if DEF defines it; never invent P0 aliases.

| Context | Soft | Hard |
|---------|------|------|
| P2 body | 16384 | 65535 |
| DEF `0xC0` | 1 MiB | 16 MiB |
| MM inline P6 | 16 MiB | 256 MiB / unit |
| Crypto ct P7 | - | 16 MiB |
| P9 outer (D) | 64 KiB | profile |
| Agent args | 4096 | 65535 |
| Private `0xCF` | as DEF | as DEF |

DEF may lower caps, not raise past hard. Over soft: reject or allow-large flag. Over hard: always reject.

---

## C.10 Efficiency

P0=1 byte/char; P1=1-byte fences/pads; P2 fixed headers (optional `flags.pad4`). P3/P4 min 2 bytes for non-ASCII (no 1-byte Latin-1; avoids C1 clash). CJK/common target 3-byte (`0xE0-0xEF`); emoji base often 3-byte; ZWJ = N scalars. Prefer `0x9F` pad over stretching data. vs UTF-8: slightly less dense on some 2-byte Latin; wins non-colliding C1/P2. Min: P0=1, P1=1, P2>=1+header, P3/P4>=2, P6/P7/P9 per headers.

---

## C.11 Conformance checklist

P0 eternal + overlong ban; C.3 plane/leads; ASCENT-V primary + UTF-8 bridge only; BE headers; no UTF-8 BOM signature; STRICT_C1 default / LEGACY_PASS import-only; no surrogates; skip-by-length + max-frame; private cannot redefine P0-P2.

---

*End planes-encoding wave2. Merge into SPEC.md section C.*
