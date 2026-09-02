# invent-A | wave 1 | axis=heritage-ascent

**node:** invent-A  
**wave:** 1  
**axis:** heritage-ascent  

---

## Proposed NAME

**ASCENT** - ASCII Successor with Compatible Encoding of Named Text

**Full expansion:** American Standard Code for Extended Named Text (working committee title: ASCENT)

**Manifesto:** Keep every classic ASCII byte sacred, then ascend the rest of human writing, agents, media refs, and deep-space links into one self-describing stream.

Pronunciation: /uh-SENT/ (ascent). Committee shorthand: "ASCENT-7" for the 7-bit identity plane, "ASCENT-n" for version n of the full standard.

---

## Why this name beats obvious alternatives

| Candidate | Problem |
|-----------|---------|
| ASCII2 / ASCII++ | Sounds like a fork, not a successor; implies breakage |
| UNICODE-next / UTF-n | Already overloaded; fights ISO/Unicode politics |
| UCS / Universal Character Stream | Cold; no nod to the 1963 root |
| PAX (Portable All-scripts eXchange) | Cute but no ASCII DNA in the letters |
| SEVEN+ / Extended ASCII | Historically polluted (code pages 437/850 chaos) |

**ASCENT** keeps the **ASC** stem that everyone already types and greps, adds **ENT** as "encoded named text," and the ordinary English word *ascent* states the design story: climb from 7-bit roots without abandoning them. Slightly witty for a standards body, still solemn enough for ISO/IEC paperwork.

---

## High-level plane map

Philosophy: **fixed-width control planes** for machine safety; **variable-width data planes** for human text and payloads; **escapes that never collide with 0x00-0x7F single bytes**.

| Plane | Rough role | Sketch (not normative) |
|-------|------------|-------------------------|
| P0 Identity | Classic 7-bit ASCII, byte-identical | `0x00-0x7F` single-byte, forever |
| P1 Control Fixed | C0/C1-class + ASCENT ESC chains; agent/LLM control; quantum-safe crypto control sequences | Multi-byte only via ESC (`0x1B`) or designated lead-ins outside P0 |
| P2 Scripts Core | All living languages + major historical scripts as first-class code units (no surrogates) | Variable-width (2-4 units typical); scalar values, not UTF-16 pairs |
| P3 Emoji & Symbols | Full emoji, ZWJ sequences as atomic named clusters where useful | Same width model as P2; no surrogate pair encoding in the wire form |
| P4 Multimodal | Streamable refs and inline payloads (image/audio/sensor chunks) | Marker + length + type + body or URI-ref |
| P5 Self-Desc | Standard body, registries, version history | Documents that *are* the spec |
| P6 Deep-Space | Low-entropy defaults, FEC blocks, sync markers | Profile, not a separate encoding |

**Escapes:** ESC + F-byte selects plane/mode; ST (string terminator) ends delimited constructs. Data planes never emit lone `0x00-0x7F` as multi-byte trailers that could be misread as ASCII.

---

## How ASCII is embedded

Codepoints (and wire bytes) 0 through 127 are **bit-for-bit identical** to classic 7-bit ASCII (ANSI X3.4-1963 / ISO 646 IRV). Any pure-ASCII file is a valid ASCENT document of the identity profile. Decoders MUST treat every `0x00-0x7F` byte as that ASCII character with no multi-byte recombination. All extensions begin only at designated lead sequences or at byte values outside that range, so greppers, `cat`, SMTP 7-bit paths, and legacy C string tools keep working on the ASCII subset without a version flag.

---

## Agent control + multimodal marker syntax (sketch)

Minimal concrete forms (illustrative; F-bytes TBD by control-plane committee):

```
ESC A C T ; role=system ; id=... ST
...control payload bytes...
ESC A C T / ST

ESC M M R ; type=image/webp ; transfer=ref ; uri=cid:chunk-9 ST
ESC M M R ; type=audio/opus ; transfer=inline ; len=4096 ST
<4096 bytes>
```

Rules of thumb:
- Control tokens live in the **same byte stream** as text (no side channel required).
- Names are ASCII letters inside the marker so logs stay readable.
- Multimodal: either **ref** (URI/cid) or **inline** (length-prefixed body).
- Crypto control (e.g. `ESC Q S C ; alg=ML-KEM-768 ; ... ST`) carries algorithm ids and nonces only; key material rules are profile-specific.

---

## Self-description hook

An ASCENT **normative document** is itself an ASCENT file whose P5 region (or a whole-file profile) embeds:
1. Machine-readable registry (code units, plane map, ESC tables)
2. Human-readable prose of the standard
3. Append-only **version history** blocks (hash-chained)

A single valid file can therefore ship "the full definition + history." Conformance tests may require that `ascent --self-describe` extract P5 and re-validate the decoder against the embedded tables. Bootstrapping: identity-plane ASCII subset of the self-desc header is enough to find the version magic and length, then load the rest.

---

## Deep-space profile (constraint 5)

Profile **ASCENT-DS**: low-entropy default alphabet for telemetry text; fixed sync words; Reed-Solomon or LDPC FEC frames around logical records; optional repeat of P5 digest at frame headers so a partial receive can still recover the dictionary. Ground systems may strip FEC and re-emit pure ASCENT-core.

---

## Risks / open questions (for later specialists)

1. **Unicode coexistence:** map or dual-stack? 1:1 BMP/SMP import vs clean-room scalars.
2. **ESC collision surface:** legacy VT/ANSI sequences vs ASCENT F-byte discipline; need a reserved private-use ESC tree.
3. **Emoji atomicity:** when is a ZWJ sequence one "character" for agents vs display?
4. **Inline multimodal DoS:** max length, sandbox, and content-hash binding to refs.
5. **Quantum-safe control:** which PQ algorithms are mandatory in the base registry vs profiles.
6. **Self-desc circularity:** how a decoder validates the embedded spec without already knowing version N+1.
7. **IP / governance:** ISO vs IETF vs joint; trademark "ASCENT" clearance.
8. **Efficiency vs safety:** variable-width min size for CJK/emoji vs fixed-width agent control pads.

---

*End invent-A wave1. Ready for plane formalization and name collision search.*
