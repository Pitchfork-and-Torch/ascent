# ascent-wire 2.1.0 (SkyPulse) - release notes draft

**Do not publish to PyPI/npm from this PR unless Jon asks.** Version bumps and
goldens are in-tree. Live site `ascent.jonbailey.xyz` needs Jon's Cloudflare
Pages approval.

## Honesty fence

ASCENT is a wire encoding + agent/control grammar. This release does **not**
increase Starlink physical downlink/uplink Mbps. SkyPulse improves usable
application goodput and session continuity under LEO (PATHHINT foresight,
fail-closed skip, LEO-efficient framing). No "Grok offline in space forever".

## Versions

| Surface | Version |
|---------|---------|
| Nexus / architecture card | **2.1.0** |
| ascent-wire (PyPI + npm, in-repo) | **2.1.0** |
| SPEC | **1.0.0-rc1** + append-only SkyPulse appendix |
| Cont packing | Unchanged (`0xA0-0xBF`, 5-bit) |

## Added

- PATHHINT / SKYSTATE unit (`0xC5` schema `0x01`) in Python + JS
- `ref/ascent_skypulse.py` LEO-IP vs D integrity helper
- Goldens: `tests/skypulse_vectors.json`, `tests/test_skypulse.py`, JS lock
- Starlink client: PATHHINT on ADUs, QUEUE on obstruction/RTT flap
- Docs: `docs/SKYPULSE.md`, `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`
- Wire Lab SkyPulse panel (site files only; deploy is gated)

## Publish checklist (later)

1. Jon approves this PR and tags `v2.1.0`
2. PyPI Trusted Publisher workflow on release
3. `npm publish` from `packages/ascent-js` if desired
4. Cloudflare Pages deploy of `site/public`
