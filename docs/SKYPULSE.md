# ASCENT SkyPulse

**Status:** Additive (architecture card / ascent-wire **2.1.0**). SPEC 1.0.0-rc1 parse law unchanged.  
**Unit:** PATHHINT / SKYSTATE (`0xC5`, schema `0x01`)  
**Profiles:** usage note **ASCENT-E-LEO** vs **ASCENT-D** (not a new P0-P2 grammar)

ASCII hyphens only.

---

## What it is

SkyPulse is a **path foresight unit** for LEO IP sessions (Starlink and similar).
It carries a compact, fail-closed hint:

- `path_id` / epoch
- `next_capacity_bps` (application goodput *seed*, not RF PHY rate)
- `freeze_ms` (relative growth-freeze window for CCA / senders)
- `confidence` in `[0, 1]`
- `ttl_ms`
- optional `obstruction` in `[0, 1]`
- optional `elev_deg`
- flags (kbps units, CRC present, field presence)

Apps and congestion control can **slow down, freeze CWND growth, or QUEUE**
instead of spraying retransmits across a 15-second LEO reconfig or a tree
obstruction. That is **usable goodput and session continuity**, not a faster radio.

## What it is not (honesty fence)

| Claim | Allowed? |
|-------|----------|
| ASCENT increases Starlink physical downlink/uplink Mbps | **No** |
| "Grok offline in space forever" | **No** |
| PATHHINT is a measured RF throughput | **No** - it is a hint |
| Dual-gate LeoAware product wins | **No** - see OrbitStack bridge |
| Replace Starlink networking / Dishy firmware | **No** |

Allowed: better application goodput, fewer wasted retransmits, foresight for
CCA/apps, LEO-efficient framing, fail-closed integrity.

## Wire (additive, skip-by-length)

Assigned from reserved P2 leads `0xC4-0xCE`. Cont class `0xA0-0xBF` stays frozen.

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
next_capacity:u32be     # bps, or kbps if FLAG_CAP_KBPS
freeze_ms:u32be         # relative (FLAG_RELATIVE_FREEZE always set in v1)
confidence:u16be        # 0..10000 => [0.0000, 1.0000]
ttl_ms:u32be
obstruction:u8          # 0..255 => [0,1] if FLAG_HAS_OBSTRUCTION; else 0xFF
elev_deg_x10:i16be      # degrees * 10; 0x7FFF absent
[crc32:u32be]           # IEEE CRC-32 of the 26-byte prefix
```

**Fail-closed:** unknown schema, reserved flags, bad length, CRC fail, or
truncated body after a readable `len` => **skip unit, do not apply**. Truncation
before `len` is a hard-fault (SPEC stream truncation rule). Same spirit as
ASCENT-D erase-on-fail: never feed a corrupt hint into CCA.

Optional **P9 wrap** (`D5 E5 C0 DE` + RS(255,223)) when integrity is requested
(spool / deep-space). Plain unit is the Earth / LEO IP lab default.

Goldens: `tests/skypulse_vectors.json`.

## ASCENT-E-LEO vs ASCENT-D

| | ASCENT-E-LEO | ASCENT-D |
|--|--------------|----------|
| Parse law | Same E grammar + PATHHINT | Same + mandatory P9 |
| Interactive Starlink IP | **Yes** | Poor fit (RS tax + latency) |
| Integrity | Light PATHHINT CRC or none (TLS already) | RS(255,223) erase-on-fail |
| Double FEC | **Forbidden as required** | P9 is the outer ECC; skip extra PATHHINT CRC |
| Use | Chat/agent turns, PATHHINT, QUEUE | Spool files, deep-space, high BER |

`recommend_integrity("ASCENT-E-LEO")` vs `recommend_integrity("ASCENT-D")`
in `ref/ascent_skypulse.py`.

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
| Policy | `ref/ascent_skypulse.py` |
| JS | `site/public/ascent_codec.js` / `packages/ascent-js` |
| SPEC | `SPEC.md` appendix SkyPulse (append-only) |
| LeoAware | `docs/ORBITSTACK-LEOAWARE-BRIDGE.md` |
