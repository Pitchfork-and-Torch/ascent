# name-judge | wave 1

**node:** name-judge  
**wave:** 1  

---

## Score table (0-100)

| Source | Name | Score | One-line verdict |
|--------|------|-------|------------------|
| A | **ASCENT** | **89** | Best shippable name (ASC DNA + English word); solid planes; slightly soft on binary agent/ECC detail |
| B | ANSC | 83 | Strongest agent opcode story; name is cold acronym soup; governance thin |
| C | PULSAR | 86 | Best deep-space/ECC + concrete binary markers; C1 collision risk; heritage underplayed |
| D | MIRROR | 85 | Best self-desc recursion (DEF, version bump); crowded plane list; forced acronym |

Pass bar spirit: all four clear ASCII 0-127; none is "Unicode but better" hand-wave. A wins on name + balance; tech is hybridized below.

---

## WINNER

**NAME:** ASCENT  
**Expansion:** ASCII Successor with Compatible Encoding of Named Text  
(Committee title retained: American Standard Code for Extended Named Text)

**Locked manifesto:** Keep every classic ASCII byte sacred, then ascend scripts, agents, media refs, crypto control, and deep-space links into one self-describing stream - fixed-width control for machines, variable-width data for humans, never remapping 0x00-0x7F.

**Pronunciation:** /uh-SENT/. Profiles: `ASCENT-7` (identity-only), `ASCENT-E` (Earth), `ASCENT-D` (deep-space), `ASCENT-A` (archive/self-desc heavy).

**Hybrid note:** Name + heritage story from **A**. Agent opcodes and skip-unknown from **B**. Outer ECC, sync, hard-fail parity, binary introducers from **C**. DEF self-map, open/close fences, content-addressed MM from **D**.

---

## Architecture synthesis (mandatory for rest of graph)

**Parse law (eternal):** if byte `< 0x80`, it is classic 7-bit ASCII (bit-identical, no overlongs ever). Higher capability only via `>= 0x80` leads or length-prefixed frames that never alias into 0-127.

| Plane | ID | Role | Layout (normative sketch) |
|-------|-----|------|---------------------------|
| Identity | P0 | Classic ASCII | `0x00-0x7F` single-byte forever |
| C1 fixed | P1 | Non-text controls: stream state, profile, soft-sync, agent fence bytes | `0x80-0x9F` reserved; never printable data. Profile `STRICT_C1` default; `LEGACY_PASS` optional |
| Escape nucleus | P2 | Length-prefixed opcodes | Lead `0xC0-0xCF` + fixed header (opcode, flags, len) + body |
| Scripts | P3 | Living + historical scripts | Variable-width scalars; no surrogates |
| Emoji/symbols | P4 | Pictographs + ZWJ as data sequences | Same V-width family as P3; grapheme policy Wave 2 |
| Agent | P5 | LLM/OS control in-band | Fixed after lead; open/close fences |
| Multimodal | P6 | Refs + inline + chunk stream | Marker + type + hash + len + body/ref |
| Crypto | P7 | Quantum-safe control only | Alg id, kid, nonce, sealed blob; keys OOB by default |
| Self-map | P8 | Definition document + registries | Bootstrap + DEF + version history |
| Deep outer | P9 | ECC frame wraps logical units | Sync + profile + params + payload + parity |
| Private | P10+ | Experimental | Explicit plane-select only; cannot redefine P0-P2 |

**Profiles:** E (light ECC optional), D (strong outer ECC, long sync, low-entropy defaults), A (max DEF + hash chain).

**Escapes:** Classic ESC `0x1B` remains legacy VT-safe. ASCENT control uses P1 fence bytes and P2 leads. Unknown plane with declared length: skip-by-length (cap max-frame); strict profile may hard-fault.

**ASCII embed:** Any pure-ASCII file is valid ASCENT under identity/E. Greppers, shebangs, SMTP 7-bit paths stay correct on the subset.

---

## Locked syntax sketches

**Agent control token**

```
0x9A                              # AGENT_OPEN (P1)
0xC1 <ver:u8> <opcode:u16be> <flags:u8> <len:u16be> <args>
0x9B                              # AGENT_CLOSE
```

Opcodes (initial): `0x0001 STOP`, `0x0002 ROLE`, `0x0003 TOOL`, `0x0004 THINK`, `0x0005 HANDOFF`, `0x0006 CAP`, `0x0007 SAFETY`.  
Args body must not contain raw `0x9A`/`0x9B`; escape `0xC1 0x1B <byte>`.  
Debug non-normative: `[A:tool_call]...[/A]`.

**Multimodal marker**

```
0x9D M <kind:u8> <codec:u16be> <flags:u8> <hash-alg:u8> <hash:N> <len:u64be> [body-or-ref]
```

kind: 1=ref, 2=inline, 3=chunk-continue, 4=end. Flags mark external URI/cid vs inline. Deep-space may force ref-only.

**Quantum-safe control**

```
0x9C K <alg:u16be> <kid-len:u8> <kid> <nonce-len:u8> <nonce> <ct-len:u32be> <ct>
```

Alg IDs from P8 PQ registry. No silent downgrade; deprecation is append-only registry + profile freeze for cruise probes.

**Self-desc frame**

```
ASCENT/1.0\n                    # P0 greppable header
0xC0 <schema:u8> <len:u32be> <DEF body>
```

DEF body: plane map, escape grammar, opcode/kind/alg tables, content hash of normative prose (or full text in profile A), append-only history `(semver, date, parent-hash, delta-hash)`. Mid-stream `VERSION_BUMP` only under explicit upgrade policy; default pin first DEF. Optional P7 signature over DEF.

**Deep-space outer (profile D)**

```
sync 0xD5 0xE5 0xC0 0xDE | profile | ECC params | len | unit | parity
```

Parity fail => erase unit (no mojibake best-effort).

---

## Wave 2 handoffs

**planes-encoding**  
Freeze P0-P10 IDs and wire leads. Decide UTF-8 dual-stack vs clean-room V-width for P3/P4 (compat vs proofs). Ban overlongs. Define C1 STRICT vs LEGACY_PASS detection. Register private-plane allocation (hash-named vs IANA-like). Efficiency tables: fixed CTL pads vs min CJK/emoji unit size.

**agents-multimodal**  
Opcode registry + role/tool name normalization (binary exact vs NFC). THINK opacity policy for shared logs. MM stream reassembly, max len, sandbox, hash-binding refs. Injection model: fences mandatory; high-assurance optional channel IDs. Safety opcode semantics (untrusted tool results).

**deep-space**  
Pick ECC families per profile (RS / LDPC / fountain), interleave vs latency, low-entropy alphabet that does not crush high-entropy K/M ciphertext. Minimal kernel DEF size under MTU; deferred full registry by content hash. Cold-start beacon vs session-after-lock. Compressor vs ECC layering order.

**governance-origin**  
Maintainers, plane-add process, PQ alg freeze for mid-cruise, trademark ASCENT clearance, ISO vs IETF vs joint. Compat promise: P0 forever; major version only on control grammar break. Self-desc circularity: bootstrap from P0 header + compiled defaults for known schema. Secret-free public registry process.

---

## Rejected alternatives (one line each)

- **ANSC:** solid tech, forgettable name; loses ASC heritage for standards memos.  
- **PULSAR:** excellent ECC story; over-weights RF metaphor for a general text+agent standard.  
- **MIRROR:** elegant recursion; expansion is stretchy marketing-acronym and plane map over-fragmented.  
- **ASCII2 / UTF-Next / Extended ASCII:** sequel or politics; no novel control plane story.  
- **Pure ESC-only text markers (A alone):** log-pretty but weak for binary agents and ECC framing.  
- **C1-as-printables or remapping 0-127:** instant fail of identity contract.

---

*End name-judge wave1. Graph must use ASCENT + plane map and syntax above.*
