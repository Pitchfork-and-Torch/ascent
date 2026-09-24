# ascent_starlink_client (Phase 1 + SkyPulse)

Dual-mode Grok session framed as ASCENT over ordinary IP (fiber or Starlink),
with **SkyPulse PATHHINT** for LEO session continuity.

## Honest scope

- **Does:** encode turns as ASCENT; emit PATHHINT (next_capacity / freeze / obstruction);
  call cloud API when reachable; fall back to local OpenAI-compatible edge model;
  **QUEUE** when obstruction or RTT flaps; flush queue when the path is stable;
  optional ASCENT-D P9 wrap for spool/deep-space; dish TCP probe opt-in.
- **Does not:** raise Starlink physical RF Mbps; reverse-engineer Dishy RF;
  run frontier Grok offline; replace Starlink networking; claim dual-gate LeoAware product wins.

See `docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md`, `docs/SKYPULSE.md`,
and `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`.

Default integrity profile is **ASCENT-E-LEO**: light PATHHINT CRC (or short RS
as a documented substitute, not stacked), no full P9 RS on interactive IP
(avoid double-FEC tax). Use `--ascent-d` / `--profile ASCENT-D` only for spool
or deep-space.

## Run

```bash
cd /path/to/ascent
PYTHONPATH=".:ref:examples/ascent_starlink_client"
# optional cloud:
# export XAI_API_KEY="..."
# optional edge:
# export EDGE_BASE_URL="http://127.0.0.1:11434/v1"
# optional dish LAN probe:
# export STARLINK_PROBE=1
# lab obstruction / QUEUE drill:
# export ASCENT_OBSTRUCTION=0.40
# export ASCENT_DISH_STATE=OBSTRUCTED

python examples/ascent_starlink_client/daemon.py --status
python examples/ascent_starlink_client/daemon.py --pathhint
python examples/ascent_starlink_client/daemon.py --once "ping"
python examples/ascent_starlink_client/daemon.py --once "ping" --ascent-d
python examples/ascent_starlink_client/daemon.py --flush
```

Interactive: run without `--once`. Type `/status`, `/flush`, or `/pathhint`.

## Env

| Variable | Role |
|----------|------|
| `XAI_API_KEY` / `OPENAI_API_KEY` | Cloud Grok |
| `XAI_BASE_URL` | default `https://api.x.ai/v1` |
| `XAI_MODEL` | default `grok-3` |
| `EDGE_BASE_URL` | default `http://127.0.0.1:11434/v1` |
| `EDGE_MODEL` | default `llama3.1:8b` |
| `ASCENT_CLOUD_TIMEOUT` | seconds (default 45) |
| `ASCENT_EDGE_TIMEOUT` | seconds (default 8) |
| `STARLINK_PROBE=1` | TCP probe dish `:9200` |
| `ASCENT_OBSTRUCTION` | 0..1 lab obstruction fraction |
| `ASCENT_ELEV_DEG` | lab elevation |
| `ASCENT_DISH_STATE` | ONLINE / OBSTRUCTED / ... lab override |
| `ASCENT_PATH_CAP_BPS` | PATHHINT next_capacity seed (predicted sender bottleneck, not RF) |
| `ASCENT_FREEZE_MS` | PATHHINT growth-freeze window |
| `ASCENT_INTEGRITY_PROFILE` | `ASCENT-E-LEO` (default) or `ASCENT-D` |

## Modes

| Mode | Meaning |
|------|---------|
| CLOUD | `api.x.ai` answered **and** path is stable |
| EDGE | Local model answered (banner printed) |
| QUEUE | Obstruction / RTT flap, or no brain: spool ADUs under `./spool/` |
| DEAD | No brain available |

Sacred-meter includes a PATHHINT fragment (`bottleneck_hint=...Mbps freeze_until=...`).
That number is **predicted sender bottleneck**, not a Starlink RF measurement.
Meter lines are prefixed **sim** unless `STARLINK_PROBE=1` observed a real dish
TCP port (`obs`). Lab env overrides are always sim. This client does not invent
a Starlink telemetry API.

ASCII-only status lines. No em/en dashes.
