#!/usr/bin/env python3
"""ASCENT SkyPulse helpers: PATHHINT policy, LEO-IP integrity, session QUEUE.

Honesty: this module does not increase Starlink physical RF Mbps. It frames
path foresight (PATHHINT) so apps/CCA waste fewer retransmits and freeze
growth across LEO reconfig / obstruction windows.

ASCII hyphens only. No network I/O. No RF.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ascent_codec import (
    FLAG_CAP_KBPS,
    FLAG_CRC,
    FLAG_HAS_ELEV,
    FLAG_HAS_OBSTRUCTION,
    FLAG_RELATIVE_FREEZE,
    canonical_pathhint_bytes,
    decode_skystate,
    encode_pathhint,
)

# Usage profile labels (not a parse-law fork). Grammar stays ASCENT-E / D.
PROFILE_E_LEO = "ASCENT-E-LEO"
PROFILE_D = "ASCENT-D"
PROFILE_E = "ASCENT-E"

# Lab defaults: obstruction fraction that should QUEUE interactive turns.
OBSTRUCTION_QUEUE = 0.15
# Typical Starlink land RTT is ~25-60 ms; 200 ms+ is a flap / rain window.
RTT_QUEUE_MS = 200.0
RTT_JUMP_MS = 80.0


@dataclass
class PathHint:
    """Decoded or to-encode PATHHINT fields (application goodput hint)."""

    path_id: int = 0
    next_capacity_bps: int = 0
    freeze_ms: int = 0
    confidence: float = 0.0
    ttl_ms: int = 0
    obstruction: Optional[float] = None
    elev_deg: Optional[float] = None
    crc: bool = False
    applied: bool = True
    reason: str = ""
    flags: int = 0

    def encode(self) -> bytes:
        if self.flags & FLAG_CAP_KBPS:
            kbps = (self.next_capacity_bps + 999) // 1000
            return encode_pathhint(
                path_id=self.path_id,
                next_capacity_kbps=kbps,
                freeze_ms=self.freeze_ms,
                confidence=self.confidence,
                ttl_ms=self.ttl_ms,
                obstruction=self.obstruction,
                elev_deg=self.elev_deg,
                crc=self.crc,
            )
        return encode_pathhint(
            path_id=self.path_id,
            next_capacity_bps=self.next_capacity_bps,
            freeze_ms=self.freeze_ms,
            confidence=self.confidence,
            ttl_ms=self.ttl_ms,
            obstruction=self.obstruction,
            elev_deg=self.elev_deg,
            crc=self.crc,
        )

    @classmethod
    def from_event(cls, ev: dict) -> "PathHint":
        return cls(
            path_id=int(ev.get("path_id") or 0),
            next_capacity_bps=int(ev.get("next_capacity_bps") or 0),
            freeze_ms=int(ev.get("freeze_ms") or 0),
            confidence=float(ev.get("confidence") or 0.0),
            ttl_ms=int(ev.get("ttl_ms") or 0),
            obstruction=ev.get("obstruction"),
            elev_deg=ev.get("elev_deg"),
            crc=bool(ev.get("crc")),
            applied=bool(ev.get("applied")),
            reason=str(ev.get("reason") or ""),
            flags=int(ev.get("flags") or 0),
        )


def recommend_integrity(profile: str) -> dict[str, Any]:
    """Choose integrity for a path. Never recommend double FEC (CRC+RS) as required.

    ASCENT-E-LEO / Starlink IP: light CRC or none (TLS already on the path).
    ASCENT-D / spool / deep-space: P9 RS(255,223) erase-on-fail.
    """
    p = (profile or "").strip().upper().replace("_", "-")
    if p in (
        "ASCENT-D",
        "D",
        "DEEP",
        "DEEP-SPACE",
        "SPOOL",
        "ARCHIVE-D",
    ):
        return {
            "profile": PROFILE_D,
            "mode": "p9",
            "double_fec": False,
            "use_pathhint_crc": False,
            "wrap_p9": True,
            "note": (
                "ASCENT-D: outer RS(255,223) erase-on-fail. Skip extra PATHHINT CRC "
                "(P9 already CRCs the unit). Use for spool/deep-space, not interactive Starlink IP."
            ),
        }
    if p in (
        "ASCENT-E-LEO",
        "E-LEO",
        "LEO",
        "LEO-IP",
        "STARLINK",
        "SKY",
        "SKYPULSE",
    ):
        return {
            "profile": PROFILE_E_LEO,
            "mode": "crc",
            "double_fec": False,
            "use_pathhint_crc": True,
            "wrap_p9": False,
            "note": (
                "ASCENT-E-LEO: Starlink/LEO IP already has PHY+TLS. Prefer light PATHHINT CRC "
                "or none. Do not wrap interactive turns in P9 RS (double-FEC tax, extra latency). "
                "PATHHINT is a goodput/CCA hint, not an RF Mbps upgrade."
            ),
        }
    return {
        "profile": PROFILE_E,
        "mode": "none",
        "double_fec": False,
        "use_pathhint_crc": False,
        "wrap_p9": False,
        "note": "ASCENT-E default: plain PATHHINT unit; optional CRC. P9 only if integrity requested.",
    }


def wrap_pathhint_p9(unit: bytes) -> Optional[bytes]:
    """Optional P9 wrap when integrity is requested (spool / D). None if unavailable."""
    if not unit:
        return None
    try:
        from ascent_d import encode_p9  # type: ignore

        return encode_p9(unit)
    except Exception:
        return None


def should_queue_session(
    *,
    obstruction: Optional[float] = None,
    dish_state: str = "",
    rtt_ms: Optional[float] = None,
    rtt_prev_ms: Optional[float] = None,
    obstruction_threshold: float = OBSTRUCTION_QUEUE,
    rtt_threshold_ms: float = RTT_QUEUE_MS,
    rtt_jump_ms: float = RTT_JUMP_MS,
) -> bool:
    """True when interactive CLOUD should yield to QUEUE (obstruction / RTT flap).

    Does not change EDGE honesty: callers still report which brain answered.
    """
    state = (dish_state or "").strip().upper()
    if state == "OBSTRUCTED":
        return True
    if obstruction is not None and obstruction >= obstruction_threshold:
        return True
    if rtt_ms is not None and rtt_ms >= rtt_threshold_ms:
        return True
    if (
        rtt_ms is not None
        and rtt_prev_ms is not None
        and abs(rtt_ms - rtt_prev_ms) >= rtt_jump_ms
    ):
        return True
    return False


def pathhint_from_env_and_dish(
    *,
    path_id: int = 1,
    obstruction: Optional[float] = None,
    elev_deg: Optional[float] = None,
    next_capacity_bps: int = 50_000_000,
    freeze_ms: int = 15_000,
    confidence: float = 0.5,
    ttl_ms: int = 30_000,
    crc: bool = True,
) -> PathHint:
    """Build a PATHHINT for the Starlink client sacred-meter / ADU prefix."""
    return PathHint(
        path_id=path_id,
        next_capacity_bps=next_capacity_bps,
        freeze_ms=freeze_ms,
        confidence=confidence,
        ttl_ms=ttl_ms,
        obstruction=obstruction,
        elev_deg=elev_deg,
        crc=crc,
        applied=True,
    )


def format_pathhint_meter(hint: PathHint, *, applied: Optional[bool] = None) -> str:
    """ASCII sacred-meter fragment. Never claims RF Mbps."""
    ok = hint.applied if applied is None else applied
    if not ok:
        return f"pathhint=skip reason={hint.reason or 'fail-closed'}"
    cap_mbps = hint.next_capacity_bps / 1_000_000.0
    obst = "na" if hint.obstruction is None else f"{hint.obstruction:.2f}"
    el = "na" if hint.elev_deg is None else f"{hint.elev_deg:.1f}deg"
    return (
        f"pathhint cap_hint={cap_mbps:.1f}Mbps freeze={hint.freeze_ms}ms "
        f"conf={hint.confidence:.2f} obst={obst} el={el}"
    )


__all__ = [
    "PROFILE_E_LEO",
    "PROFILE_D",
    "PROFILE_E",
    "OBSTRUCTION_QUEUE",
    "RTT_QUEUE_MS",
    "PathHint",
    "recommend_integrity",
    "wrap_pathhint_p9",
    "should_queue_session",
    "pathhint_from_env_and_dish",
    "format_pathhint_meter",
    "encode_pathhint",
    "decode_skystate",
    "canonical_pathhint_bytes",
    "FLAG_CAP_KBPS",
    "FLAG_CRC",
    "FLAG_HAS_ELEV",
    "FLAG_HAS_OBSTRUCTION",
    "FLAG_RELATIVE_FREEZE",
]
