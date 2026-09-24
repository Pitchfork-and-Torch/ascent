# ASCENT evaluator - round 1

**node:** evaluator  
**round:** 1  
**target:** `.\SPEC.md` (ASCENT Official Specification v1.0 Draft)  
**rubric:** `graph/RUBRIC.md`  
**locked expectations:** `artifacts/wave1-judge.md`  
**date:** 2026-07-29

---

## Explicit completeness checks

| Check | Result | Evidence |
|-------|--------|----------|
| Section **A** exists (name, acronym, manifesto) | YES | SPEC.md `## A. Name, acronym, manifesto` |
| Section **B** exists (origin story) | YES | `## B. Origin Story` |
| Section **C** exists (technical overview) | YES | `## C. Technical overview` through C.5 |
| Section **D** exists (acronym breakdown) | YES | `## D. Breakdown of the Acronym` |
| Section **E** exists (Hello Universe) | YES | `## E. Hello, Universe` |
| Section **F** exists (governance) | YES | `## F. Governance model` |
| Hello Universe has **hex dump** | YES | E.2 concrete hex dump, 132 bytes total, offsets `0000`-`0080` |
| Hello Universe has human text + agent + multimodal | YES | P0 greeting + ROLE agent frame + MM REF |
| Judge-locked name ASCENT + expansion | YES | A; matches wave1-judge WINNER |
| Parse law byte `< 0x80` = classic ASCII forever | YES | A, C eternal parse law, C.2 |
| Planes P0-P10+ present | YES | C.1 table |
| Agent / MM / crypto / DEF / P9 syntax present | YES | C.3.1-C.3.4, C.5.1 |

---

## Criterion scores

### 1. ASCII 0-127 byte-identical + clear embed - **20 / 20**

**Pass bar:** Must be 20/20. **Awarded: full.**

**Evidence:**
- Eternal parse law: `if a byte is less than 0x80, it is classic 7-bit ASCII, bit-identical, forever` (A; C).
- Overlong ban: multi-byte encoding of `0x00-0x7F` scalars illegal; decoders MUST reject (C).
- Embed: `Wire 0x00-0x7F equals classic ASCII ... Pure-ASCII files are valid ASCENT-7` (C.2); shebangs, SMTP 7-bit paths, greppers on P0 subset.
- Private planes `MUST NOT remap 0x00-0x7F` (C.1); F.3 `P0 forever` / `No overlongs, no remapping 0-127`.
- Identity profile `ASCENT-7` (A, C.5).

**Gaps:** None material for this criterion. Identity contract is explicit and repeated without loopholes.

---

### 2. Scripts + emoji first-class (no surrogates) - **14 / 15**

**Pass bar:** >= 12. **Awarded: 14.**

**Evidence:**
- Planes P3 Scripts and P4 Emoji/symbols with ZWJ sequences (C.1).
- `No UTF-16 surrogates on the wire: each scalar is one unit (1-4 bytes). ZWJ, variation selectors, and skin tones are separate scalars in sequence` (C).
- ASCENT-V 2/3/4-byte data units; bootstrap maps `0x000080..0x10FFFF` excluding surrogates `0xD800-0xDFFF` (C.4.1).
- Grapheme clustering is display/agent layer only (C.4.1); efficiency intent for CJK 3-byte leads (C.5.6).

**Gaps:**
- No concrete repertoire assignment table beyond Unicode range claim (bootstrap registry referenced, not enumerated).
- Emoji policy deferred to DEF-annex (`C.5.5`); fine for draft but not fully first-class in-spec examples beyond ZWJ mention.

---

### 3. Agent control tokens in-stream - **14 / 15**

**Pass bar:** >= 12. **Awarded: 14.**

**Evidence:**
- Locked fence form matches judge: `0x9A` / `0xC1 ver opcode flags len args` / `0x9B` (C.3.1).
- Opcode registry v1: STOP, ROLE, TOOL, THINK, HANDOFF, CAP, SAFETY with semantics (C.3.1 table).
- Fence escape in args: `0xC1 0x1B <byte>`; raw `0x9A`/`0x9B` forbidden in args (C.3.1).
- CRITICAL flag, max args 8192, ROLE binary-exact match, THINK opacity, SAFETY untrusted classes (C.3.1).
- Injection model: control only inside complete fences; untrusted tool/MM bytes stay data until re-encode (C.3.4).
- Concrete Hello Universe agent frame + standalone hex `9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B` (E.1, E.2).

**Gaps:**
- TOOL and CAP args described as name/TLV/bitset without full byte-level TLV map.
- Nested frames forbidden; concurrent multi-agent channels only lightly touched (optional channel IDs on CRITICAL).

---

### 4. Multimodal streamable refs/payloads - **9 / 10**

**Pass bar:** >= 7. **Awarded: 9.**

**Evidence:**
- P6 wire: `0x9D 0x4D <kind> <codec> <flags> <hash-alg> <hash:N> <len:u64be> [body-or-ref]` (C.3.2).
- kinds 1 REF / 2 INLINE / 3 CHUNK / 4 END; flags EXTERNAL, FINAL_HASH, STREAM_ID_PRESENT, SANDBOX_REQUIRED (C.3.2).
- Hash over logical media after reassembly; unknown codec skip-by-length; D prefers ref-only (C.3.2, C.5.4).
- Hello Universe REF with sha-256, EXTERNAL, len 42, body `cid:sha256:...`, full hex (E.1-E.2).

**Gaps:**
- CHUNK reassembly: stream-id present but reorder, timeout, and incomplete-stream fault rules not fully specified.
- Codec registry is example-level (`0x0005` octet-stream) without initial normative codec table.

---

### 5. Self-describing meta-document - **13 / 15**

**Pass bar:** >= 12. **Awarded: 13.**

**Evidence:**
- Greppable bootstrap: `ASCENT/1.0\n` + `0xC0 schema:u8 len:u32be DEF body` (C.3.4, C.4.3).
- DEF carries plane map, escape grammar, opcode/kind/alg tables, content hash of normative prose, append-only history `(semver, date, parent-hash, delta-hash)` (C.3.4).
- Circularity bootstrap fully answered: P0 header + fixed DEF shell + shipped defaults for known `schema:u8` (F.5).
- First-DEF pin, VERSION_BUMP under upgrade policy, optional P7 signature (C.3.4, F.5).
- DEF-kernel / DEF-annex / Beacon DEF size goals and session-after-lock (C.5.5).
- Profile A archive/self-desc heavy (A, C.5).

**Gaps:**
- DEF body binary schema not fully field-mapped (no normative TLV/struct layout or enumerated `schema:u8` values for shipped defaults).
- Content-hash algorithm for normative prose not pinned in one place (sha-256 used for MM; DEF history uses hashes without alg id in the history tuple sketch).

---

### 6. Efficiency (fixed control / var data / escapes) - **9 / 10**

**Pass bar:** >= 7. **Awarded: 9.**

**Evidence:**
- Philosophy: fixed or length-declared control; variable data; never alias into 0-127 (C, C.1).
- P1 single-byte fences; P2 fixed BE headers + len; P3/P4 ASCENT-V 2-4 byte data; pad `0x9F` (C.1, C.4.1, C.5.6).
- Explicit efficiency intent: P0 = 1 byte/char; min 2 for non-ASCII; CJK/common aim 3-byte; density tradeoff vs UTF-8 accepted for non-colliding C1/P2 (C.5.6).
- Max-frame soft/hard caps table (C.4.3); clean-room ASCENT-V justified by P1/P2 vs UTF-8 collision (C.4.1).
- Fence escape cost fixed at 3 wire bytes inside agent args (C.3.1).

**Gaps:**
- No measured comparison table (sample scripts: Latin, CJK, emoji) of ASCENT-V vs UTF-8 byte counts.
- Optional `0xA0-0xAF` nibble cont adds a second continuation class that implementers must track via DEF.

---

### 7. Deep-space profile (ECC, low-entropy) - **5 / 5**

**Pass bar:** >= 3. **Awarded: full.**

**Evidence:**
- Profile ASCENT-D and locked P9: sync `0xD5 0xE5 0xC0 0xDE` + profile + ecc + len + unit + parity (C.5.1; matches judge).
- ECC families: default RS(255,223) GF(256), optional AR4JA-class LDPC; interleave I=8 default; crc_pre; family NONE illegal on D (C.5.2).
- Fail policy: parity/CRC fail => erase unit; no soft mojibake; incomplete interleave erase (C.5.3).
- HE=0 vs HE=1: compress rules; ciphertext/media opaque; MM on D prefers REF (C.5.4).
- Beacon / session-after-lock; MAX_UNIT 8192; encode/decode order (C.5.5, C.5.2).
- PQ freeze mid-cruise (F.4).

**Gaps:** None material for 5-point criterion. Optional STUFF default-off is documented.

---

### 8. Governance (maintainers, add process, compat) - **5 / 5**

**Pass bar:** >= 3. **Awarded: full.**

**Evidence:**
- Maintainers: AJMG dual ISO/IEC JTC 1 + IETF; editors; implementer council (F.1).
- Per-kind process table: P0 closed; P1 supermajority; registries append-only; private cannot redefine P0-P2 (F.2).
- Compat guarantees: P0 forever, no overlongs, skip-unknown, major only on control grammar break, deprecation append-only, ECC erase-on-fail, DEF self-desc (F.3).
- Versioning major/minor/patch + profile labels orthogonal to semver (F.7).
- Trademark/registry note and conflict rule: P0-P2 cannot be weakened by either track alone (F.6).

**Gaps:** None material for 5-point criterion.

---

### 9. Completeness A-F + Hello Universe - **5 / 5**

**Pass bar:** 5/5. **Awarded: full.**

**Evidence:**
- Sections A through F present with required content types (name/manifesto, origin, technical, acronym breakdown, Hello Universe, governance).
- E.1 readable annotation + E.2 hex dump with section map and agent-alone dump.
- Stream includes human P0 text, agent ROLE=guide, multimodal REF with hash bind.
- Appendix cites graph path wave1 inventors -> judge -> wave2 specialists -> synthesizer.

**Hex dump integrity (spot check, not inventing):**
- Offsets: 11 + 17 = 0x1C agent start; 15-byte agent; 0x2B MM start; 89-byte MM; total 132.
- Agent: `9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B` = OPEN + ver1 + ROLE 0x0002 + flags0 + len6 + `05` + `guide` + CLOSE.
- MM: `9D 4D 01 00 05 01 01` + 32-byte hash + `00 00 00 00 00 00 00 2A` + 42-byte cid body.

**Gaps:** None for completeness score.

---

## Score table

| Criterion | Max | Awarded | Pass bar |
|-----------|-----|---------|----------|
| ASCII 0-127 byte-identical + clear embed | 20 | **20** | 20/20 |
| Scripts + emoji first-class (no surrogates) | 15 | **14** | >= 12 |
| Agent control tokens in-stream | 15 | **14** | >= 12 |
| Multimodal streamable refs/payloads | 10 | **9** | >= 7 |
| Self-describing meta-document | 15 | **13** | >= 12 |
| Efficiency (fixed control / var data / escapes) | 10 | **9** | >= 7 |
| Deep-space profile (ECC, low-entropy) | 5 | **5** | >= 3 |
| Governance (maintainers, add process, compat) | 5 | **5** | >= 3 |
| Completeness A-F + Hello Universe | 5 | **5** | 5/5 |
| **TOTAL** | **100** | **94** | >= 85 + ASCII 20 |

---

## 1. Total score

**94 / 100**

## 2. Verdict

**PASS**

Requirements: total >= 85 **and** ASCII criterion = 20/20.  
Both met: **94 >= 85** and **ASCII = 20/20**.

No anti-pattern from rubric:
- Not "Unicode but better" hand-wave (novel P1-P9 control planes).
- Does not break 0-127.
- No UTF-16 surrogate dependency.
- Name has technical substance (planes, wire syntax, profiles).
- Self-desc recursion answered (F.5).
- Multimodal has concrete stream syntax + hex example.

Judge locks satisfied: ASCENT name/expansion/manifesto/profiles; parse law; P0-P10+ map; agent/MM/crypto/DEF/P9 sketches hybridized into normative detail.

## 3. Revision patches

**Not required** (PASS). No ordered FAIL patch list.

## 4. Residual polish items (optional, non-blocking)

1. **DEF body binary layout:** enumerate shipped `schema:u8` values and a normative field/TLV map for plane map, opcode tables, and history records (closes most of the 2-point self-desc gap).
2. **TOOL / CAP arg TLVs:** pin byte layouts for TOOL name+flags and CAP bitset/TLV so implementers need no invent.
3. **CHUNK reassembly rules:** timeout, max open streams, reorder policy, and fault on END without FINAL_HASH when required.
4. **Codec + PQ alg bootstrap tables:** numeric IDs for initial codecs and PQ algs (names ML-KEM-768 etc. are present; IDs are not).
5. **Efficiency comparison table:** sample byte counts ASCENT-V vs UTF-8 for Latin, CJK, and emoji sequences (normative intent already in C.5.6).
6. **DEF history hash alg:** pin alg id (e.g. sha-256) in the history tuple sketch so archive pin is unambiguous.
7. **ROLE args consistency:** Hello Universe uses length-prefixed `05 guide`; ROLE row says `role` UTF-8 with charset constraints - state that name_len:u8 prefix is normative for ROLE/TOOL names.

## 5. Completeness + Hello Universe hex (explicit)

- **A-F:** all six sections exist in SPEC.md.
- **Hello Universe hex dump:** present at E.2 (132 bytes), with section map and agent-alone dump.
- **ASCII identity:** full 20/20.

---

*End evaluator round 1. ASCENT SPEC.md PASS at 94/100.*
