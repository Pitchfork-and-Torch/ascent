# ascent_starlink_client (Phase 1)

Dual-mode Grok session framed as ASCENT over ordinary IP (fiber or Starlink).

## Honest scope

- **Does:** encode turns as ASCENT; call cloud API when reachable; fall back to local OpenAI-compatible edge model; spool when offline; flush queue when cloud returns; optional ASCENT-D P9 wrap; dish TCP probe opt-in.
- **Does not:** reverse-engineer Dishy RF; run frontier Grok offline; replace Starlink networking.

See `docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md`.

## Run

```powershell
cd $env:USERPROFILE\Projects\next-ascii
$env:PYTHONPATH = ".;ref;examples\ascent_starlink_client"
# optional cloud:
# $env:XAI_API_KEY = "..."
# optional edge:
# $env:EDGE_BASE_URL = "http://127.0.0.1:11434/v1"
# $env:EDGE_MODEL = "llama3.1:8b"
# optional dish LAN probe:
# $env:STARLINK_PROBE = "1"

py -3 examples\ascent_starlink_client\daemon.py --status
py -3 examples\ascent_starlink_client\daemon.py --once "ping"
py -3 examples\ascent_starlink_client\daemon.py --once "ping" --ascent-d
py -3 examples\ascent_starlink_client\daemon.py --flush
```

Interactive: run without `--once`. Type `/status` or `/flush` at the prompt.

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

## Modes

| Mode | Meaning |
|------|---------|
| CLOUD | `api.x.ai` answered |
| EDGE | Local model answered (banner printed) |
| QUEUE | Outbound ADUs under `./spool/` until flush |
| DEAD | No brain available |

ASCII-only status lines. No em/en dashes.
