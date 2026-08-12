"""Starlink dish health probe (optional, non-authoritative).

Default: stub so the client runs without a dish. This module does **not**
invent a Starlink telemetry API.

Observational (`obs` sacred-meter): opt-in TCP reachability to the dish LAN
port (`STARLINK_PROBE=1`, typically 192.168.100.1:9200). Open/closed only.

Lab (`sim` sacred-meter): `ASCENT_DISH_STATE` / `ASCENT_OBSTRUCTION` overrides.
Never treat TCP :9200 as PHY rate, obstruction fraction, or SNR.
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
    """Return dish health. Lab overrides via env; no RF, no fake telemetry API.

    Env:
      STARLINK_PROBE=1          TCP reachability to 192.168.100.1:9200
      ASCENT_OBSTRUCTION=0.0-1  lab obstruction fraction (sim)
      ASCENT_ELEV_DEG           lab elevation (sim)
      ASCENT_DISH_STATE         ONLINE|OBSTRUCTED|OFFLINE|UNKNOWN (sim)
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
