#!/usr/bin/env python3
"""ASCENT dual-mode client (Phase 1 + SkyPulse).

Modes: CLOUD | EDGE | QUEUE | DEAD
ASCII status only. Stock IP path (fiber or Starlink). No RF hacks.

SkyPulse PATHHINT is a goodput/CCA hint. It does not raise Starlink RF Mbps.
QUEUE on obstruction / RTT flap. CLOUD/EDGE name the brain honestly.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from pathlib import Path

from brains import answer, probe_cloud
from codec_session import (
    TurnADU,
    build_pathhint,
    flush_queue,
    list_pending,
    spool_write,
    try_ascent_d_wrap,
)
from dish_health import probe as dish_probe

_ROOT = Path(__file__).resolve().parents[2]
_REF = _ROOT / "ref"
if str(_REF) not in sys.path:
    sys.path.insert(0, str(_REF))

try:
    from ascent_skypulse import (  # type: ignore
        PathHint,
        format_pathhint_meter,
        recommend_integrity,
        should_queue_session,
    )
except Exception:
    PathHint = None  # type: ignore
    format_pathhint_meter = None  # type: ignore
    recommend_integrity = None  # type: ignore
    should_queue_session = None  # type: ignore

ROOT = Path(__file__).resolve().parent
SPOOL = ROOT / "spool"
ARCHIVE = SPOOL / "archive"
_LAST_RTT_MS: float | None = None


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float | None = None) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def make_pathhint(dish):
    obst = dish.obstruction
    elev = dish.elev_deg
    cap = _env_int("ASCENT_PATH_CAP_BPS", 50_000_000)
    freeze = _env_int("ASCENT_FREEZE_MS", 15_000)
    conf = _env_float("ASCENT_PATH_CONFIDENCE", 0.5) or 0.5
    if obst is not None:
        conf = max(0.15, min(1.0, 1.0 - obst))
    ttl = _env_int("ASCENT_PATH_TTL_MS", 30_000)
    profile = os.environ.get("ASCENT_INTEGRITY_PROFILE", "ASCENT-E-LEO")
    blob = build_pathhint(
        path_id=_env_int("ASCENT_PATH_ID", 1),
        next_capacity_bps=cap,
        freeze_ms=freeze,
        confidence=conf,
        ttl_ms=ttl,
        obstruction=obst,
        elev_deg=elev,
        profile=profile,
    )
    hint = None
    if PathHint is not None:
        hint = PathHint(
            path_id=_env_int("ASCENT_PATH_ID", 1),
            next_capacity_bps=cap,
            freeze_ms=freeze,
            confidence=conf,
            ttl_ms=ttl,
            obstruction=obst,
            elev_deg=elev,
            applied=blob is not None,
        )
    return blob, hint


def sacred_meter(
    mode: str,
    dish: str,
    queue_n: int,
    detail: str = "",
    rtt_ms: float | None = None,
    hint=None,
) -> str:
    if mode == "CLOUD":
        api = "ok"
    elif mode == "EDGE":
        api = "DOWN"
    elif mode == "DEAD":
        api = "DOWN"
    elif mode == "QUEUE":
        api = "ok" if "brain=CLOUD" in detail else ("DOWN" if "brain=EDGE" in detail else "HOLD")
    else:
        api = "ok" if probe_cloud() else "DOWN"
    rtt = f" rtt={rtt_ms:.0f}ms" if rtt_ms is not None else ""
    extra = f" {detail}" if detail else ""
    ph = ""
    if hint is not None and format_pathhint_meter is not None:
        ph = " " + format_pathhint_meter(hint)
    return (
        f"[ASCENT] mode={mode} p0=1.00 api={api} dish={dish} "
        f"queue={queue_n}{rtt}{extra}{ph}"
    ).strip()


def run_once(text: str, session: str, use_d: bool, profile: str) -> int:
    global _LAST_RTT_MS
    dish = dish_probe()
    queue_n = len(list_pending(SPOOL))
    hint_blob, hint = make_pathhint(dish)

    result = answer(text)
    brain = result.mode  # CLOUD | EDGE | DEAD  (honesty: which brain answered)
    rtt = result.rtt_ms
    queue_path = False
    if should_queue_session is not None:
        queue_path = should_queue_session(
            obstruction=dish.obstruction,
            dish_state=dish.state,
            rtt_ms=rtt,
            rtt_prev_ms=_LAST_RTT_MS,
        )
    _LAST_RTT_MS = rtt

    # Session mode: QUEUE when obstruction/RTT flap. Brain name stays honest in detail.
    if queue_path and brain in ("CLOUD", "EDGE"):
        mode = "QUEUE"
        detail = f"brain={brain} path=flap {result.detail}".strip()
    else:
        mode = brain
        detail = result.detail

    print(sacred_meter(mode, dish.state, queue_n, detail, rtt, hint))
    if brain == "EDGE":
        print("[ASCENT] EDGE MODE - local model, not frontier Grok")
    if mode == "QUEUE":
        print(
            "[ASCENT] QUEUE - obstruction or RTT flap; ADU spooled. "
            "Not an RF speedup. PATHHINT freeze is for CCA/apps."
        )

    pol = recommend_integrity(profile) if recommend_integrity else {"wrap_p9": False}
    if use_d and not pol.get("wrap_p9"):
        print(
            "[ASCENT] note: --ascent-d on Starlink IP adds RS tax; "
            "ASCENT-E-LEO prefers light PATHHINT CRC. Wrapping anyway because flag set."
        )

    turn = int(time.time()) % 1_000_000
    adu = TurnADU(
        session=session,
        turn=turn,
        mode=mode,
        user_text=text,
        assistant_text=result.text,
        rtt_ms=result.rtt_ms,
        pathhint=hint_blob,
    )
    blob = adu.to_bytes()
    if use_d or pol.get("wrap_p9"):
        wrapped = try_ascent_d_wrap(blob)
        if wrapped is not None:
            blob = wrapped
            print(f"[ASCENT] P9 ASCENT-D wrap ({len(blob)} B)")
        else:
            print("[ASCENT] P9 wrap skipped (unit too large or ascent_d missing)")

    if mode == "DEAD" or mode == "QUEUE" or not result.ok:
        path = spool_write(SPOOL, blob, f"{session}-{turn}.adu")
        print(f"[ASCENT] QUEUE spooled {path.name} ({len(blob)} B)")
        print(result.text)
        return 2 if mode != "QUEUE" else 0

    print("--- assistant ---")
    print(result.text)
    spool_write(ARCHIVE, blob, f"{session}-{turn}.adu")

    if mode == "CLOUD":
        n = flush_queue(SPOOL, ARCHIVE)
        if n:
            print(f"[ASCENT] flushed {n} queued ADU(s) to archive (cloud path up)")
    return 0


def cmd_status(profile: str) -> int:
    dish = dish_probe()
    q = list_pending(SPOOL)
    cloud = probe_cloud()
    _, hint = make_pathhint(dish)
    pol = recommend_integrity(profile) if recommend_integrity else {}
    print(
        sacred_meter(
            "IDLE",
            dish.state,
            len(q),
            f"probe_cloud={'ok' if cloud else 'DOWN'} pending={[p.name for p in q[:5]]}",
            hint=hint,
        )
    )
    print(f"[ASCENT] spool={SPOOL}")
    print(
        f"[ASCENT] dish_probe={dish.state} {dish.detail} "
        f"obst={dish.obstruction} el={dish.elev_deg}"
    )
    if pol:
        print(
            f"[ASCENT] integrity profile={pol.get('profile')} mode={pol.get('mode')} "
            f"wrap_p9={pol.get('wrap_p9')} (not an RF Mbps claim)"
        )
    return 0


def cmd_flush() -> int:
    n = flush_queue(SPOOL, ARCHIVE)
    print(f"[ASCENT] flushed {n} ADU(s)")
    return 0 if n >= 0 else 1


def cmd_pathhint(profile: str) -> int:
    dish = dish_probe()
    blob, hint = make_pathhint(dish)
    if blob is None:
        print("[ASCENT] PATHHINT encode unavailable")
        return 1
    print(blob.hex().upper())
    if hint is not None and format_pathhint_meter is not None:
        print("[ASCENT]", format_pathhint_meter(hint))
    pol = recommend_integrity(profile) if recommend_integrity else {}
    if pol:
        print("[ASCENT]", pol.get("note"))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ASCENT dual-mode client (CLOUD / EDGE / QUEUE) + SkyPulse PATHHINT"
    )
    ap.add_argument("--once", metavar="TEXT", help="Single-shot prompt")
    ap.add_argument("--session", default="sat-" + uuid.uuid4().hex[:8])
    ap.add_argument(
        "--ascent-d",
        action="store_true",
        help="Force P9 ASCENT-D wrap (spool/deep-space; avoid on interactive Starlink IP)",
    )
    ap.add_argument(
        "--profile",
        default=os.environ.get("ASCENT_INTEGRITY_PROFILE", "ASCENT-E-LEO"),
        help="Integrity profile: ASCENT-E-LEO (default) or ASCENT-D",
    )
    ap.add_argument("--status", action="store_true", help="Print sacred-meter and exit")
    ap.add_argument("--flush", action="store_true", help="Flush pending queue to archive")
    ap.add_argument("--pathhint", action="store_true", help="Encode a SkyPulse PATHHINT and exit")
    args = ap.parse_args()

    if args.status:
        return cmd_status(args.profile)
    if args.flush:
        return cmd_flush()
    if args.pathhint:
        return cmd_pathhint(args.profile)
    if args.once:
        return run_once(args.once, args.session, args.ascent_d, args.profile)

    print(sacred_meter("IDLE", dish_probe().state, len(list_pending(SPOOL))))
    print("Commands: empty line quits. /status /flush /pathhint")
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
            cmd_status(args.profile)
            continue
        if line in ("/flush", "flush"):
            cmd_flush()
            continue
        if line in ("/pathhint", "pathhint"):
            cmd_pathhint(args.profile)
            continue
        run_once(line, session, args.ascent_d, args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
