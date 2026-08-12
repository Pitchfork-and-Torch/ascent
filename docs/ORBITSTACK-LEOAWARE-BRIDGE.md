# OrbitStack / LeoAware bridge (PATHHINT)

**Status:** Implementer note for Pitchfork-and-Torch OrbitStack. Not a product claim.  
**ASCENT side:** SkyPulse PATHHINT (`0xC5` schema `0x01`), architecture **2.1.0**  
**Honesty:** PATHHINT does not raise Starlink RF Mbps. Dual-gate LeoAware remains
a **product fence** for paid OrbitStack; this document does not grant it.

ASCII hyphens only.

---

## What LeoAware should consume

Treat a successfully **applied** PATHHINT as a *seed*, never as ground truth:

| PATHHINT field | LeoAware use |
|----------------|--------------|
| `next_capacity_bps` | Seed / cap for the **next** send window. Do not treat as measured PHY rate. |
| `freeze_ms` | **Freeze growth** (CWND / pacing increase) until local now + freeze_ms. Still allow decrease on loss. |
| `confidence` | Blend weight. Low confidence => ignore or decay fast. |
| `ttl_ms` | Hint expires. After TTL, revert to local estimator. |
| `obstruction` | Optional QUEUE / hold-new-data signal for the app. Not a loss-burst synonym. |
| `elev_deg` | Diagnostic / logging. Do not gate recovery on elevation alone. |
| `path_id` | Epoch. New id => drop stale hint. |
| `applied=false` | **Fail-closed:** erase/skip. Do not apply. |

Corrupt, unknown schema, CRC fail, reserved flags, or expired TTL => **no hint**.
Local loss/RTT estimators keep running.

## Never gate `loss_burst` REPROBE

PATHHINT must **not** suppress loss-burst reprobes:

1. A LEO handoff can look like a burst even when the hint still says "freeze".
2. If LeoAware skips REPROBE because `freeze_ms` is live, recovery stalls and
   goodput collapses - the opposite of SkyPulse's job.
3. Freeze applies to **growth**, not to loss response.

Normative intent for this bridge:

```
on PATHHINT applied:
    seed next_capacity if confidence >= floor
    freeze_growth_until = now + freeze_ms
    do not set "ignore loss_burst"
    do not disable REPROBE

on loss_burst:
    REPROBE as usual (absolute dual-gate still product-fenced)
    PATHHINT freeze does not cancel this
```

## Absolute dual-gate (product fence)

OrbitStack's paid LeoAware **absolute dual-gate** (whatever the current product
name: dual signal before growth, dual signal before certain probes) stays behind
the product fence. Open ASCENT SkyPulse:

- **Does** ship PATHHINT encode/decode, fail-closed skip, LEO-IP vs D integrity.
- **Does not** implement, enable, or claim dual-gate wins in this repo.
- Integrators may *read* PATHHINT in an open client; dual-gate logic remains
  OrbitStack product code.

Do not market "ASCENT unlocks dual-gate" or "LeoAware is faster because of ASCENT".

## Fail-closed mapping

| Event | Action |
|-------|--------|
| Applied PATHHINT | Seed + freeze growth; log path_id |
| Skip / CRC fail / unknown | Ignore hint; no state change |
| TTL expiry | Drop hint; keep local CCA |
| New path_id | Replace hint; do not merge stale freeze |
| P9 wrap fail (if used) | Erase unit (ASCENT-D policy); no hint |

## Integrity choice

On Starlink IP, LeoAware should consume **plain or CRC PATHHINT** (ASCENT-E-LEO).
Do not require P9 RS on the interactive path. P9 is for spool/deep-space ADUs.

## References

- `docs/SKYPULSE.md`
- `docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md`
- `ref/ascent_skypulse.py` (`recommend_integrity`, `should_queue_session`)
- SPEC appendix SkyPulse
