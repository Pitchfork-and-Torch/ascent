# ASCENT-D deep-space profile | wave 2

**node:** deep-space  
**wave:** 2  
**parent:** name-judge  
**standard:** ASCENT  
**profile:** ASCENT-D (normative). Notes for C (crypto P7) and F (planes/framing).

---

## 1. Scope

ASCENT-D is the long-haul profile. It mandates outer **P9** ECC frames around logical units. Inner planes P0-P8 follow the judge synthesis.

**Parse law:** bytes `< 0x80` are classic ASCII forever. Higher capability only via `>= 0x80` leads or length-prefixed frames that never alias 0-127. Earth may strip P9 and re-emit E. D senders MUST emit P9; D receivers MUST validate P9 before inner decode.

---

## 2. Outer frame layout (P9) - LOCKED

Big-endian. One frame protects one **unit**.

```
sync[4] = 0xD5 0xE5 0xC0 0xDE
profile = u8              # 0x44='D', 0x45='E', 0x41='A'
ecc     = ECC_PARAMS      # sec 3
len     = u32be           # unit bytes, 0..MAX_UNIT
unit    = len bytes       # logical payload (may be compressed; sec 5)
parity  = PARITY          # size from ecc
```

| Field | Normative |
|-------|-----------|
| sync | Hard lock. Slide until match; confirm via profile+len+parity. |
| profile | Selects ECC table and fail policy for this frame. |
| ecc | family id, (n,k) or rate class, interleave depth, crc_pre flag. |
| len | Exact unit length. len > MAX_UNIT => erase frame. |
| unit | Opaque until parity OK. |
| parity | Redundancy over protected vector as family requires. |

**MAX_UNIT (D):** 8192 bytes. Optional STUFF=1 in ecc: stuff `0xD5 -> 0xD5 0x00` inside unit only. Default STUFF=0 (resync on next clean sync).

---

## 3. ECC families by profile - LOCKED

| Profile | Outer ECC | Interleave | Why |
|---------|-----------|------------|-----|
| **E** | Optional: CRC-32C alone, or light **RS(255,239)** GF(256) (16 parity). | I=1 | Low latency; strip on Earth. |
| **D** | Default **RS(255,223)** GF(256) (32 parity). Chain into **I=8** row-column interleave across up to 8 codeblocks. Weak-link option: **AR4JA-class LDPC** rate 1/2, 1024 info bits (family LDPC_D). | I=8 default; I=1 for beacons | CCSDS-adjacent RS for short units; LDPC for low SNR; interleave fights bursts. |
| **A** | **RS(255,223)** + SHA-256 hash trailer inside unit. Fountain/raptor **only** for bulk annexes (full DEF, media), never control kernels. | I=4 | Integrity + large-annex repair; kernel stays RS. |

**D defaults (normative unless ecc overrides):**

- family_id `0x01` = RS_GF256, n=255, k=223  
- Short final block zero-padded before encode; `len` is true size  
- interleave_depth = 8  
- crc_pre = 1: CRC-32C over (profile||ecc_hdr||len||unit), 4 B prepended before RS  
- family_id `0x02` = LDPC_AR4JA_R12_N1024 (optional D)  
- family_id `0x00` = NONE (E only; illegal on D)

---

## 4. Fail policy - LOCKED

1. **Parity/CRC fail:** **erase unit**. No best-effort text. No U+FFFD fill. Log erase; hunt next sync.  
2. **No soft mojibake on D.** Non-normative SOFT_DEBUG may dump hex offline only; never feed agents or displays as text.  
3. Illegal len, unknown profile, or family illegal on D: same as parity fail (erase).  
4. Incomplete interleave at timeout: erase open codeblocks in that superframe.  
5. After outer OK: unknown inner planes with declared length use skip-by-length; STRICT_PLANE=1 may hard-fault.

---

## 5. Layering and low-entropy defaults - LOCKED

**Encode:** logical unit -> optional compress -> CRC (if crc_pre) -> RS/LDPC segment -> interleave -> sync|profile|ecc|len + parity.  
**Decode:** reverse. Decompress only after CRC+ECC success.

**Low-entropy alphabet (HE=0 text/DEF only):**

- Prefer P0 ASCII for labels, logs, DEF kernel strings.  
- P3: short leads for frequent Latin-ext/digits; rare scripts pay full V-width.  
- Optional compress: `comp:u8` in unit header: 0=none, 1=lz4, 2=zstd-dflt-d-1 (dict id in DEF). Never entropy-code ciphertext or random media.

---

## 6. High-entropy co-existence (P6/P7) - LOCKED

Outer ECC corrects channel noise; it does not assume low unit entropy.

1. Any P7 (`0x9C K...`) or P6 inline/chunk (kind 2/3) sets unit flag **HE=1**.  
2. HE=1 => **comp MUST be 0**. ECC still applies.  
3. Under D, multimodal is **ref-only preferred** (kind=1: hash + URI/cid). Bulk body OOB or A annex.  
4. Ciphertext/media pass opaque inside unit.  
5. Low-entropy alphabet rules apply only when HE=0.

---

## 7. Minimal kernel DEF (MTU thinking) - LOCKED

Channel model: 1-8 KiB reliable units (MAX_UNIT=8192).

| Artifact | Goal | Content |
|----------|------|---------|
| **DEF-kernel** | <= 2048 B compressed / 4096 B raw | `ASCENT/1.0\n`; plane map P0-P10; P2 leads; agent opcodes (7); MM kinds; PQ alg ids in use; ECC E/D/A table; MAX_UNIT; fail-policy id. |
| **DEF-annex** | deferred by content hash | Full prose, emoji policy, large registries (P6 ref or A fountain). |
| **Beacon DEF** | <= 512 B | profile D, RS defaults, kernel_hash 32 B, schema u8. |

Kernel MUST parse fences, skip-by-length, validate P9, resolve annex by hash. Full registry not required for cold lock.

---

## 8. Cold-start beacon vs session-after-lock - LOCKED

### Beacon (no session)

Periodic **BEACON** units (unit[0]=`0x01`):

```
0x01 | schema:u8 | profile:u8 | ecc_defaults:6B | kernel_hash:32B | period_ms:u32be | [optional kernel fragment]
```

Still wrapped in P9 sync `0xD5 0xE5 0xC0 0xDE`. Prefer I=1, small len, RS(255,223). Receiver hunts sync, decodes; if kernel_hash known, load compiled defaults; else wait for kernel unit type `0x02`. One-way broadcast legal; no handshake.

### Session-after-lock

After **N=3** good frames with matching profile+kernel_hash: enter SESSION (data `0x10`, agent, HE units). I may rise to 8. VERSION_BUMP ignored unless UPGRADE bit set; default pin first kernel. After **M=16** consecutive misses: leave SESSION, beacon hunt, erase in-flight.

---

## 9. Agent / multimodal under D (C+F notes) - LOCKED

| Topic | Rule |
|-------|------|
| Agent | Inner `0x9A`...`0x9B` only after outer OK. Fence bytes escaped per judge. |
| Opcodes | Same as E; SAFETY first-class; untrusted tools stay fenced. |
| MM | Ref-only preferred on D. Inline/chunk only HE=1, not in beacon phase. |
| Crypto (C) | P7 in HE=1 units; keys OOB; no silent PQ downgrade mid-cruise. |
| Framing (F) | P9 wraps whole unit; P1-P8 live inside; private planes cannot redefine P9. |

---

## 10. Constants

```
SYNC=D5 E5 C0 DE  PROFILE_D=0x44  MAX_UNIT=8192
RS=RS(255,223) GF(256) I=8 crc_pre=1
LDPC_OPT=AR4JA r=1/2 N_info=1024
FAIL=erase unit   COMP=compress->CRC->ECC->interleave
HE=1 => comp=0    DEF_KERNEL<=2KiB z / 4KiB raw
BEACON=type 0x01 I=1   SESSION=3 good / unlock 16 miss
```

Governance-only (non-blocking): LDPC H-matrix annex packaging; fountain ID for A; mid-cruise PQ freeze process.

---

*End wave2-deep-space. SPEC-ready for synthesizer.*
