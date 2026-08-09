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
    state: str  # ONLINE | OFFLINE | OBSTRUCTED | UNKNOWN
    detail: str = ""


def probe(timeout: float = 0.25) -> DishHealth:
    # Opt-in: avoid hanging labs when no dish is present
    if os.environ.get("STARLINK_PROBE", "").strip() not in ("1", "true", "yes"):
        return DishHealth(state="SKIP", detail="set STARLINK_PROBE=1 to scan dish")
    host = os.environ.get("STARLINK_DISH_HOST", "192.168.100.1")
    port = int(os.environ.get("STARLINK_DISH_PORT", "9200"))
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return DishHealth(state="ONLINE", detail=f"{host}:{port} open")
    except OSError as e:
        return DishHealth(state="UNKNOWN", detail=str(e)[:80])
