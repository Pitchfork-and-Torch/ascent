# ASCENT 1.0 Release Candidate checklist

**Goal:** Freeze implementer-critical wire forms so multi-language codecs stay bit-identical.  
**SPEC status today:** `1.0.0-rc1`  
**Architecture / Nexus site:** `2.1.0` (SkyPulse additive; Cont freeze unchanged)  
**Packing:** Cont `0xA0-0xBF` (5-bit) frozen  
**RC date:** 2026-07-31  

## RC sign-off

| Gate | Status |
|------|--------|
| Python goldens | PASS (`tests/test_ascent_codec.py`) |
| JS/Python lock | PASS (`node tests/run_js_lock.js`) |
| Hello Universe 132 B | PASS |
| P9 encode match freeze | PASS |
| 1-byte P9 recovery | PASS |
| Public single-commit | PASS |
| Live Nexus 2.0 | PASS |

## Locked forms (do not change without major version)

### Parse law

- `byte < 0x80` => classic ASCII width 1 forever  
- No overlongs of `0x00-0x7F`  
- No UTF-16 surrogates on the wire  
- Multi-byte integers big-endian  

### ASCENT-V

| Form | Lead | Trail | Range |
|------|------|-------|-------|
| 2-byte | `D0-DF` | 1 Cont | U+0080..027F |
| 3-byte | `E0-EF` | 2 Cont | U+0280..427F |
| 4-byte | `F0-F4` | 3 Cont | from U+4280 when residual fits |
| LONG | `F5 03` | u24be | remaining scalars |

Goldens: `caf\u00e9` -> `636166D3A9`; U+1F680 -> `F3ADA0A0`  
Encoding guard: LONG `F503000041` reject overlong; first legal LONG U+2C280 -> `F50302C280` (`tests/encoding_guard_vectors.json`)

### Agent frame

```
9A C1 ver opcode:u16be flags len:u16be args 9B
```

ROLE=guide: `9AC10100020000060567756964659B`  

Opcodes 1..7: STOP ROLE TOOL THINK HANDOFF CAP SAFETY  

### Multimodal

```
9D 4D kind codec flags hash-alg hash len:u64be body
```

Event type string always `multimodal`; wire kind in `mm_kind`.

### ASCENT-D outer

```
D5 E5 C0 DE | profile | family n k interleave crc_pre | len:u32be | unit | RS codewords
```

Default RS(255,223) GF(256) poly 0x11d (reedsolo). Erase-on-fail.  

Golden: `tests/freeze_vectors.json` key `p9_hello_frame_hex` (297 B for Hello unit with header).

## RC gate (all must be green)

| # | Check | How |
|---|--------|-----|
| 1 | Python goldens | `PYTHONPATH=ref py -3 tests/test_ascent_codec.py` |
| 2 | JS/Python lock | `node tests/run_js_lock.js` |
| 3 | Hello Universe 132 B | `ascent self-test` / decode CLI |
| 4 | P9 encode match | freeze_vectors p9 hex |
| 5 | 1-byte P9 recovery | JS lock + Python satellite lab |
| 6 | No em/en dash product copy | utf8-hygiene scrub |
| 7 | Public history | single commit, secret scan |
| 8 | Live site | ascent.jonbailey.xyz Wire Lab 2.0 |

## Freeze vectors file

`tests/freeze_vectors.json` - regenerate with:

```bash
set PYTHONPATH=ref
py -3 -c "exec(open('tests/gen_freeze_vectors.py',encoding='utf-8').read())"
```

(or the inline generator used in the monorepo session)

## After RC

1. Tag SPEC `1.0.0-rc1` in SPEC.md header (content freeze)  
2. Keep Nexus site on 2.x for UI-only bumps  
3. Publish `ascent-wire` to PyPI when package metadata reviewed  
4. Add npm `@pitchfork/ascent` mirroring `site/public/ascent_codec.js`  

## Explicitly still draft (OK for RC)

- Full AEGIR hybrid production (DEMO golden only for CI)  
- LDPC alternate ECC  
- Private plane registries  
- CHUNK reassembly multi-stream stress tests beyond SPEC prose  
- SkyPulse PATHHINT (`0xC5`) is **additive** after RC (appendix); does not thaw Cont or P9 goldens  
