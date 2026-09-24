#!/usr/bin/env python3
# Delay Hull contact lab. Injected clock. Not a Bundle Protocol Agent.
# Not an ASCENT convergence layer. No network. No RF.
# ASCII hyphens only.

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ascent_codec import AscentCodecError, decode_stream, encode_turn
from ascent_d import decode_p9, encode_p9


def sample_adu(
    *,
    session: int = 0xA5CE47,
    turn: int = 1,
    corr: int = 0x1001,
    lifetime_s: int = 3600,
    role: int = 1,
    tool: str = "ping",
    text: bytes = b"ping\n",
) -> bytes:
    """One request document: TURN head + P0 text + one TOOL frame."""
    from ascent_codec import encode_agent_frame

    head = encode_turn(
        session=session,
        turn=turn,
        corr=corr,
        lifetime_s=lifetime_s,
        role=role,
        crc=True,
    )
    return head + text + encode_agent_frame(0x0003, name=tool)


class ContactLab:
    """Hold ADUs until a contact window is open and the lifetime is live.

    Windows are [open, close) on the injected clock, in seconds.
    Lifetime is seconds after enqueue. Duplicate session+turn+corr is a no-op.
    ascent_d=True stores a P9 wrap. A parity fail erases and emits no TOOL.
    """

    def __init__(
        self,
        windows: Sequence[Tuple[int, int]],
        now: int = 0,
    ) -> None:
        self.windows = [(int(a), int(b)) for a, b in windows]
        self.now = int(now)
        self.spool: List[dict] = []
        self.seen = set()

    def in_window(self, now: Optional[int] = None) -> bool:
        t = self.now if now is None else int(now)
        return any(a <= t < b for a, b in self.windows)

    def enqueue(self, adu: bytes, *, ascent_d: bool = False) -> dict:
        try:
            events = decode_stream(adu)
        except AscentCodecError as ex:
            return {"status": "rejected", "reason": str(ex), "tools": []}
        turn = next(
            (e for e in events if e.get("kind") == "turn" and e.get("applied")),
            None,
        )
        if turn is None:
            return {"status": "rejected", "reason": "no_turn", "tools": []}
        stored = encode_p9(adu) if ascent_d else adu
        item = {
            "id": len(self.spool),
            "enqueued_at": self.now,
            "lifetime_s": int(turn["lifetime_s"]),
            "session": int(turn["session"]),
            "turn": int(turn["turn"]),
            "corr": int(turn["corr"]),
            "role": int(turn["role"]),
            "ascent_d": bool(ascent_d),
            "stored": stored,
            "clear": adu,
            "state": "held",
        }
        self.spool.append(item)
        return {"status": "held", "id": item["id"], "tools": []}

    def smash_stored(self, item_id: int, count: int = 17) -> None:
        """Punch more symbol errors than RS(255,223) can correct.

        One symbol error is recovered by the outer code. Erase happens when
        decode fails. This is not a single-bit CRC.
        """
        item = self.spool[item_id]
        raw = bytearray(item["stored"])
        if not raw:
            return
        start = max(0, len(raw) - count)
        for n in range(start, len(raw)):
            raw[n] ^= 0xFF
        item["stored"] = bytes(raw)

    def advance(self, to_s: int) -> List[dict]:
        self.now = int(to_s)
        if not self.in_window():
            return []
        results: List[dict] = []
        for item in self.spool:
            if item["state"] != "held":
                continue
            if self.now > item["enqueued_at"] + item["lifetime_s"]:
                item["state"] = "dropped"
                results.append(
                    {
                        "status": "dropped",
                        "reason": "lifetime",
                        "id": item["id"],
                        "tools": [],
                    }
                )
                continue
            key = (item["session"], item["turn"], item["corr"])
            if key in self.seen:
                item["state"] = "duplicate"
                results.append(
                    {"status": "duplicate", "id": item["id"], "tools": []}
                )
                continue
            clear, erased = self._unwrap(item)
            if erased or clear is None:
                item["state"] = "erased"
                results.append(
                    {"status": "erased", "id": item["id"], "tools": []}
                )
                continue
            try:
                events = decode_stream(clear)
            except AscentCodecError:
                item["state"] = "erased"
                results.append(
                    {"status": "erased", "id": item["id"], "tools": []}
                )
                continue
            tools = [
                e.get("name", "")
                for e in events
                if e.get("kind") == "agent"
                and e.get("opcode_name") == "TOOL"
                and not e.get("skipped")
            ]
            self.seen.add(key)
            item["state"] = "delivered"
            results.append(
                {
                    "status": "delivered",
                    "id": item["id"],
                    "tools": tools,
                    "events": events,
                }
            )
        return results

    def _unwrap(self, item: dict) -> Tuple[Optional[bytes], bool]:
        if not item["ascent_d"]:
            return item["clear"], False
        frame, _nxt, status = decode_p9(item["stored"])
        if status != "ok" or frame is None:
            return None, True
        return frame.unit, False


def tool_names(result: Dict[str, Any]) -> List[str]:
    return list(result.get("tools") or [])
