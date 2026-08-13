# ascent-wire 2.1.0 (SkyPulse) - release notes draft

**Do not publish to PyPI/npm from this PR unless Jon asks.** Version bumps and
goldens are in-tree. Live site `ascent.jonbailey.xyz` needs Jon's Cloudflare
Pages approval. Do not merge this PR from the agent.

## Honesty fence

ASCENT is a wire encoding + agent/control grammar. This release does **not**
increase Starlink physical downlink/uplink Mbps. SkyPulse improves **usable
session bandwidth**, session continuity, and control overhead under LEO
(PATHHINT foresight, fail-closed skip, LEO-efficient framing). No bare
"bandwidth upgrade." No "Grok offline in space forever".

## SCIENCE-OK hard amends (this PR)

1. **Append-only / freeze.** No P0-P2 break. Cont `0xA0-0xBF` freeze stays.
   Wire package **2.1.0**. SPEC stays **1.0.0-rc1 + SkyPulse appendix**.
2. **PATHHINT field semantics (normative).** `next_capacity` = predicted
   bottleneck bits/s as seen by the sender, **not** RF PHY. Required:
   freeze_until, path_id/epoch, confidence, TTL. elev/obstruction optional.
   Fail-closed: CRC/short-RS fail, stale TTL, unknown version => erase.
   Never act on corrupt units.
3. **LEO-IP profile.** Starlink IP/QUIC uses **light integrity** (CRC or short
   RS(255,239) I=1, not stacked). Full RS(255,223) ASCENT-D = spool / deep-space
   / high-BER only.
4. **Hybrid fuse** (`docs/ORBITSTACK-LEOAWARE-BRIDGE.md`). PATHHINT may seed
   freeze + next_capacity. Orb pathID still owns REPROBE when not suppressed.
   Assist suppress ~2s / no hybrid util-MD (no double-cut). Predictive pre-hop
   freeze = **growth freeze only**; never gate `ep:loss_burst`.
5. **Sacred-meter.** Observational only when a real dish/API exists. Wire Lab
   meters labeled **sim**. No fake Starlink telemetry API.
6. **ASCENT ship success metrics** (not LeoAware dual-gate, not "+X Mbps
   Starlink"): goldens Py≡JS; PATHHINT round-trip; erase-on-fail green;
   overhead bytes/hint (30/34); apply vs reject rates.
7. **Ship order.** (a) SPEC appendix + goldens + ascent-wire 2.1.0 ->
   (b) Wire Lab panel -> (c) publish PATHHINT codec -> (d) LeoAware later.
   Do not claim OrbitStack paid wins.

## Versions

| Surface | Version |
|---------|---------|
| Nexus / architecture card | **2.1.0** |
| ascent-wire (PyPI + npm, in-repo) | **2.1.0** |
| SPEC | **1.0.0-rc1** + append-only SkyPulse appendix |
| Cont packing | Unchanged (`0xA0-0xBF`, 5-bit) |

## Added

- PATHHINT / SKYSTATE unit (`0xC5` schema `0x01`) in Python + JS
- `ref/ascent_skypulse.py` LEO-IP vs D integrity helper + `evaluate_pathhint`
- Goldens: `tests/skypulse_vectors.json`, `tests/test_skypulse.py`, JS lock
- Starlink client: PATHHINT on ADUs, QUEUE on obstruction/RTT flap, sim/obs meter
- Docs: `docs/SKYPULSE.md`, `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`
- Wire Lab SkyPulse panel (site files only; deploy is gated; meters labeled sim)

## Publish checklist (later)

1. Jon approves this PR and tags `v2.1.0`
2. PyPI Trusted Publisher workflow on release
3. `npm publish` from `packages/ascent-js` if desired
4. Cloudflare Pages deploy of `site/public`
