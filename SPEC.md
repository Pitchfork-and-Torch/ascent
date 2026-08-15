# ASCENT - Official Specification (v1.0 Release Candidate)

**Status:** Release Candidate for implementer freeze  
**Version:** 1.0.0-rc1  
**Nexus / architecture card:** 2.1.0 (SkyPulse)  
**Freeze companions:** `docs/SPEC-FREEZE-1.0-RC.md`, `tests/freeze_vectors.json`, `node tests/run_js_lock.js`  
**Parse law (eternal):** if a byte is less than `0x80`, it is classic 7-bit ASCII, bit-identical, forever.

**RC rule:** Locked wire forms in the freeze companions MUST NOT change without a major version bump. Editorial prose may still clarify until 1.0.0 final.

---

## A. Name, acronym, manifesto

**NAME:** ASCENT  
**Pronunciation:** /uh-SENT/  
**Public expansion:** ASCII Successor with Compatible Encoding of Named Text  
**Committee title (heritage):** American Standard Code for Extended Named Text

**Manifesto.** Keep every classic ASCII byte sacred, then ascend scripts, agents, media refs, crypto control, and deep-space links into one self-describing stream - fixed-width control for machines, variable-width data for humans, never remapping `0x00-0x7F`.

ASCENT is not "Unicode but better." It is a wire contract: identity for greppers and shebangs, planes for living text, fences for agents, markers for multimodal work, envelopes for quantum-safe control, and an outer ECC frame for the subset that leaves the atmosphere. The name is English on purpose. Operators remember *ascent*. Committees may keep the longer title for stationery.

**Profiles (normative labels):**

| Label | Role |
|-------|------|
| `ASCENT-7` | Identity only: pure classic ASCII |
| `ASCENT-E` | Earth / general interchange |
| `ASCENT-E-LEO` | Usage profile of E: SkyPulse PATHHINT, light integrity (CRC or short RS) on LEO IP (not a parse-law fork) |
| `ASCENT-D` | Deep-space (strong outer ECC, long sync) |
| `ASCENT-A` | Archive / self-description heavy |

Profile is orthogonal to semver: `ASCENT-E/1.0` is Earth profile of major 1.

---

## B. Origin Story

*Minutes of the Ad Hoc Joint Working Group on Compatible Text Encoding, late 2020s into the early 2030s. Coffee appears more often than quorum.*

The Committee notes that ANSI X3.4-1963 served teletypes, email, and the accidental Internet with distinction. Later decades produced approximately seventeen mutually incompatible notions of "extended ASCII," a script repertoire larger than any code page, agents that demand the same byte stream as prose, and deep-space links whose bit-error rates make UTF-8 look like a parlor game.

It was moved and carried, without enthusiasm, that a successor shall exist; that it shall not be named "ASCII2"; and that it shall not force operators to recompile every shebang and SMTP path on Earth.

Working title ASCENT survived three rejected expansions, two trademark searches, and one argument about whether "ascent" means progress or merely altitude. The minority preferred a purely recursive acronym and was filed under hobbies.

Design law on first reading: **if a byte is less than `0x80`, it is classic 7-bit ASCII, bit-identical, forever.** Novelty begins only at or above that threshold, or behind length-prefixed frames that never alias into the sacred range. The Chair observed this is the only guarantee implementers will actually remember.

Later sessions fixed planes P0-P10+, agent fences, multimodal markers, quantum-safe envelopes, self-describing DEF documents, and a deep-space outer frame for the subset that launches hardware. Hybrid synthesis retained ASCENT heritage, agent opcodes with skip-unknown discipline, outer ECC and hard-fail parity, and DEF self-maps with open/close fences and content-addressed multimodal refs.

The Committee does not claim ASCENT ends encoding history. It claims greppers may continue to work.

Adjourned. Next meeting subject to launch windows and ISO calendar collisions.

---

## C. Technical overview

ASCENT is a **stream of units**. A unit is either a single P0 byte, a fixed P1 control byte, a length-declared P2 (or P6/P7) frame, a variable-width data scalar (P3/P4), or (under profile D) a whole logical payload wrapped by a P9 outer ECC frame.

**Eternal parse law:**

```
if byte < 0x80:
    emit classic 7-bit ASCII (ANSI X3.4 / ISO 646 IRV), width 1
    never recombine into a multi-byte unit
else:
    enter ASCENT extension grammar
```

**Overlong ban:** any multi-byte encoding of a `0x00-0x7F` scalar is illegal; decoders MUST reject. No best-effort overlong ASCII. **No UTF-16 surrogates** on the wire: each scalar is one unit (1-4 bytes). ZWJ, variation selectors, and skin tones are separate scalars in sequence.

**Endianness:** all multi-byte integers in headers (lengths, opcodes, codec/alg/plane ids) are **big-endian** (`u16be` / `u32be` / `u64be`). No little-endian fields in 1.0.

**Unknown handling:** unknown unit with declared length => **skip-by-length** under max-frame caps; unknown without length => hard-fault in strict profiles. Truncation is always a hard-fault.

### C.1 Codepoint allocation philosophy (planes, ranges, reserved blocks)

1. Control is fixed-width or length-declared; data is variable-width.  
2. **P0 eternal:** `0x00-0x7F` never change meaning or width.  
3. One encoding per scalar on the native wire; overlongs illegal forever.  
4. No surrogate pair dependency for any repertoire unit.  
5. Private planes cannot redefine P0-P2.  
6. Fixed control for machines; variable data for humans; never alias extension bytes into 0-127.

| Plane | ID | Role | Wire / lead |
|-------|-----|------|-------------|
| Identity | **P0** | Classic ASCII | `0x00-0x7F` single-byte forever |
| C1 fixed | **P1** | Non-text stream controls | `0x80-0x9F`; never printable data |
| Escape nucleus | **P2** | Length-prefixed opcodes / DEF | Lead `0xC0-0xCF` + header + body |
| Scripts | **P3** | Living + historical scripts | ASCENT-V variable-width |
| Emoji/symbols | **P4** | Pictographs; ZWJ sequences | Same V-width family as P3 |
| Agent | **P5** | LLM/OS in-band control | P1 fences + P2 agent frames |
| Multimodal | **P6** | Refs, inline, chunks | P1 `0x9D` + header + body/ref |
| Crypto | **P7** | Quantum-safe control | P1 `0x9C` + alg/kid/nonce/ct; keys OOB |
| Self-map | **P8** | DEF, registries, history | P0 header and/or `0xC0` DEF |
| Deep outer | **P9** | ECC wrap | Sync `0xD5 0xE5 0xC0 0xDE` + profile + params + len + unit + parity |
| Private | **P10+** | Experimental | Plane-select only; no P0-P2 redefine |

**P1 assigned (initial):**

| Byte | Name | Role |
|------|------|------|
| `0x80-0x99` | Reserved CTL | Stream state, soft-sync, profile |
| `0x9A` | AGENT_OPEN | P5 fence open |
| `0x9B` | AGENT_CLOSE | P5 fence close |
| `0x9C` | CRYPTO_MARK | P7 start |
| `0x9D` | MM_MARK | P6 start |
| `0x9E` | PLANE_SELECT | Arg: plane id `u8` |
| `0x9F` | PAD | Ignore in text assembly |

**P2 leads (initial):**

| Lead | Name | Header (all BE) |
|------|------|-----------------|
| `0xC0` | DEF | `schema:u8` `len:u32be` `body` |
| `0xC1` | AGENT_OP | `ver:u8` `opcode:u16be` `flags:u8` `len:u16be` `args` |
| `0xC2` | VERSION_BUMP | `len:u16be` `body` |
| `0xC3` | REGISTRY_DELTA | `len:u32be` `body` |
| `0xC4` | Reserved | Skip-by-length when header present |
| `0xC5` | SKYSTATE | `schema:u8` `len:u16be` `body` (PATHHINT schema `0x01`; see appendix SkyPulse) |
| `0xC6-0xCE` | Reserved | Skip-by-length when header present |
| `0xCF` | PRIVATE_OP | `plane:u16be` `len:u32be` `body` (P10+) |

**Private planes (P10+):** hash-named default (`plane_id` from hash of `org||name`, salt on collision); interchange embeds a DEF slice. Optional public block `0x8000-0x8FFF` via maintainers. MUST declare `fixed|vwidth`, `max_unit`, `skip`. MUST NOT remap `0x00-0x7F` or P1/P2 leads.

**STRICT_C1 vs LEGACY_PASS:** default for E/D/A is **STRICT_C1** (`0x80-0x9F` always control, never printable). **LEGACY_PASS** is import-only for opaque legacy C1 bytes; recognized fences and P2 still control. Profile D is always STRICT_C1.

### C.2 How classic ASCII is embedded

Wire `0x00-0x7F` equals classic ASCII (NUL through DEL), bit-identical to ANSI X3.4 / ISO 646 IRV. Pure-ASCII files are valid **ASCENT-7** and valid profile E with no header. Shebangs (`#!`), SMTP 7-bit paths, and greppers remain correct on the P0 subset. Classic ESC `0x1B` remains legacy VT-safe; ASCENT native control uses P1 fences and P2 leads, not a hostile takeover of ESC.

ASCII is **only** single-byte P0. Multi-byte forms MUST NOT change the pure-ASCII subset when those bytes are read as single units. That is the identity contract.

### C.3 Control tokens, multimodal markers, quantum-safe sequences

#### C.3.1 Agent control (P5)

```
0x9A                                              # AGENT_OPEN  (P1)
0xC1 <ver:u8> <opcode:u16be> <flags:u8> <len:u16be> <args:len>
0x9B                                              # AGENT_CLOSE (P1)
```

- OPEN and CLOSE are required. Nested agent frames are forbidden in v1.  
- `ver` initial `0x01`. Unknown ver: skip-by-length if `len` readable; else hard-fault.  
- Unknown opcode: skip if length-valid and CRITICAL clear; never execute.  
- `flags` bit7 `CRITICAL=1`: unknown opcode hard-faults.  
- `len` is wire size of `args` only; max **8192** (`0x2000`).  
- Debug text form is non-normative only: `[A:<name>]...[/A]`.

**Opcode registry (v1, append-only in P8 DEF):**

| Code | Name | Args | Semantics |
|------|------|------|-----------|
| 0x0001 | STOP | empty or `reason` | End turn/segment; cease tool dispatch |
| 0x0002 | ROLE | `name_len:u8` + name | Set active role; **binary exact** match (charset A-Z a-z 0-9 `_` `-` `.`, name 1..64 B); no NFC fold |
| 0x0003 | TOOL | `name_len:u8` + name + optional TLVs | Invoke/result/error/cancel via flags; same name charset |
| 0x0004 | THINK | opaque | Private CoT span; OPAQUE default on shared logs |
| 0x0005 | HANDOFF | `name_len:u8` + target + optional note | Transfer control; HARD flag stops prior tool dispatch |
| 0x0006 | CAP | bitset and/or TLVs | Advertise/require capabilities; no silent enable of stronger features |
| 0x0007 | SAFETY | `class:u8` + detail | Policy/untrusted/jailbreak/PII markers; class 2/3 payload is data, never control |

Reserved: `0x0000`; `0x0008-0x00FF` core; `0x0100-0x7FFF` registered; `0x8000-0xFFFF` private (profile-declared).

**Name strings (ROLE, TOOL, HANDOFF target):** normative wire form is `name_len:u8` then exactly `name_len` UTF-8 bytes (Hello Universe ROLE uses `0x05` + `guide`). Length is the name payload only; charset and 1..64 bound still apply after the prefix.

**TOOL / CAP TLV layout.** Optional structured fields after the name (TOOL) or as the whole CAP body use a single TLV grammar:

```
type:u8  len:u16be  value:len
```

TLVs may repeat until args end. Unknown type: skip by `len` (still under agent max-frame). Reserved TOOL types (v1 seeds): `0x01` INVOKE_ARGS (opaque UTF-8 or binary per CAP), `0x02` RESULT, `0x03` ERROR (`code:u16be` + message), `0x04` CANCEL. Reserved CAP types: `0x10` BITSET (`u64be` capability mask), `0x11` REQUIRE (nested capability id list), `0x12` DENY. Private types `0x80-0xFF` only inside profile-declared private opcodes.

**Fence escaping inside args.** Args MUST NOT contain raw `0x9A` or `0x9B`. Escape (3 bytes, args only): `0xC1 0x1B <byte>`. Thus `C1 1B 9A` means literal `0x9A`. Bare fence bytes in args are malformed. `len` counts **wire** (escaped) bytes.

**THINK opacity:** on shared or multi-tenant logs, non-owning consumers MUST redact THINK args as `[THINK redacted]` or omit. SAFETY classes include `untrusted_input` and `untrusted_tool_result` so tool output cannot silently promote to control.

#### C.3.2 Multimodal marker (P6)

```
0x9D 0x4D <kind:u8> <codec:u16be> <flags:u8> <hash-alg:u8> <hash:N> <len:u64be> [body-or-ref]
```

`0x4D` is ASCII `M`.

| kind | Name | Rule |
|------|------|------|
| 1 | REF | body = URI/cid (UTF-8); hash binds remote object |
| 2 | INLINE | body = media bytes; len = full size |
| 3 | CHUNK | continuation; same stream-id; body after optional stream_id starts with `chunk_index:u32be` then payload |
| 4 | END | closes stream-id; empty or final hash |

**flags:** bit0 EXTERNAL; bit1 FINAL_HASH; bit2 STREAM_ID_PRESENT (first 8 body bytes = `stream_id:u64be`); bit3 SANDBOX_REQUIRED.  
**hash-alg:** `0=none` (forbidden for INLINE on D; discouraged on E); `1=sha-256` N=32; `2=sha-512` N=64; `3=blake3-256` N=32. Hash is over **logical media** after reassembly, not framing.  
Unknown codec: skip-by-length; do not decode. Profile D prefers **ref-only**; large INLINE is an Earth convenience.

**Bootstrap codec ids (registry seeds, append-only):**

| codec:u16be | Name |
|-------------|------|
| `0x0000` | reserved |
| `0x0001` | text/plain; charset=utf-8 |
| `0x0002` | application/json |
| `0x0003` | image/png |
| `0x0004` | image/jpeg |
| `0x0005` | application/octet-stream |
| `0x0006` | audio/wav |
| `0x0007` | video/mp4 |
| `0x0008-0x00FF` | core reserved |
| `0x0100-0x7FFF` | registered |
| `0x8000-0xFFFF` | private (profile-declared) |

**CHUNK reassembly (normative):** receivers order payload by `chunk_index` (ascending, dense preferred; gaps allowed until END). Reassembly buffer is keyed by `stream_id` when STREAM_ID_PRESENT is set; without stream_id, only a single open CHUNK stream is legal per consumer context. **Timeout** on an open stream is optional (profile or local policy; D SHOULD set a mission timer). Missing kind=4 END before timeout, consumer close, or hard max open streams => **incomplete stream**: discard buffer, do not emit partial media as complete, do not treat FINAL_HASH as valid. Duplicate `chunk_index` is malformed. Hash (when present) is computed only after END and full reassembly.

#### C.3.3 Quantum-safe control (P7)

```
0x9C 0x4B <alg:u16be> <kid-len:u8> <kid> <nonce-len:u8> <nonce> <ct-len:u32be> <ct>
```

`0x4B` is ASCII `K`. Algorithm IDs come only from the P8 PQ registry. Unknown alg: do not decrypt; skip-by-length if `ct-len` valid. **No silent downgrade.** Keys stay out-of-band by default; `kid` names the key material. Never embed private keys. ASCENT-D may freeze the alg set mid-cruise (see F).

**Bootstrap PQ alg ids (registry seeds, append-only):**

| alg:u16be | Name | Role |
|-----------|------|------|
| `0x0000` | reserved | - |
| `0x0001` | ML-KEM-768 | KEM |
| `0x0002` | ML-KEM-1024 | KEM |
| `0x0003` | ML-DSA-65 | signature |
| `0x0004` | ML-DSA-87 | signature |
| `0x0005` | SLH-DSA-128f | signature |
| `0x0006` | SLH-DSA-192f | signature |
| `0x0007-0x00FF` | core reserved | - |
| `0x0100-0x7FFF` | registered | - |
| `0x8000-0xFFFF` | private | profile-declared |

**Registered AEGIR suite ids (append-only, first public registration block):**

Companion design: `design/AEGIR.md` (ASCENT Encryption with Ghost-Immune Resilience). These ids inhabit P7; they do not redefine P0-P2. Full suite-1 sealed profiles use Dual-Core Hybrid (AND composition) and History-Bound Outer Pad; `0x010B` is CI/demo only and is **not** Mythos-grade.

| alg:u16be | Name | Role |
|-----------|------|------|
| `0x0100` | AEGIR-SUITE-1 | Suite descriptor / versioned envelope |
| `0x0101` | AEGIR-DCH-KEM-768 | Hybrid KEM container (ML-KEM-768 + X25519) |
| `0x0102` | AEGIR-DCH-KEM-1024 | Hybrid KEM high |
| `0x0103` | AEGIR-AEAD-AES256-GCMSIV | Bulk AEAD |
| `0x0104` | AEGIR-AEAD-CHACHA20POLY | Bulk AEAD alternate |
| `0x0105` | AEGIR-HBOP-SHA512 | Outer pad KDF family |
| `0x0106` | AEGIR-SIG-HYBRID-65 | ML-DSA-65 + Ed25519 |
| `0x0107` | AEGIR-SIG-SLH-128f | Archive signature |
| `0x0108` | AEGIR-DSR-STATE | Ratchet state blob (encrypted) |
| `0x0109` | AEGIR-MPR-V1 | Manifold poison decoy (non-key) |
| `0x010A` | AEGIR-IMS-SEAL | Immune Merkle seal record |
| `0x010B` | AEGIR-DEMO-X25519-GCM | Demo classical path only (CI vectors) |
| `0x010C-0x01FF` | AEGIR reserved | future suite cores |
| `0x0200-0x7FFF` | other registered | public process |

#### C.3.4 Self-desc (P8) and injection model

Greppable bootstrap:

```
ASCENT/1.0\n                    # P0 header
0xC0 <schema:u8> <len:u32be> <DEF body>
```

**Shipped `schema:u8` values (normative seeds; unknown with length is skip or hard-fault per profile):**

| schema | Name | Body role |
|--------|------|-----------|
| `0x00` | reserved | illegal open |
| `0x01` | KERNEL | plane map + registry kernel (opcodes, MM kinds, codecs, PQ algs, ECC table, caps) |
| `0x02` | ANNEX_HASH | full prose annex: content hash of normative text (or full embed under profile A) |
| `0x03` | HISTORY | history-only delta (append records; no plane rewrite) |
| `0x04-0x7F` | registered | future public schemas |
| `0x80-0xFF` | private | profile-declared; must not redefine P0-P2 shell |

DEF body (schema-dependent) carries plane map, escape grammar, opcode/kind/alg/codec tables, content hash of normative prose (or full text in profile A), and append-only history. **History record tuple (normative fields):** `(semver, date:u32be YYYYMMDD or ISO-UTF-8 short form, parent-hash, delta-hash, hash-alg:u8)` where `hash-alg` uses the same ids as P6 (`1=sha-256`, `2=sha-512`, `3=blake3-256`; `0=none` illegal for history). Default pin: first DEF wins unless upgrade policy allows mid-stream `VERSION_BUMP`. Optional P7 signature over DEF.

**Injection model:**

1. Control executes only inside complete `0x9A`..`0x9B`, `0x9D M`, or `0x9C K` units. P0-P4 prose never runs as opcodes.  
2. Fences are mandatory. High-assurance deployments MAY require channel IDs on CRITICAL frames.  
3. Untrusted tool or MM bytes that *look* like fences remain **data** until a trusted boundary re-encodes a legal frame.  
4. Strip-high-bit gateways lose P1-P7; remaining P0 must stay non-executing.

### C.4 Encoding rules (byte sequences, endianness, BOM)

#### C.4.1 Native data path: ASCENT-V (clean-room primary)

Native ASCENT does **not** share UTF-8 lead/continuation discipline. Judge-locked P1 (`0x80-0x9F`) and P2 (`0xC0-0xCF`) collide with UTF-8 continuations and 2-byte leads. Dual-stack native wire would demote fences or invent stateful exceptions that break range-to-plane proofs. Clean-room keeps fixed control, skip-by-length, and P9 sync simple.

**This packing is normative for ASCENT 1.1 and later.** Implementers MUST match the formulas below (and the reference codec in `ref/ascent_codec.py`). Earlier draft language that split conts into optional `0xA0-0xAF` nibble vs primary `0xB0-0xBF` is superseded.

**ASCENT-V data units (P3/P4):**

| Class | Range | Form | Use |
|-------|-------|------|-----|
| Cont-only | `0xA0-0xBF` | Illegal as lead | Continuation; **5 payload bits** (`value = byte & 0x1F`); **32 values** in the class |
| 2-byte data | `0xD0-0xDF` | lead + 1 cont | Scalars `U+0080..U+027F` |
| 3-byte data | `0xE0-0xEF` | lead + 2 conts | Scalars `U+0280..U+427F` |
| 4-byte data | `0xF0-0xF4` | lead + 3 conts | Scalars from `U+4280` while the top nibble of `v` fits `0..4` |
| LONG | `0xF5 0x03` | `0xF5 0x03` + `cp:u24be` | Any remaining Unicode scalar (including most emoji) |
| Ext / plane select | `0xF5` + other `plane:u8` | `0xF5` `plane:u8` + data | Force P3/P4/private data plane; **`plane=0x03` is reserved for LONG**, not a plane id |
| Reserved | `0xF6-0xFF` | Illegal open data lead | Strict hard-fault |

**Continuation class (frozen):** every continuation byte is in `0xA0-0xBF` and carries **exactly 5 payload bits**: `payload = byte & 0x1F`. There are **32 legal cont values** (not 64). Conts MUST NOT appear as leads. Cont trailers MUST NOT be `0x00-0x9F` or `0xC0-0xFF`.

**Leads (frozen):** 2-byte leads `0xD0-0xDF`, 3-byte leads `0xE0-0xEF`, 4-byte leads `0xF0-0xF4` (top nibble of the residual must be `0..4` so the lead stays in that range).

##### Scalar encode (normative) - `cp >= 0x80`, not a surrogate

Encode one Unicode scalar per unit. Surrogates `U+D800..U+DFFF` are **illegal** on the wire. Overlong multi-byte encodings of ASCII (`0x00-0x7F`) remain **illegal** (eternal parse law / overlong ban in section C). Decoders MUST reject both.

Let `cont(x) = 0xA0 | (x & 0x1F)`.

1. **2-byte** - `U+0080..U+027F`:
   - `v = cp - 0x80`
   - `lead = 0xD0 | ((v >> 5) & 0xF)`
   - `cont0 = cont(v)`  i.e. `0xA0 | (v & 0x1F)`
   - Wire: `lead cont0` (2 bytes)

2. **3-byte** - `U+0280..U+427F`:
   - `v = cp - 0x280`
   - `lead = 0xE0 | ((v >> 10) & 0xF)`
   - `cont0 = cont(v >> 5)`
   - `cont1 = cont(v)`
   - Wire: `lead cont0 cont1` (3 bytes)

3. **4-byte** - `cp >= U+4280` and residual `v` fits in 18 bits with top field `0..4`
   (equivalently `0 <= v < (5 << 15)`, max `cp = U+2C27F`):
   - `v = cp - 0x4280`
   - Require `((v >> 15) & 0xF) <= 4` so `lead = 0xF0 | ((v >> 15) & 0xF)` lands in `0xF0-0xF4`
   - `cont0 = cont(v >> 10)`
   - `cont1 = cont(v >> 5)`
   - `cont2 = cont(v)`
   - Wire: `lead cont0 cont1 cont2` (4 bytes)

4. **LONG** - any remaining scalar (including most emoji and all scalars that do not fit steps 1-3):
   - Wire: `0xF5 0x03` + `cp` as **u24be** (3 big-endian bytes, high byte first)
   - Total 5 bytes. `cp` MUST be a valid Unicode scalar (not a surrogate, not > `0x10FFFF`).

**Decode sketch (normative inverse):** on lead `L`:
- if `L` in `0xD0-0xDF`: read 1 cont; `v = ((L & 0xF) << 5) | (c0 & 0x1F)`; `cp = v + 0x80`
- if `L` in `0xE0-0xEF`: read 2 conts; `v = ((L & 0xF) << 10) | ((c0 & 0x1F) << 5) | (c1 & 0x1F)`; `cp = v + 0x280`
- if `L` in `0xF0-0xF4`: read 3 conts; `v = ((L & 0xF) << 15) | ((c0 & 0x1F) << 10) | ((c1 & 0x1F) << 5) | (c2 & 0x1F)`; `cp = v + 0x4280`
- if `L == 0xF5` and next byte `== 0x03`: read `cp:u24be`; accept only non-surrogate scalars `<= 0x10FFFF` that cannot use a shorter 2/3/4-byte form (`cp >= U+2C280`). Reject `cp < 0x80` as overlong ASCII.
- else: plane-select / reserved / hard-fault per profile

**Illegal (MUST reject):**
- Overlongs of ASCII (any multi-byte unit that would decode to `0x00-0x7F`)
- Surrogates as scalars or as LONG payloads
- Cont byte outside `0xA0-0xBF` after a data lead
- Cont used as a lead
- Truncated multi-byte unit
- Non-minimal width when a shorter form can represent the same `cp` (encoders MUST use the shortest applicable of steps 1-3 before LONG; decoders MUST reject overlong width for the same residual ranges)

**Plane default:** default data plane is P3. `0xF5 0x04` selects P4 until the next select. Grapheme clustering (ZWJ sequences, variation selectors, skin tones) is a display/agent layer only; each scalar is one ASCENT-V unit in sequence.

**UTF-8 relationship:** the UTF-8 bridge (C.4.2) remains **import/export only**. Native wire is ASCENT-V as specified here. Labs and demos MAY emit multimodal INLINE bodies that contain UTF-8 octets under P6 (kind INLINE) for interop demos; those bytes are MM payload, not ASCENT-V text units.

Bootstrap registry still maps Unicode scalars `0x000080..0x10FFFF` excluding surrogates `0xD800-0xDFFF` onto these forms.

#### C.4.2 UTF-8 bridge (import/export only)

1. **Import:** strict UTF-8 -> map `U+0080+` to ASCENT-V (C.4.1 packing), `U+0000-7F` to P0; strip BOM.  
2. **Export:** Unicode-mapped ASCENT-V -> strict UTF-8; strip or side-channel controls per profile.  
3. `EF BB BF` is bridge-only, never an ASCENT signature; native encoders MUST NOT write it.  
4. Corpora enter via bridge; agents and ECC stay ASCENT-native.  
5. Bridge MUST NOT dual-stack UTF-8 lead/cont bytes as native ASCENT-V data on the wire.

#### C.4.3 Signatures and max-frame

| Signature | Bytes | Meaning |
|-----------|-------|---------|
| Text magic | `ASCENT/1.0` + LF | P0 greppable self-desc |
| DEF | `0xC0` + schema + len + body | P8 self-map |
| Deep sync | `0xD5 0xE5 0xC0 0xDE` | P9 outer unit |
| UTF-8 BOM | `EF BB BF` | Bridge hint only |

ASCENT-7 needs no magic. Prefer magic + DEF for self-desc streams.

| Context | Soft | Hard |
|---------|------|------|
| P2 body | 16384 | 65535 |
| DEF `0xC0` | 1 MiB | 16 MiB |
| MM inline P6 | 16 MiB (E) | 256 MiB / unit (E); D lower (see C.5) |
| Crypto ct P7 | - | 16 MiB |
| P9 outer (D) | 64 KiB soft guidance | MAX_UNIT 8192 normative on D |
| Agent args | 8192 wire | 8192 |
| Private `0xCF` | as DEF | as DEF |

DEF may lower caps, not raise past hard. Over hard: always reject.

### C.5 Profiles (ASCENT-7, E, D, A) and deep-space outer frame

| Profile | Role | Notes |
|---------|------|--------|
| **ASCENT-7** | Identity-only | Pure P0; any classic ASCII file is valid |
| **ASCENT-E** | Earth / general | Full control + scripts + agents + MM + crypto; light ECC optional |
| **ASCENT-E-LEO** | LEO IP usage of E | PATHHINT on Starlink-class IP; light integrity = CRC or short RS(255,239) I=1 (not stacked); no full P9 RS on interactive turns |
| **ASCENT-D** | Deep-space | Strong outer ECC, long sync, low-entropy defaults; MM ref-only preferred; PQ freeze common |
| **ASCENT-A** | Archive | Max DEF + hash chain; full normative embed encouraged; annex repair optional |

#### C.5.1 P9 outer frame (locked)

Big-endian. One frame protects one **unit**. D senders MUST emit P9; D receivers MUST validate P9 before inner decode. Earth may strip P9 and re-emit E.

```
sync[4] = 0xD5 0xE5 0xC0 0xDE
profile = u8              # 0x44='D', 0x45='E', 0x41='A'
ecc     = ECC_PARAMS      # family, (n,k) or rate, interleave, crc_pre
len     = u32be           # unit bytes, 0..MAX_UNIT
unit    = len bytes       # logical payload
parity  = PARITY          # size from ecc
```

**MAX_UNIT (D):** 8192 bytes. Optional STUFF in ecc: stuff `0xD5 -> 0xD5 0x00` inside unit only (default off).

#### C.5.2 ECC families

| Profile | Outer ECC | Interleave | Notes |
|---------|-----------|------------|-------|
| **E** | Optional CRC-32C or light RS(255,239) | I=1 | Low latency; strip on Earth |
| **D** | Default **RS(255,223)** GF(256); optional AR4JA-class LDPC rate 1/2, 1024 info bits | I=8 default; I=1 for beacons | Burst resistance; CCSDS-adjacent RS |
| **A** | RS(255,223) + SHA-256 trailer inside unit; fountain only for bulk annexes | I=4 | Kernel stays RS |

**D defaults (normative unless ecc overrides):** family_id `0x01` = RS_GF256 n=255 k=223; interleave_depth 8; crc_pre=1 (CRC-32C over profile||ecc_hdr||len||unit); family `0x00` NONE is illegal on D.

**Encode order:** logical unit -> optional compress -> CRC (if crc_pre) -> RS/LDPC -> interleave -> sync|profile|ecc|len + parity.  
**Decode:** reverse. Decompress only after CRC+ECC success.

#### C.5.3 Fail policy (D)

1. **Parity/CRC fail => erase unit.** No best-effort text. No U+FFFD fill. Log erase; hunt next sync.  
2. No soft mojibake on D. Offline hex dumps only; never feed agents or displays as text.  
3. Illegal len, unknown profile, or illegal family on D: same as parity fail (erase).  
4. Incomplete interleave at timeout: erase open codeblocks.  
5. After outer OK: unknown inner planes with declared length use skip-by-length; strict plane mode may hard-fault.

#### C.5.4 Low-entropy vs high-entropy

When HE=0 (text/DEF): prefer P0 for labels and DEF kernel strings; optional compress (lz4 / zstd with DEF dict). When any P7 or P6 inline/chunk is present, set **HE=1**: compress MUST be 0; ECC still applies. Ciphertext and media pass opaque. Multimodal on D prefers kind=1 REF (hash + URI/cid); bulk body out-of-band or A annex.

#### C.5.5 Minimal kernel DEF and cold-start

| Artifact | Goal | Content |
|----------|------|---------|
| **DEF-kernel** | <= 2048 B compressed / 4096 B raw | Magic; plane map; P2 leads; 7 agent opcodes; MM kinds; PQ algs in use; ECC table; MAX_UNIT; fail-policy id |
| **DEF-annex** | deferred by content hash | Full prose, emoji policy, large registries |
| **Beacon DEF** | <= 512 B | profile D, RS defaults, kernel_hash 32 B, schema |

**Beacon (unit type `0x01`):** still P9-wrapped; prefer I=1, small len, RS(255,223). One-way broadcast legal.  
**Session-after-lock:** after N=3 good frames with matching profile+kernel_hash, enter SESSION (data/agent/HE units); I may rise to 8. After M=16 consecutive misses, leave SESSION and resume beacon hunt. VERSION_BUMP ignored unless UPGRADE bit set; default pin first kernel.

#### C.5.6 Efficiency (normative intent)

P0 = 1 byte/char. P1 = 1-byte fences/pads. P2 = fixed headers. P3/P4 minimum 2 bytes for non-ASCII (no 1-byte Latin-1; avoids C1 clash). CJK and common targets aim at 3-byte leads. Prefer `0x9F` pad over stretching data. Slight density cost vs UTF-8 on some 2-byte Latin is accepted in exchange for non-colliding C1/P2 and simple skip-by-length proofs.

**Illustrative density (logical scalars only; no control frames):**

| Sample | Scalars | UTF-8 bytes | ASCENT-V bytes | Note |
|--------|---------|-------------|----------------|------|
| ASCII "Hello" | 5 | 5 | 5 (P0) | Identical |
| Latin "cafe" + U+00E9 | 5 | 6 | 7 (P0 + one 2-byte) | ASCENT pays +1 vs UTF-8 2-byte Latin |
| CJK three BMP ideographs | 3 | 9 | 9 (3x 3-byte) | Same class as UTF-8 3-byte |
| One BMP emoji base | 1 | 4 | 3 or 4 (3-byte lead typical) | Often match or better |
| ZWJ emoji (N scalars) | N | sum UTF-8 | sum ASCENT-V | Same scalar count; no surrogate pairs |

**P0 is byte-identical to UTF-8 for `0x00-0x7F`.** Control cost is explicit (P1 1 B fences; P2 fixed headers + len) rather than overloaded multi-byte data. Judge-locked P1 (`0x80-0x9F`) and P2 (`0xC0-0xCF`) would collide with UTF-8 continuation and 2-byte lead ranges; ASCENT-V therefore uses a clean-room data path so fences never alias into data continuations (see C.4.1).

---

## D. Breakdown of the Acronym

| Letter | Stands for | Note |
|--------|------------|------|
| **A** | **A**SCII / **A**merican | Roots in X3.4 / ISO 646 IRV identity |
| **S** | **S**uccessor / **S**tandard | Climb with a contract, not a fork |
| **C** | **C**ompatible / **C**ode | Bit-identical `0x00-0x7F`; no overlongs |
| **E** | **E**ncoding of | Wire form plus control grammar |
| **N** | **N**amed | Scalars, opcodes, algs, kinds in registries |
| **T** | **T**ext | Humans first-class; agents and media share the stream |

Public: **ASCII Successor with Compatible Encoding of Named Text.**  
Committee title: **American Standard Code for Extended Named Text.**  
Mnemonic: *ascent* - leave the 7-bit basement, do not burn the stairs.

---

## E. Hello, Universe (complete example: human text + agent control token + multimodal reference in one valid stream)

Profile: **ASCENT-E**. Optional greppable header, pure P0 greeting, one ROLE agent frame, one multimodal REF. All multi-byte integers big-endian.

### E.1 Readable annotation

```
ASCENT/1.0\n                          # P0 self-desc magic (11 bytes)
Hello, Universe.\n                    # P0 human text (17 bytes)

0x9A                                  # AGENT_OPEN
0xC1                                  # AGENT_OP lead
  ver     = 0x01
  opcode  = 0x0002  ROLE
  flags   = 0x00
  len     = 0x0006  (wire args)
  args    = 0x05 'g' 'u' 'i' 'd' 'e'   # name_len + "guide"
0x9B                                  # AGENT_CLOSE

0x9D 0x4D                             # MM_MARK + 'M'
  kind      = 0x01 REF
  codec     = 0x0005  (example: octet-stream)
  flags     = 0x01    EXTERNAL
  hash-alg  = 0x01    sha-256
  hash      = SHA-256("ASCENT Hello Universe sample media v1")
              = e491921182da9cb7b24e4b8a579d5e78
                edc23e40141d015faa097c3ecc6d65eb
  len       = 0x000000000000002A  (42)
  body      = "cid:sha256:aabbccddeeff0011223344556677889"
```

Hash binds the remote object (illustrative sample payload). Ref string is exactly 42 UTF-8 bytes. No fence escapes needed in this ROLE body.

### E.2 Concrete hex dump (132 bytes total)

```
0000:  41 53 43 45 4E 54 2F 31 2E 30 0A 48 65 6C 6C 6F
0010:  2C 20 55 6E 69 76 65 72 73 65 2E 0A 9A C1 01 00
0020:  02 00 00 06 05 67 75 69 64 65 9B 9D 4D 01 00 05
0030:  01 01 E4 91 92 11 82 DA 9C B7 B2 4E 4B 8A 57 9D
0040:  5E 78 ED C2 3E 40 14 1D 01 5F AA 09 7C 3E CC 6D
0050:  65 EB 00 00 00 00 00 00 00 2A 63 69 64 3A 73 68
0060:  61 32 35 36 3A 61 61 62 62 63 63 64 64 65 65 66
0070:  66 30 30 31 31 32 32 33 33 34 34 35 35 36 36 37
0080:  37 38 38 39
```

**Section map:**

| Offset | Length | Content |
|--------|--------|---------|
| 0x0000 | 11 | `ASCENT/1.0\n` |
| 0x000B | 17 | `Hello, Universe.\n` |
| 0x001C | 15 | Agent ROLE=guide (`9A C1 ... 9B`) |
| 0x002B | 89 | Multimodal REF unit |

**Agent frame alone:**

```
9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B
```

A pure-ASCII-only decoder stops being useful at `0x9A` but never misreads the earlier P0 bytes as multi-byte. An ASCENT-E decoder emits the greeting, applies role `guide`, and records an external media reference bound by the given hash. Under ASCENT-D the same logical unit would ride inside a P9 frame with sync `D5 E5 C0 DE`, RS parity, and erase-on-fail - never a best-effort mojibake of agent fences.

---

## F. Governance model

### F.1 Maintainers

1. **ASCENT Joint Maintenance Group (AJMG)** - dual liaison to **ISO/IEC JTC 1** (character / IT vocabulary) and **IETF** (on-wire profiles, registries). Neither track may silently diverge P0-P2 grammar.  
2. **Editors** for core wire grammar, plane registries, agent opcodes, PQ alg IDs, and deep-space profiles. Changes land as append-only DEF history, not silent rewrites.  
3. **Implementer council** (non-voting): greppability, skip-by-length safety, and "will this brick a cruise probe" review.

### F.2 Adding codepoints, opcodes, planes

| Kind | Process | Bar |
|------|---------|-----|
| P0 units | **Closed.** No additions. | Eternal freeze |
| P1 fences / state | Supermajority; major if fence semantics change | Compat impact statement |
| P2 opcodes / leads | Registry assign open IDs; unknown-with-length skippable | Cap max-frame; no ID reuse |
| P3/P4 scalars / clusters | Periodic repertoire updates | No surrogates; no overlongs |
| P5 agent opcodes | Opcode registry; fences mandatory | Safety opcodes not redefined in place |
| P6 multimodal kinds | Kind/codec/hash-alg tables | DoS caps in profiles |
| P7 PQ algs | Append-only alg-id registry | No silent downgrade |
| P8 DEF / self-map | Schema IDs; history chain | Bootstrap immutable without major |
| P9 outer ECC | Profile-scoped families | Hard-fail parity stays hard |
| P10+ private | Explicit plane-select; hash-named or experimental public block | **Cannot redefine P0-P2** |

Private planes are sandboxes. Unregistered private extensions cannot claim pure E/D/A for those bits.

### F.3 Compatibility guarantees (locked)

- **P0 forever:** pure-ASCII files are valid under identity / E (and as identity subset of D/A).  
- **No overlongs, no remapping 0-127.**  
- **Skip-unknown** with declared length (cap max-frame); strict profiles may hard-fault.  
- **Major only on control grammar break** (fences, leads, DEF shell, parse law). Minor/patch for repertoire, registry adds, clarifications.  
- **Deprecation append-only:** IDs never recycled; "do not emit" is a flag, not a reclaim.  
- **ECC erase-on-fail** on D: no soft decode of failed parity.  
- **DEF self-desc:** bootstrap from greppable P0 header + fixed DEF shell + shipped defaults for known `schema:u8`.

### F.4 PQ freeze for mid-cruise probes

High-latency deployments may declare a **profile freeze**: content-addressed snapshot of the P7 alg registry (and related DEF slice) bound into the mission DEF. Mid-cruise receivers MUST NOT accept alg IDs outside that freeze without pre-authorized upgrade (ground-commanded VERSION_BUMP or dual-DEF handoff). Silent algorithm substitution is non-conformant. Earth registries may grow; frozen probes stay boring on purpose.

### F.5 Self-desc circularity bootstrap

1. Greppable P0 header: `ASCENT/1.0` (or later major) as plain ASCII.  
2. Compiled defaults: every conformant decoder ships tables for known `schema:u8` values enough to parse the DEF shell (`0xC0` + schema + length). Shipped seeds include at least `0x01` KERNEL, `0x02` ANNEX_HASH, `0x03` HISTORY (see C.3.4).  
3. DEF body: plane map, escape grammar, opcode/kind/alg/codec tables (bootstrap seeds in C.3.1-C.3.3), hash of normative prose (full text in profile A). History records carry `hash-alg:u8` with parent/delta hashes.  
4. Validate tables against defaults; strict mismatch is fault. Unknown schema with length: skip or hard-fault per profile.  
5. Default pin: first DEF wins unless upgrade policy allows mid-stream VERSION_BUMP. Optional P7 signature over DEF.  
6. Circularity answer: open the envelope with eternal P0 header + fixed DEF shell + shipped defaults - never version N+1 knowledge first.

### F.6 Trademark and public registry

Clear "ASCENT" for standards use; prefer open implementation over exclusive trademark (certification mark only if branding needs it). Registries are public, secret-free, and append-only. Content hashes of normative text are first-class. Core grammar and repertoire lean ISO/IEC; on-wire registries, agent opcodes, and PQ lists lean IETF (or joint). Conflict rule: **P0-P2 parse law cannot be weakened by either track alone.**

### F.7 Versioning and conformance claims

- **Major:** only when control grammar breaks. Rare. Loud.  
- **Minor:** registry growth, repertoire, opcodes, non-breaking clarifications.  
- **Patch:** errata, examples, non-normative notes.  
- **P0 forever** across majors.  
- Profile labels orthogonal to semver: `ASCENT-E/2.1` is Earth of major 2 minor 1.

Conformance claims MUST name profile + major (and freeze hash when D or mission-frozen). A claim of "ASCENT support" without profile is incomplete.

---

## Appendix: Graph path (one short paragraph citing wave1 inventors -> judge -> wave2 specialists -> synthesizer)

Four wave-1 inventors proposed **ASCENT**, **ANSC**, **PULSAR**, and **MIRROR**. The wave-1 **name-judge** selected ASCENT (score 89), locked the manifesto, plane map P0-P10+, parse law, agent/MM/crypto/DEF/P9 sketches, and hybridized agent opcodes (B), outer ECC (C), and DEF self-maps (D). Wave-2 specialists then froze wire detail: **planes-encoding** (allocation, ASCENT-V, BE, BOM, C1 modes, max-frame), **agents-multimodal** (opcodes, fence escape, MM/P7, injection, Hello Universe seed), **deep-space** (P9 layout, RS/LDPC, erase-on-fail, kernel DEF, beacon/session), and **governance-origin** (A/B/D/F prose, maintainers, freezes, bootstrap). This document is the **synthesizer** merge into one ship-ready ASCENT 1.0 draft under `graph/RUBRIC.md` pass criteria (ASCII 20/20 identity, no surrogates, self-desc recursion, concrete agent and multimodal syntax).

---

## Appendix: Implementer freeze pointers (1.0-RC track)

Normative wire forms used by multi-language goldens are summarized in:

- `docs/SPEC-FREEZE-1.0-RC.md` - RC checklist  
- `tests/freeze_vectors.json` - ROLE, ASCENT-V, Hello Universe, P9 frame hex  
- `tests/test_vectors.json` - encode/decode vectors  
- `tests/run_js_lock.js` - JS codec must match Python  

Agent loop adoption guide: `docs/AGENT-LOOP.md`.  
Installable Python package: `ascent-wire` (`pyproject.toml`, `python -m ascent self-test`).

---

## Appendix: SkyPulse / PATHHINT (append-only, 2.1.0)

This appendix does **not** change P0-P2 parse law, Cont freeze (`0xA0-0xBF`, 5-bit), or ASCENT-D P9 defaults. It assigns reserved P2 lead `0xC5` and documents usage profile **ASCENT-E-LEO**.

**Non-claims:** ASCENT does not increase Starlink physical RF Mbps. PATHHINT is a **usable session bandwidth** / CCA foresight unit (`next_capacity` = predicted bottleneck bits/s as seen by the sender, not RF PHY). Fail-closed erase is the same spirit as D erase-on-fail. Do not market a bare "bandwidth upgrade."

### G.1 SKYSTATE lead

```
0xC5 <schema:u8> <len:u16be> <body:len>
```

- `len` cap for skip: 16384 (P2 soft). Schema `0x01` body cap: 256.
- Unknown `schema` with readable `len`: **skip-by-length**; do not apply (erase).
- Truncation before `len` is readable: hard-fault.

### G.2 PATHHINT v1 (`schema = 0x01`)

Body 26 bytes, plus 4 if `FLAG_CRC`:

| Offset | Field | Required | Notes |
|--------|-------|----------|-------|
| 0 | `flags:u8` | yes | bit0 CAP_KBPS; bit1 HAS_OBSTRUCTION; bit2 HAS_ELEV; bit3 RELATIVE_FREEZE (v1 MUST set); bit4 CRC; bit5-7 MBZ |
| 1 | `path_id:u64be` | **yes** | path or epoch |
| 9 | `next_capacity:u32be` | **yes** | **predicted bottleneck bits/s as seen by the sender**, not RF PHY; kbps if CAP_KBPS |
| 13 | `freeze_ms:u32be` | **yes** (`freeze_until`) | relative growth-freeze; v1 MUST set RELATIVE_FREEZE. Semantic freeze_until = now + freeze_ms. Not Unix-epoch ms on the wire. |
| 17 | `confidence:u16be` | **yes** | 0..10000 => [0,1] |
| 19 | `ttl_ms:u32be` | **yes** | hint lifetime; stale TTL => erase (consumer) |
| 23 | `obstruction:u8` | optional | 0..255 => [0,1] if HAS_OBSTRUCTION; else `0xFF` |
| 24 | `elev_deg_x10:i16be` | optional | degrees * 10; `0x7FFF` absent |
| 26 | `crc32:u32be` | if FLAG_CRC | IEEE CRC-32 of bytes 0..25 |

**Fail-closed:** CRC fail, short-RS fail (if used), reserved flags, bad length, missing RELATIVE_FREEZE, confidence > 10000, unknown schema/version, or stale TTL: **erase** (`applied=false`). Never act on a corrupt unit. Truncation before `len` is a hard-fault.

Optional P9 wrap of the whole unit when integrity is requested (spool / D). Interactive LEO IP MUST NOT require full RS(255,223) P9 (double-FEC tax vs PHY+TLS).

### G.3 ASCENT-E-LEO vs ASCENT-D

ASCENT-E-LEO is a **usage profile** of E: emit/consume PATHHINT; Starlink IP/QUIC uses **light integrity** (PATHHINT CRC, v1 shipped, **or** short RS(255,239) I=1 as a substitute, never stacked). Full RS(255,223) ASCENT-D is for spool / deep-space / high-BER only. It is not a new parse law and does not freeze Cont differently.

Goldens: `tests/skypulse_vectors.json`. Narrative: `docs/SKYPULSE.md`. LeoAware hybrid fuse: `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`.

---

*End ASCENT Official Specification v1.0.0-rc1. Keep every classic ASCII byte sacred. Ascend the rest without burning the stairs.*
