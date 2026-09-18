# ASCENT-D satellite lab results

**UTC sample run:** 2026-07-30 (local lab)

## Legal rails

- Public Celestrak TLE only (ISS ZARYA)
- Simulated downlink BER tiers
- **No RF transmit / no satellite command**

## Satellite scenario (live TLE)

| Field | Value (example run) |
|-------|---------------------|
| Name | ISS (ZARYA) |
| Inclination | ~51.63 deg |
| Period | ~92.9 min |
| Approx altitude | ~426 km |
| Mean motion | ~15.49 rev/day |

## ASCENT-D results

| Path | Result |
|------|--------|
| Clean P9 encode/decode | PASS |
| Hello Universe inside P9 | PASS (text+agent+multimodal) |
| LEO clear BER 1e-5 | 40/40 recovered |
| LEO degraded BER 5e-3 | partial recovery + erasures |
| LEO blackout BER 5e-2 | 0/40 recovered, 40/40 erased |
| Hard corruption | erased (no mojibake) |

## Run

```bash
set PYTHONPATH=ref
py -3 tests/test_ascent_d_satellite.py
```
