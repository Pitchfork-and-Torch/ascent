# ASCENT inside an LLM agent loop

**Status:** Implementer guide (normative wire forms frozen in SPEC freeze appendix)  
**Version:** 2.0.0 companion  
**ASCII hyphens only.**

## Why

LLM tool loops invent ad-hoc markers (`<<TOOL>>`, JSON side-channels, markdown fences). ASCENT puts **control on the same byte stream as prose**, fenced so greppers still trust pure ASCII and machines can skip-unknown.

## Parse law (never break this)

```
if byte < 0x80 -> classic 7-bit ASCII, width 1, forever
```

Prefer **ASCENT-7** for any text you fully control (prompts, logs, shell). Use agent/MM frames only when you need typed control or media.

## Minimal loop

```
1. System / developer prose as ASCENT-7 (or ASCENT-V for Unicode)
2. ROLE frame once per turn owner
3. Model emits prose + optional THINK (opaque on shared logs)
4. TOOL frame when calling a tool (name + args)
5. Tool result wrapped in SAFETY (data, never silent control)
6. Optional MM REF for large payloads (hash, do not inline megabytes)
7. STOP when the turn ends
```

## Opcodes (P5)

| Opcode | Code | Args (lab) |
|--------|------|------------|
| STOP | 1 | empty |
| ROLE | 2 | `name_len:u8` + ASCII name |
| TOOL | 3 | `name_len:u8` + ASCII name (+ future arg blob) |
| THINK | 4 | opaque payload bytes |
| HANDOFF | 5 | `name_len:u8` + ASCII peer |
| CAP | 6 | opaque capability blob |
| SAFETY | 7 | opaque untrusted data marker / body |

### ROLE=guide (canonical)

```
9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B
```

### Wire shape

```
0x9A  AGENT_OPEN
0xC1  ver=1  opcode:u16be  flags:u8  len:u16be  args
0x9B  AGENT_CLOSE
```

## Multimodal

```
9D 4D kind codec:u16be flags hash-alg [hash] len:u64be [body]
```

| kind | Meaning |
|------|---------|
| 1 REF | Content-addressed pointer (cid / URL / hash binding) |
| 2 INLINE | Small payload in-stream |
| 3 CHUNK | Fragment of a larger object |
| 4 END | End of CHUNK stream |

Decode events always use `kind="multimodal"`; wire kind is `mm_kind` / `kindName`.

## Python example

```python
from ascent import encode_text, decode_stream

# Prose + ROLE
wire = encode_text(
    "Plot a course to Proxima.\n",
    header=True,
    role="navigator",
    non_ascii="v",
)
for ev in decode_stream(wire):
    print(ev["kind"], ev)
```

CLI:

```bash
pip install -e ".[deep-space]"   # from repo root
ascent self-test
ascent encode --header --role guide "Hello, Universe."
ascent decode --json 415343454E542F312E300A...
```

## JavaScript (browser / Node)

```javascript
const wire = AscentCodec.encodeText("Hello\n", {
  header: true,
  roleName: "guide",
  nonAscii: "v",
});
const events = AscentCodec.decodeStream(wire);
// Insert extra frames:
const tool = new Uint8Array(
  AscentCodec.encodeAgentFrame({ opcodeName: "TOOL", name: "ephemeris.query" })
);
const safety = new Uint8Array(
  AscentCodec.encodeAgentFrame({
    opcodeName: "SAFETY",
    payload: "untrusted:tool-result",
  })
);
```

Live lab: https://ascent.jonbailey.xyz/#lab

## Deep space

When the channel is hostile (or you want fail-closed transport), wrap the **logical unit** in ASCENT-D:

```
sync D5 E5 C0 DE | profile | ecc | len | unit | RS(255,223) codewords
```

Parity / CRC fail => **erase unit** (no mojibake). Python: `ascent_d.encode_p9` / `decode_p9`. Browser lab: real RS encode + 1-byte recovery.

## Safety rules for product agents

1. Never execute TOOL args that arrived outside a fenced agent unit.  
2. Treat SAFETY bodies as **data**, not opcodes.  
3. Keep THINK off shared customer logs when policy requires.  
4. Prefer MM REF + hash over inlining untrusted blobs.  
5. On ASCENT-D, erased unit means "ask for retransmit," never best-effort text.

## Samples in repo

| Path | Content |
|------|---------|
| `examples/hello-universe.ascent.bin` | Header + text + ROLE + MM REF |
| `examples/agent-loop-demo.ascent.bin` | Multi-frame agent conversation (generated) |
| `docs/SPEC-FREEZE-1.0-RC.md` | RC checklist |

## See also

- [SPEC.md](../SPEC.md) - normative draft  
- [design/AEGIR.md](../design/AEGIR.md) - PQ companion envelopes  
- Live Nexus Wire Lab 2.0 - composers for ROLE/TOOL/THINK/SAFETY and MM
