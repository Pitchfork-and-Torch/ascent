"""Starlink dish health probe (optional, non-authoritative).

Default: stub that reports UNKNOWN so the client runs without RE tools.
Wire real probes via community starlink-grpc-tools against 192.168.100.1:9200
for diagnostics only. Never treat dish gRPC as a security boundary.
"""
from __future__ import annotations

import os
import socket
from dataclasses import dataclass


@dataclass
class DishHealth:
    state: str  # ONLINE | OFFLINE | OBSTRUCTED | UNKNOWN | SKIP
    detail: str = ""
    obstruction: float | None = None
    elev_deg: float | None = None
    snr_db: float | None = None


def probe(timeout: float = 0.25) -> DishHealth:
    """Return dish health. Lab overrides via env; no RF, diagnostics only.

    Env:
      STARLINK_PROBE=1          TCP probe 192.168.100.1:9200
      ASCENT_OBSTRUCTION=0.0-1  lab obstruction fraction
      ASCENT_ELEV_DEG           lab elevation
      ASCENT_DISH_STATE         ONLINE|OBSTRUCTED|OFFLINE|UNKNOWN
    """
    obst = _env_float("ASCENT_OBSTRUCTION")
    elev = _env_float("ASCENT_ELEV_DEG")
    forced = os.environ.get("ASCENT_DISH_STATE", "").strip().upper()
    if forced in ("ONLINE", "OFFLINE", "OBSTRUCTED", "UNKNOWN", "SKIP"):
        if forced == "OBSTRUCTED" and obst is None:
            obst = 0.40
        return DishHealth(
            state=forced,
            detail="ASCENT_DISH_STATE override (lab)",
            obstruction=obst,
            elev_deg=elev,
        )
    if obst is not None and obst >= 0.15:
        return DishHealth(
            state="OBSTRUCTED",
            detail="ASCENT_OBSTRUCTION lab override",
            obstruction=obst,
            elev_deg=elev,
        )
    # Opt-in: avoid hanging labs when no dish is present
    if os.environ.get("STARLINK_PROBE", "").strip() not in ("1", "true", "yes"):
        return DishHealth(
            state="SKIP",
            detail="set STARLINK_PROBE=1 to scan dish",
            obstruction=obst,
            elev_deg=elev,
        )
    host = os.environ.get("STARLINK_DISH_HOST", "192.168.100.1")
    port = int(os.environ.get("STARLINK_DISH_PORT", "9200"))
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return DishHealth(
                state="ONLINE",
                detail=f"{host}:{port} open",
                obstruction=obst if obst is not None else 0.0,
                elev_deg=elev,
            )
    except OSError as e:
        return DishHealth(
            state="UNKNOWN",
            detail=str(e)[:80],
            obstruction=obst,
            elev_deg=elev,
        )


def _env_float(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
