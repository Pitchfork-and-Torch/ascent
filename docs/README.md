# ASCENT docs assets

| File | Use |
|------|-----|
| [ascent-infographic.png](ascent-infographic.png) | Full architecture card v2.1.0 (README + site; regen PNG on deploy) |
| [ascent-infographic.jpg](ascent-infographic.jpg) | JPEG twin |
| [ascent-infographic-banner.jpg](ascent-infographic-banner.jpg) | Wide header / social crop |
| [series/](series/) | 8-panel integration explainer series |
| [SKYPULSE.md](SKYPULSE.md) | PATHHINT / SKYSTATE: what, why, non-claims |
| [GROK-ASCENT-STARLINK-ARCHITECTURE.md](GROK-ASCENT-STARLINK-ARCHITECTURE.md) | Grok + ASCENT + Starlink dual-mode plan |
| [ORBITSTACK-LEOAWARE-BRIDGE.md](ORBITSTACK-LEOAWARE-BRIDGE.md) | LeoAware PATHHINT consume rules |
| [RELEASE-2.1.0.md](RELEASE-2.1.0.md) | In-repo release notes draft (no publish) |
| [AGENT-LOOP.md](AGENT-LOOP.md) | LLM agent loop guide |
| [SPEC-FREEZE-1.0-RC.md](SPEC-FREEZE-1.0-RC.md) | 1.0-RC freeze checklist |
| [ENCODING-GUARD.md](ENCODING-GUARD.md) | LONG overlong / non-minimal reject (SPEC C.4.1) |

**Current card:** ASCENT Nexus Wire Lab 2.0 · architecture **v2.1.0** (SkyPulse)

## Integration series (Desktop + docs)

Regenerate:

```bash
python site/scripts/make_infographic_series.py
```

Writes PNG/JPG to `Desktop/ASCENT-infographics/` and `docs/series/`.

| Panel | Topic |
|-------|--------|
| 01 | What is ASCENT |
| 02 | Integration stack |
| 03 | Wire Lab 2.0 |
| 04 | Agent loop |
| 05 | ASCENT-D erase-on-fail |
| 06 | Package + golden lock |
| 07 | Hello, Universe anatomy |
| 08 | End-to-end map |

## Architecture card + OG

```bash
python site/scripts/make_infographic.py
python site/scripts/make_og.py
```

Outputs also land in `site/public/` (`infographic.png`, `infographic.jpg`, `og.jpg`) and `assets/masters/`.
