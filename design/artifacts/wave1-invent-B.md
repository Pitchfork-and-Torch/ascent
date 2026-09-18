# invent-B | wave=1 | axis=agent-native

**node:** invent-B  
**wave:** 1  
**axis:** agent-native / neural / post-LLM

---

## 1. Name

**ANSC** (Agent-Native Stream Code)  
**Expansion:** Agent-Native Stream Code  
**Manifesto:** One byte stream that agents, models, humans, and deep-space relays parse the same way: ASCII where you already are, control and multimodal planes where agents need them.

## 2. Why ANSC beats alternatives

| Candidate | Weakness vs ANSC |
|-----------|------------------|
| UTF-8-next / Unicode-N | Human-script first; agent tokens and multimodal refs stay out-of-band |
| ATE (Agent Text Encoding) | Sounds like "ate"; no stream/multimodal signal |
| NLEX (Neural Lexeme Exchange) | Lexeme bias; underplays fixed control planes and crypto |
| POST / ASC2 | Overloaded or joke sequel; no agent-native story |

ANSC is pronounceable ("ansk"), marks **agent-native** without denying human text, and names the unit of work: a **stream**, not a page of glyphs.

## 3. High-level plane map

**Fixed-width control planes** for agent/OS/crypto framing; **variable-width data planes** for scripts, emoji, payloads; **one escape ladder** so unknown planes stay stream-safe.

| Plane | Role | Rough logical range |
|-------|------|---------------------|
| P0 Classic | Byte-identical ASCII | `0x00`-`0x7F` |
| P1 C1+ | Lead / null-safe extended controls (not free text) | `0x80`-`0x9F` |
| P2 Fixed CTL | 16/32-bit agent control words (role, tool, stop, think, handoff) | lead `0xC0` + fixed 2/4 data |
| P3 Script V | Living + historical scripts (V-width; no surrogates) | multi-byte data plane |
| P4 Emoji V | Pictographs as first-class scalars | same V-width family as P3 |
| P5 MM | Multimodal refs/payloads (chunked, streamable) | lead + type + length + body/ref |
| P6 QS | Quantum-safe crypto sequences (KEM/sig, nonce, alg id) | fixed header + variable material |
| P7 META | Self-description, version, capability bits | full def can embed in-document |
| P8 DEEP | Deep-space: FEC, low-entropy pads, resync markers | framed / interleaved mode |
| P9 PRIV | Private/experimental via registered plane id | escape-registered only |

**Escapes:** ASCII ESC `0x1B` stays classic; ANSC-ESC is a distinct multi-byte lead in P2 for plane switch, length-prefixed private use, and version negotiation. Unknown planes: skip-by-length when length present; hard-fault only in strict profile.

## 4. How ASCII is embedded

Bytes `0x00`-`0x7F` are **bit-identical** to classic 7-bit ASCII (same C0, same printables, same CR/LF/TAB). Any pure-ASCII file is valid ANSC with no header. Higher planes never alias into that range for data; multi-byte sequences always start with a lead `>= 0x80` (or an ANSC control lead), so greppers, shebangs, and 7-bit-only tools keep working on the ASCII subset without reinterpretation.

## 5. Agent control + multimodal syntax (sketch)

**Agent control (in-stream, fixed after lead):**

```
C2 <opcode:u16> <flags:u8> <len:u8> [args:len]
```

Minimal opcodes: `0x0001 STOP`, `0x0002 ROLE`, `0x0003 TOOL`, `0x0004 THINK` (private CoT start/end via flags), `0x0005 HANDOFF`, `0x0006 CAP` (capability bitset).

**Multimodal marker:**

```
M5 <kind:u8> <codec:u16> <flags:u8> <len:u32> <body-or-ref>
```

`kind`: 1=image, 2=audio, 3=video, 4=tensor, 5=file-ref, 6=stream-continue. Body is inline bytes or URI/hash when `flags` mark external. CONTINUATION + sequence for chunk reassembly. Control/MM never reuse ASCII letter ranges; strip-`>=0x80` tools still see clean prose around them.

## 6. Self-description hook

A conformant ANSC definition document is itself ANSC. Plane P7 carries: magic + version (major.minor.patch + profile BASE/AGENT/DEEP); plane registry (id, fixed vs variable, max unit, skip rule); opcode and kind tables; hash of normative prose (or full text in DEEP); changelog chain (parent version hash + delta). Boot: if stream opens with P7, decoder loads tables from the document; else compiled defaults for the negotiated version. One file ships **full definition + history** with no out-of-band PDF.

## 7. Risks / open questions

1. **Lead-byte pressure** if dual-stack gateways must coexist with UTF-8-looking traffic.  
2. **THINK / private regions:** policy for opaque agent-only spans in shared logs.  
3. **Skip-unknown vs security:** lying lengths enable DoS; need max-frame and authenticated framing in QS.  
4. **Scalar policy:** import Unicode scalars 1:1 above 127 vs denser re-index (compat vs efficiency).  
5. **DEEP FEC:** mandatory default (Reed-Solomon vs LDPC); interleave depth vs latency.  
6. **PQ alg agility** without breaking old relays.  
7. **Normalization** of tool names and ROLE ids (binary exact vs fold/NFC).  
8. **Legacy C1:** keep `0x80`-`0x9F` non-text on the wire to kill Windows-1252 footguns.

---

*End invent-B wave1. Ready for plane-math, opcode registry, and DEEP FEC specialists.*
