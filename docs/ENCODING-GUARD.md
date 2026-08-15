# ASCENT encoding guard (LONG overlongs)

**Status:** Implementer note (normative rules already in SPEC C.4.1)  
**ASCII hyphens only.**

## Hole

SPEC 1.0.0-rc1 already says decoders MUST reject:

- overlong multi-byte encodings of ASCII (`0x00-0x7F`)
- non-minimal width when a shorter 2/3/4-byte ASCENT-V form can represent the same scalar

Short 2/3/4-byte forms have disjoint residual ranges, so they cannot smuggle ASCII. The only remaining path was LONG (`F5 03` + `cp:u24be`). Reference decoders accepted LONG payloads for scalars that belong on P0 or in a shorter V form, including `F5 03 00 00 41` (overlong `A`).

That is the UTF-8 overlong class on this wire: a filter that only looks at single-byte `0x00-0x7F` can miss an ASCII codepoint hidden in five bytes.

## Guard

LONG is legal only when the shortest form is LONG:

| Form | Scalars |
|------|---------|
| P0 | `U+0000..U+007F` |
| 2-byte | `U+0080..U+027F` |
| 3-byte | `U+0280..U+427F` |
| 4-byte | `U+4280..U+2C27F` (`v < 5<<15`) |
| LONG | `U+2C280..U+10FFFF`, not a surrogate |

Decoders MUST reject LONG otherwise. Encoders already emit the shortest form.

## Goldens

Shared file: `tests/encoding_guard_vectors.json`.

| Hex | Result |
|-----|--------|
| `F5 03 00 00 41` | reject overlong ASCII (`A`) |
| `F5 03 00 00 00` | reject overlong ASCII (NUL) |
| `F5 03 00 00 E9` | reject non-minimal (cafe is `D3 A9`) |
| `F5 03 01 F6 80` | reject non-minimal (rocket is `F3 AD A0 A0`) |
| `F5 03 02 C2 80` | accept U+2C280 (first legal LONG) |
| `F4 BF BF BF` | accept U+2C27F (last 4-byte) |

## Wire Lab

Nexus gallery sample **Encoding guard** loads `F503000041`. Decode status must show a hard fault, not the letter A.

Live: https://ascent.jonbailey.xyz/#lab

## Not a new protocol

No new lead, opcode, or profile. Cont freeze `0xA0-0xBF` is unchanged. This is the existing C.4.1 illegal list, now enforced and tested.
