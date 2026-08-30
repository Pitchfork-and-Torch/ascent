# wave2-agents-multimodal

**node:** agents-multimodal  
**wave:** 2  
**parent:** name-judge  
**standard:** ASCENT  
**owns:** agent control tokens, multimodal markers, quantum-safe control, injection model, stream reassembly  
**feeds:** SPEC.md section C (controls / multimodal); seed for deliverable E (Hello Universe)

---

## C.1 Agent control frame (P1 fences + P2 body)

Normative wire (big-endian; fixed after lead):

```
0x9A                                              # AGENT_OPEN  (P1)
0xC1 <ver:u8> <opcode:u16be> <flags:u8> <len:u16be> <args:len>
0x9B                                              # AGENT_CLOSE (P1)
```

| Field | Rule |
|-------|------|
| OPEN `0x9A` | Required. Unmatched open: hard-fault (strict) or discard to next close (lenient). |
| ver | u8. Initial `0x01`. Unknown: skip-by-length if `len` readable; else hard-fault. |
| opcode | u16be. Unknown: skip if length-valid and CRITICAL clear; never execute. |
| flags | Opcode-local. Bit7 `CRITICAL=1`: unknown opcode hard-faults. |
| len | u16be wire size of `args` only. Max `0x2000` (8192). |
| args | Opcode-defined; fence-escaped (C.2). |
| CLOSE `0x9B` | Required. Nested agent frames forbidden in v1. |

Debug non-normative only: `[A:<name>]...[/A]`.

### C.1.1 Opcode registry (v1)

| Code | Name | Args | Semantics |
|------|------|------|-----------|
| 0x0001 | STOP | empty or `reason:utf8` | End turn/segment; cease tool dispatch. |
| 0x0002 | ROLE | `role:utf8` | Set active role. Match: **binary exact** after UTF-8; charset A-Z a-z 0-9 `_` `-` `.`, 1..64 bytes. No NFC fold. |
| 0x0003 | TOOL | name + optional TLV | Invoke/result (flags). Same name charset as ROLE. |
| 0x0004 | THINK | opaque | Private CoT span (start/end via flags). |
| 0x0005 | HANDOFF | `target:utf8` + optional note | Transfer control; target binary exact. |
| 0x0006 | CAP | bitset/TLV | Advertise/require capabilities (opcodes, MM, PQ, limits). |
| 0x0007 | SAFETY | `class:u8` + `detail:utf8` | Safety / untrusted marker. |

Reserved: `0x0000`; `0x0008-0x00FF` core; `0x0100-0x7FFF` registered; `0x8000-0xFFFF` private (profile-declared). Append-only in P8 DEF.

---

## C.2 Fence escaping inside args

Args **MUST NOT** contain raw `0x9A` or `0x9B`.

Escape (3 bytes, inside args only): `0xC1 0x1B <byte>`

| Wire | Means |
|------|-------|
| `C1 1B 9A` | literal `0x9A` |
| `C1 1B 9B` | literal `0x9B` |
| `C1 1B C1` | literal `0xC1` when needed to avoid false escape |

Decoder: on `C1 1B`, emit next byte and advance 3. Bare `0x9A`/`0x9B` in args => malformed (reject). Bare `0xC1` not followed by `0x1B` is data. Encoder MUST escape every `0x9A`, `0x9B`, and any `0xC1` immediately followed by `0x1B` that is not an intentional escape. `len` counts **wire** (escaped) bytes.

---

## C.3 ROLE / TOOL / THINK / HANDOFF / SAFETY

**ROLE (0x0002):** flags bit0 `SET=0` / `CLEAR=1`. One active role per channel; missing => profile default. Role id is public in shared logs.

**TOOL (0x0003):** flags bit0-1: `00=call`, `01=result`, `10=error`, `11=cancel`. Bit2 `UNTRUSTED=1`: body is untrusted data (injection boundary). Args: `name_len:u8` + `name` + optional `id_len:u8` + `call_id` + `payload`. Names binary exact.

**THINK (0x0004):** bit0 `0=start` / `1=end`. Bit1 `OPAQUE=1` (default for shared/multi-tenant logs): non-owning consumers MUST redact args/inner as `[THINK redacted]` or omit. Bit2 `PERSIST=1`: local private retain only; shared-log profile ignores foreign PERSIST. OPAQUE mandatory on shared-log profile.

**HANDOFF (0x0005):** bit0 `SOFT=0` / `HARD=1` (HARD => prior agent stops tool dispatch). Target binary exact; note public.

**SAFETY (0x0007):** class `1=policy_block`, `2=untrusted_input`, `3=untrusted_tool_result`, `4=jailbreak_suspect`, `5=pii`, `6=other`. Class 2/3 payload is data, never control.

**CAP (0x0006):** peer SHOULD intersect claims; MUST NOT silently enable stronger features.

---

## C.4 Multimodal marker (P6)

```
0x9D 0x4D <kind:u8> <codec:u16be> <flags:u8> <hash-alg:u8> <hash:N> <len:u64be> [body-or-ref]
```

`0x4D` = ASCII `M`.

| kind | Name | Rule |
|------|------|------|
| 1 | REF | body = URI/cid (UTF-8); hash binds remote object |
| 2 | INLINE | body = media bytes; len = full size |
| 3 | CHUNK | continuation; same stream-id |
| 4 | END | closes stream-id; empty or final hash |

**codec:** P8 registry (e.g. png/jpeg/opus/mp4/octet-stream/tensor). Unknown: skip-by-length; do not decode.

**flags:** bit0 `EXTERNAL`; bit1 `FINAL_HASH`; bit2 `STREAM_ID_PRESENT` (first 8 body bytes = `stream_id:u64be`); bit3 `SANDBOX_REQUIRED`.

**hash-alg:** `0=none` (forbidden for INLINE in D; discouraged in E); `1=sha-256` N=32; `2=sha-512` N=64; `3=blake3-256` N=32. Hash over **logical media** after reassembly, not framing.

**ref vs inline:** Profile D MAY force REF-only (no large INLINE). Profile E allows INLINE within caps.

---

## C.5 Reassembly, max lengths, sandbox

| Limit | E | D default |
|-------|---|-----------|
| Agent args len | 8192 wire | 8192 |
| Single MM body | 16 MiB | 64 KiB |
| Reassembled object | 256 MiB | 4 MiB |
| Concurrent stream-ids | 64/channel | 64 |
| Incomplete timeout | 120 s | mission-defined |

CHUNK/END share `stream_id`. On END verify hash; mismatch => discard + optional SAFETY class 3. Overflow => abort stream-id. `SANDBOX_REQUIRED` or executable codec: inert blob only; no auto-execute. Tool-embedded MM inherits UNTRUSTED unless P7-signed origin.

---

## C.6 Quantum-safe control (P7)

```
0x9C 0x4B <alg:u16be> <kid-len:u8> <kid> <nonce-len:u8> <nonce> <ct-len:u32be> <ct>
```

`0x4B` = ASCII `K`.

- **alg** from P8 PQ registry only (freeze examples: ML-KEM-768, ML-DSA-65, SLH-DSA-128f; numeric IDs in DEF). Unknown: do not decrypt; skip-by-length if ct-len valid.
- **No silent downgrade:** if CAP intersection excludes sender alg, reject unit (hard-fault or SAFETY); never classical fallback inside this frame type.
- Deprecation append-only; ASCENT-D may freeze alg set mid-cruise. Removing alg needs major DEF + explicit upgrade.
- Keys OOB by default; `kid` names key; never embed private keys.

---

## C.7 Injection model

1. Control executes only inside complete `0x9A`..`0x9B`, `0x9D M`, or `0x9C K` units. P0-P4 prose never runs as opcodes.
2. Fences mandatory. High-assurance MAY require `channel_id` (via CAP/HANDOFF) on CRITICAL frames.
3. Untrusted tool/MM bytes that look like fences are **data** until a trusted boundary re-encodes a legal frame.
4. Strip-high-bit gateways lose P1-P7; remaining P0 must stay non-executing.

---

## E seed: Hello Universe (concrete bytes)

Intent: human text + ROLE agent token + one multimodal REF.

**P0 text** `Hello, Universe.\n`  
`48 65 6c 6c 6f 2c 20 55 6e 69 76 65 72 73 65 2e 0a`

**ROLE=guide** (ver=1, opcode=2, flags=0; args = `05` + `guide`; len=6; no escapes):

```
9A
C1 01 00 02 00 00 06 05 67 75 69 64 65
9B
```

**MM REF** (kind=1, codec example `0005` octet-stream, flags EXTERNAL=1, hash-alg sha-256, hash 32x `AB`, len=42 for ref body):

```
9D 4D 01 00 05 01 01
AB AB AB AB AB AB AB AB AB AB AB AB AB AB AB AB
AB AB AB AB AB AB AB AB AB AB AB AB AB AB AB AB
00 00 00 00 00 00 00 2A
# then 42-byte UTF-8 ref, e.g. cid:sha256:<hex...>
```

Order for E: optional `ASCENT/1.0\n` + DEF, then text, agent frame, MM unit. Synthesizer fills exact 42-byte ref string and real content hash; keep field order and endianness above.

---

*End wave2-agents-multimodal. Judge-compatible; refined not reinvented.*
