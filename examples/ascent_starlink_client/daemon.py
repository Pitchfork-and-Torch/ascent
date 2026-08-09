#!/usr/bin/env python3
"""ASCENT dual-mode client (Phase 1).

Modes: CLOUD | EDGE | QUEUE | DEAD
ASCII status only. Stock IP path (fiber or Starlink). No RF hacks.
"""
from __future__ import annotations

import argparse
import time
import uuid
from pathlib import Path

from brains import answer, probe_cloud
from codec_session import TurnADU, flush_queue, list_pending, spool_write, try_ascent_d_wrap
from dish_health import probe as dish_probe

ROOT = Path(__file__).resolve().parent
SPOOL = ROOT / "spool"
ARCHIVE = SPOOL / "archive"


def sacred_meter(
    mode: str,
    dish: str,
    queue_n: int,
    detail: str = "",
    rtt_ms: float | None = None,
) -> str:
    if mode == "CLOUD":
        api = "ok"
    elif mode == "EDGE":
        api = "DOWN"
    elif mode in ("DEAD", "QUEUE"):
        api = "DOWN"
    else:
        api = "ok" if probe_cloud() else "DOWN"
    rtt = f" rtt={rtt_ms:.0f}ms" if rtt_ms is not None else ""
    extra = f" {detail}" if detail else ""
    return (
        f"[ASCENT] mode={mode} p0=1.00 api={api} dish={dish} "
        f"queue={queue_n}{rtt}{extra}"
    ).strip()


def run_once(text: str, session: str, use_d: bool) -> int:
    dish = dish_probe()
    queue_n = len(list_pending(SPOOL))

    result = answer(text)
    mode = result.mode
    print(sacred_meter(mode, dish.state, queue_n, result.detail, result.rtt_ms))
    if mode == "EDGE":
        print("[ASCENT] EDGE MODE - local model, not frontier Grok")

    turn = int(time.time()) % 1_000_000
    adu = TurnADU(
        session=session,
        turn=turn,
        mode=mode,
        user_text=text,
        assistant_text=result.text,
        rtt_ms=result.rtt_ms,
    )
    blob = adu.to_bytes()
    if use_d:
        wrapped = try_ascent_d_wrap(blob)
        if wrapped is not None:
            blob = wrapped
            print(f"[ASCENT] P9 ASCENT-D wrap ({len(blob)} B)")
        else:
            print("[ASCENT] P9 wrap skipped (unit too large or ascent_d missing)")

    if mode == "DEAD" or not result.ok:
        path = spool_write(SPOOL, blob, f"{session}-{turn}.adu")
        print(f"[ASCENT] QUEUE spooled {path.name} ({len(blob)} B)")
        print(result.text)
        return 2

    print("--- assistant ---")
    print(result.text)
    spool_write(ARCHIVE, blob, f"{session}-{turn}.adu")

    # Catch-up: when cloud works again, flush any offline queue
    if mode == "CLOUD":
        n = flush_queue(SPOOL, ARCHIVE)
        if n:
            print(f"[ASCENT] flushed {n} queued ADU(s) to archive (cloud path up)")
    return 0


def cmd_status() -> int:
    dish = dish_probe()
    q = list_pending(SPOOL)
    cloud = probe_cloud()
    mode = "CLOUD" if cloud else ("EDGE?" if True else "DEAD")
    print(
        sacred_meter(
            "IDLE",
            dish.state,
            len(q),
            f"probe_cloud={'ok' if cloud else 'DOWN'} pending={[p.name for p in q[:5]]}",
        )
    )
    print(f"[ASCENT] spool={SPOOL}")
    print(f"[ASCENT] dish_probe={dish.state} {dish.detail}")
    return 0


def cmd_flush() -> int:
    n = flush_queue(SPOOL, ARCHIVE)
    print(f"[ASCENT] flushed {n} ADU(s)")
    return 0 if n >= 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ASCENT dual-mode client (CLOUD / EDGE / QUEUE)"
    )
    ap.add_argument("--once", metavar="TEXT", help="Single-shot prompt")
    ap.add_argument("--session", default="sat-" + uuid.uuid4().hex[:8])
    ap.add_argument("--ascent-d", action="store_true", help="Try P9 ASCENT-D wrap")
    ap.add_argument("--status", action="store_true", help="Print sacred-meter and exit")
    ap.add_argument("--flush", action="store_true", help="Flush pending queue to archive")
    args = ap.parse_args()

    if args.status:
        return cmd_status()
    if args.flush:
        return cmd_flush()
    if args.once:
        return run_once(args.once, args.session, args.ascent_d)

    print(sacred_meter("IDLE", dish_probe().state, len(list_pending(SPOOL))))
    print("Commands: empty line quits. Prefix with /status for meter.")
    session = args.session
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            return 0
        if line in ("/status", "status"):
            cmd_status()
            continue
        if line in ("/flush", "flush"):
            cmd_flush()
            continue
        run_once(line, session, args.ascent_d)


if __name__ == "__main__":
    raise SystemExit(main())
