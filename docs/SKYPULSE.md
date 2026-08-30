# ASCENT SkyPulse

**Status:** Additive (architecture card / ascent-wire **2.1.0**). SPEC 1.0.0-rc1 parse law unchanged.  
**Unit:** PATHHINT / SKYSTATE (`0xC5`, schema `0x01`)  
**Profiles:** usage note **ASCENT-E-LEO** vs **ASCENT-D** (not a new P0-P2 grammar)

ASCII hyphens only.

---

## Honesty fence

ASCENT does **not** raise Starlink physical RF Mbps. SkyPulse is for **usable
session bandwidth**, session continuity, and control overhead under LEO.
Never market a bare "bandwidth upgrade."

## What it is

SkyPulse is a **path foresight unit** for LEO IP sessions (Starlink and similar).
It carries a compact, fail-closed hint. Normative field semantics:

| Field | Required | Meaning |
|-------|----------|---------|
| `next_capacity` | yes | **Predicted bottleneck bits/s as seen by the sender.** Not RF PHY rate. |
| `freeze_until` | yes | Growth-freeze window. v1 wire is relative `freeze_ms` (`FLAG_RELATIVE_FREEZE`). Semantic freeze_until = now + freeze_ms. |
| `path_id` / epoch | yes | Path or epoch. Unknown/new id replaces stale hint. |
| `confidence` | yes | `[0, 1]` blend weight. |
| `ttl_ms` | yes | Hint lifetime. Stale TTL => erase (consumer-side). |
| `obstruction` | optional | `[0, 1]` if present. |
| `elev_deg` | optional | Degrees if present. |

Apps and congestion control can **slow down, freeze CWND growth, or QUEUE**
instead of spraying retransmits across a 15-second LEO reconfig or a tree
obstruction. That is **usable session bandwidth and session continuity**, not a
faster radio.

## What it is not (honesty fence)

| Claim | Allowed? |
|-------|----------|
| ASCENT increases Starlink physical downlink/uplink Mbps | **No** |
| Bare "bandwidth upgrade" | **No** - say **usable session bandwidth** |
| "Grok offline in space forever" | **No** |
| PATHHINT is a measured RF throughput | **No** - predicted sender bottleneck |
| Dual-gate LeoAware product wins | **No** - see OrbitStack bridge |
| Replace Starlink networking / Dishy firmware | **No** |
| Invented Starlink telemetry API | **No** |

Allowed: usable session bandwidth, fewer wasted retransmits, foresight for
CCA/apps, LEO-efficient framing, fail-closed integrity.

## Wire (additive, skip-by-length)

Assigned from reserved P2 leads `0xC4-0xCE`. Cont class `0xA0-0xBF` stays frozen.
No P0-P2 parse-law break. SPEC stays **1.0.0-rc1 + this appendix**.

```
0xC5                    # SKYSTATE lead
schema:u8               # 0x01 = PATHHINT v1
len:u16be               # body length (v1: 26 or 30 with CRC)
body
```

PATHHINT v1 body (26 bytes, +4 IEEE CRC-32 if `FLAG_CRC`):

```
flags:u8
path_id:u64be
next_capacity:u32be     # predicted sender bottleneck; bps, or kbps if FLAG_CAP_KBPS
freeze_ms:u32be         # relative freeze_until (FLAG_RELATIVE_FREEZE always set in v1)
confidence:u16be        # 0..10000 => [0.0000, 1.0000]
ttl_ms:u32be
obstruction:u8          # 0..255 => [0,1] if FLAG_HAS_OBSTRUCTION; else 0xFF
elev_deg_x10:i16be      # degrees * 10; 0x7FFF absent
[crc32:u32be]           # IEEE CRC-32 of the 26-byte prefix
```

**Fail-closed (never act on corrupt units):**

| Condition | Action |
|-----------|--------|
| CRC fail or short-RS fail | **erase** (`applied=false`) |
| Stale TTL | **erase** (consumer `evaluate_pathhint`) |
| Unknown schema / version | **erase** (skip-by-length) |
| Missing `FLAG_RELATIVE_FREEZE` | **erase** (`missing_freeze_until`) |
| Reserved flags, bad length, confidence > 10000 | **erase** |
| Truncation before `len` is readable | hard-fault (SPEC stream rule) |

Goldens: `tests/skypulse_vectors.json`. Canonical 50e6 bps is a **hint**, not RF.

## LEO-IP vs ASCENT-D integrity (when each applies)

Do not stack CRC + RS. Pick one profile.

| | ASCENT-E-LEO (Starlink IP/QUIC) | ASCENT-D |
|--|--------------------------------|----------|
| Parse law | Same E grammar + PATHHINT | Same + mandatory P9 |
| Interactive Starlink IP | **Yes** | Poor fit (RS tax + latency) |
| Integrity | **Light:** PATHHINT CRC (v1 shipped) **or** short RS(255,239) I=1 as a substitute, never stacked | Full RS(255,223) P9 erase-on-fail |
| Double FEC | **Forbidden as required** | P9 is the outer ECC; skip extra PATHHINT CRC |
| Use | Chat/agent turns, PATHHINT, QUEUE | Spool files, deep-space, high BER |

`recommend_integrity("ASCENT-E-LEO")` vs `recommend_integrity("ASCENT-D")`
in `ref/ascent_skypulse.py`. Short RS is an allowed LEO-IP substitute, not a
new v1 wire flag.

## ASCENT ship success metrics

Separate from LeoAware dual-gate. **Not** "+X Mbps Starlink."

| Metric | v1 target |
|--------|-----------|
| Goldens Py ≡ JS | `tests/skypulse_vectors.json` + `tests/run_js_lock.js` |
| PATHHINT round-trip | encode/decode fields match; PathHint.encode() == wire |
| Erase-on-fail | CRC flip, unknown schema, missing freeze, stale TTL => `applied=false` |
| Overhead bytes/hint | **30** plain, **34** with CRC |
| Apply vs reject | lab samples: 2 applied / 2 rejected in `test_ship_metrics_not_rf` |

## Ship order

1. SPEC appendix + goldens + ascent-wire **2.1.0**
2. Wire Lab panel (meters labeled **sim**)
3. Publish PATHHINT codec (PyPI/npm later; Jon gated)
4. LeoAware later (OrbitStack product; not this PR)

Do not claim OrbitStack paid wins. Live site deploy still needs Jon approval.

## Sacred-meter

Observational (`obs`) only when a real dish/API exists. Wire Lab and lab env
overrides are **sim**. TCP :9200 is reachability, not a telemetry API.

## Quick start

```bash
PYTHONPATH=ref python -c "from ascent_codec import canonical_pathhint_bytes, decode_stream; print(decode_stream(canonical_pathhint_bytes()))"
python -m ascent pathhint --profile ASCENT-E-LEO
python tests/test_skypulse.py
node tests/run_js_lock.js
```

Client: `examples/ascent_starlink_client/daemon.py --pathhint`

## Implementers

| Surface | Location |
|---------|----------|
| Python wire | `ref/ascent_codec.py` (`encode_pathhint`, `decode_skystate`) |
| Policy | `ref/ascent_skypulse.py` (`evaluate_pathhint`, `recommend_integrity`) |
| JS | `site/public/ascent_codec.js` / `packages/ascent-js` |
| SPEC | `SPEC.md` appendix SkyPulse (append-only) |
| LeoAware | `docs/ORBITSTACK-LEOAWARE-BRIDGE.md` (hybrid fuse) |
