# invent-C | wave=1 | axis=deep-space

node=invent-C  
wave=1  
axis=deep-space / interstellar / ECC-first  

---

## 1. Name

**PULSAR** - Profiled Universal Long-haul Stream with ASCII Root

**Manifesto:** An encoding is a navigation beacon: low entropy by default, error-corrected by design, and still byte-identical to 1963 ASCII for codepoints 0-127.

## 2. Why this name

- **PULSAR** is pronounceable and radio-native: a periodic beacon you lock onto when SNR is terrible.
- Beats **UTF-Next / ASCII2 / UniStream**: those advertise genealogy or width, not survival under bit flips at AU-to-light-year scale.
- Beats **Q-ASCII / ECC-ASCII**: those name a patch. PULSAR names a **profiled stream** (Earth terminal vs deep-space relay vs archive).
- Beats mission cosplay (**VOYAGER, HELIOS**): those are craft names. PULSAR is a mechanism (pulse, lock, recover).
- Fits RF tickets and dry memos without marketing fog.

## 3. High-level plane map

**Fixed-width control planes** for machine lock and ECC framing; **variable-width data planes** for text, emoji, payloads; **explicit escapes** only at plane boundaries. Defaults favor low entropy (common scripts/controls short; rare scripts pay more).

| Plane | Role | Rough range (illustrative) |
|-------|------|----------------------------|
| **C0 / ASCII** | Classic 7-bit controls + G0 graphics; untouched | `0x00-0x7F` |
| **C1-ext** | Fixed control page: stream state, profile, ECC markers, soft-sync | `0x80-0x9F` |
| **G1-short** | High-frequency non-ASCII under Earth profile short map | `0xA0-0xFF` |
| **U-plane** | Living + historical scripts, scalar emoji (no surrogates) | multi-byte; logical scalars `U+0080..` |
| **A-plane** | Agent / LLM control tokens in-band | escaped fixed tags |
| **M-plane** | Multimodal refs and inline payload frames | length-prefixed after marker |
| **K-plane** | Quantum-safe crypto control (alg id, kid, nonce, sealed blob) | fixed header + var ciphertext |
| **E-plane** | Outer ECC framing (sync, RS/LDPC params, interleave, profile) | wraps units / documents |
| **S-plane** | Self-description: standard text, version history, registries | bootstrap unit + annexes |

**Profiles:** `PULSAR-E` (Earth, light ECC optional), `PULSAR-D` (deep-space: strong outer ECC, long sync, low-entropy defaults on), `PULSAR-A` (archive: max self-description + hash chain).

Rule: if a byte stream is ASCII printable, it **is** ASCII printable. Higher planes only via `>= 0x80` or documented multi-byte leads that never remap 0-127.

## 4. How ASCII is embedded

Codepoints **0-127** are **byte-identical and semantic-identical** to classic 7-bit ASCII (NUL through DEL). No overloading of `0x00-0x7F`. Any PULSAR document that uses only that set is valid classic ASCII and valid PULSAR under the Earth profile. Higher planes use high bytes or C1-ext escapes outside the 7-bit graphic set. ASCII-only decoders remain correct on the subset; they must not remap 0-127.

## 5. Agent control + multimodal markers (sketch)

Introducers outside pure ASCII body (or C1 + ASCII for human logs):

- **Agent:** `0x9A` `A` `<kind:1>` `<flags:1>` `<ulen:u16be>` `<body>`  
  Kinds: `01` system, `02` user, `03` assistant, `04` tool_call, `05` tool_result, `06` think, `07` end, `08` safety.  
  Body: UTF-8 name/args or M-plane ref. No surrogate pairs; emoji are U-plane scalars / sequences.

- **Multimodal:** `0x9B` `M` `<type:1>` `<hash-alg:1>` `<hash:N>` `<len:u64be>` `[chunk...]`  
  Types: `01` ref-only, `02` inline, `03` chunk continue, `04` end. Streamable: handle may issue before all chunks arrive.

- **Crypto:** `0x9C` `K` `<alg:u16>` `<kid>` `<nonce>` `<ct>` - alg IDs from S-plane PQ registry.

- **Deep-space outer frame:** sync `0xD5 0xE5 0xC0 0xDE` + profile + ECC params + len + payload + parity.  
  If parity fails: erase the unit. No best-effort mojibake.

Debug (non-normative): `[A:tool_call]...[/A]`, `[M:image/png;sha256=...]`, `[K:mlkem768]`.

## 6. Self-description hook

One valid PULSAR document **may** carry (reference standard **must** carry):

1. **Bootstrap unit** (S-plane): magic, version, profile table, plane map, escape grammar, content hash of normative prose.
2. **Full definition** as U-plane/UTF-8 text in-band, plus version history as append-only `(version, date, delta-hash, parent-hash)`.
3. **Machine tables:** script blocks, agent kinds, crypto algs, ECC profile parameters.

Rule: recover this file under `PULSAR-D` and you hold the standard. Optional K-plane signature seals the bundle. The standard is not a PDF elsewhere; it is a self-validating PULSAR artifact.

## 7. Risks / open questions

1. **C1 / `0x80-0x9F` collisions** with Windows-1252 misdecode: strict mode + Earth detection heuristic required.
2. **Outer ECC family** (RS vs LDPC vs fountain): pick per profile, not one global code.
3. **In-band agent abuse** (prompt injection): safety kind + framing for untrusted tool results; policy is out of band, hooks are not.
4. **Emoji ZWJ / grapheme equality** and ECC unit boundaries without surrogates.
5. **S-plane size vs deep-space MTU:** minimum recoverable core vs compressed annexes under ECC.
6. **PQ alg agility** without silent downgrade; freeze process for mid-cruise probes.
7. **Low-entropy defaults** must not crush high-entropy K/M ciphertext; define compressor vs ECC layering.
8. **Cold-start beacon** (no handshake) vs session mode after lock.

---

*End invent-C. Sketch for plane, ECC, and self-hosting specialists.*
