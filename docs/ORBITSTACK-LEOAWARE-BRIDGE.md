# OrbitStack / LeoAware bridge (PATHHINT)

**Status:** Implementer note for Pitchfork-and-Torch OrbitStack. Not a product claim.  
**ASCENT side:** SkyPulse PATHHINT (`0xC5` schema `0x01`), architecture **2.1.0**  
**Honesty:** PATHHINT does not raise Starlink RF Mbps. Dual-gate LeoAware remains
a **product fence** for paid OrbitStack; this document does not grant it.
ASCENT ship success is goldens / round-trip / erase-on-fail / overhead / apply
vs reject - not "+X Mbps Starlink" and not LeoAware dual-gate.

ASCII hyphens only.

**Ship order:** (a) SPEC appendix + goldens + ascent-wire 2.1.0, (b) Wire Lab
panel, (c) publish PATHHINT codec, (d) LeoAware later. Do not claim OrbitStack
paid wins from this repo.

---

## Hybrid fuse contract (normative for this bridge)

PATHHINT is an **assist seed**. Orb pathID still owns recovery. Do not invent a
second cutter.

| Rule | Contract |
|------|----------|
| Seed | An **applied** PATHHINT MAY seed `freeze_until` (growth freeze) and `next_capacity` (predicted sender bottleneck bits/s). |
| Owner | Orb **pathID / epoch** still owns **REPROBE** when not suppressed. A new path_id replaces the hint; it does not merge stale freeze. |
| Assist suppress | After a PATHHINT assist, suppress re-assist for about **2 seconds**. Do not stack a hybrid utilization multiplicative decrease (util-MD) on the same event. One cut. |
| Predictive pre-hop freeze | Growth freeze **only**. **Never** gate `ep:loss_burst`. Loss-burst REPROBE stays on the Orb pathID path. |
| Fail-closed | CRC / short-RS fail, stale TTL, unknown version/schema, reserved flags, bad length => **erase**. Never act on a corrupt unit. |

```
on PATHHINT applied (confidence >= floor, TTL live, path_id known):
    seed next_capacity = predicted bottleneck bits/s as seen by the sender
    freeze_growth_until = now + freeze_ms
    start assist_suppress ~ 2s
    do not set "ignore ep:loss_burst"
    do not disable REPROBE
    do not apply a second util-MD for the same hint

on ep:loss_burst:
    REPROBE as usual when Orb pathID has not suppressed it
    PATHHINT freeze does not cancel this
    absolute dual-gate remains product-fenced

on assist_suppress window:
    do not re-seed freeze / next_capacity from a duplicate hint
    do not invent a hybrid util-MD "double-cut"
```

## What LeoAware should consume

Treat a successfully **applied** PATHHINT as a *seed*, never as ground truth:

| PATHHINT field | Required? | LeoAware use |
|----------------|-----------|--------------|
| `next_capacity` | yes | Predicted **bottleneck bits/s as seen by the sender**. Seed / cap for the next send window. **Not** RF PHY rate. |
| `freeze_until` (`freeze_ms` relative on v1 wire) | yes | **Freeze growth** (CWND / pacing increase) until local now + freeze_ms. Still allow decrease on loss. |
| `path_id` / epoch | yes | Epoch. New id => drop stale hint. Orb pathID still owns REPROBE. |
| `confidence` | yes | Blend weight. Low confidence => ignore or decay fast. |
| `ttl_ms` | yes | Hint expires. Stale TTL => erase. After TTL, revert to local estimator. |
| `obstruction` | optional | QUEUE / hold-new-data signal for the app. Not a loss-burst synonym. |
| `elev_deg` | optional | Diagnostic / logging. Do not gate recovery on elevation alone. |
| `applied=false` | - | **Fail-closed:** erase/skip. Do not apply. |

Corrupt, unknown schema, CRC/short-RS fail, reserved flags, missing freeze_until,
or expired TTL => **no hint**. Local loss/RTT estimators keep running.

## Never gate `ep:loss_burst` REPROBE

PATHHINT must **not** suppress loss-burst reprobes:

1. A LEO handoff can look like a burst even when the hint still says "freeze".
2. If LeoAware skips REPROBE because `freeze_ms` is live, recovery stalls and
   usable session bandwidth collapses - the opposite of SkyPulse's job.
3. Predictive pre-hop freeze applies to **growth**, not to loss response.

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
| Applied PATHHINT | Seed + freeze growth; log path_id; start ~2s assist suppress |
| Skip / CRC fail / short-RS fail / unknown | Erase; no state change |
| TTL expiry | Erase hint; keep local CCA |
| New path_id | Replace hint; do not merge stale freeze; Orb pathID owns REPROBE |
| P9 wrap fail (if used) | Erase unit (ASCENT-D policy); no hint |

## Integrity choice

On Starlink IP/QUIC, LeoAware should consume **light integrity**: PATHHINT CRC
(v1 shipped) **or** short RS(255,239) I=1 as a substitute, never stacked.
Do not require full RS(255,223) P9 on the interactive path. Full P9 is for
spool / deep-space / high-BER only (ASCENT-D).

## Sacred-meter

Observational (`obs`) only when a real dish/API exists. Lab env overrides and
Wire Lab meters are **sim**. This repo does not invent a fake Starlink
telemetry API. TCP :9200 is reachability, not PHY rate.

## References

- `docs/SKYPULSE.md`
- `docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md`
- `ref/ascent_skypulse.py` (`recommend_integrity`, `evaluate_pathhint`, `should_queue_session`)
- SPEC appendix SkyPulse
