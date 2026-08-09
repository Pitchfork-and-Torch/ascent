"""Build greppable ASCENT turn ADUs for dual-mode sat sessions."""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Prefer installed package; fall back to repo ref/
_ROOT = Path(__file__).resolve().parents[2]
_REF = _ROOT / "ref"
if str(_REF) not in sys.path:
    sys.path.insert(0, str(_REF))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from ascent import encode_text  # type: ignore
except Exception:
    try:
        from ascent_codec import encode_text  # type: ignore
    except Exception:
        encode_text = None  # type: ignore

ROLE_GUIDE = bytes.fromhex("9AC10100020000060567756964659B")


@dataclass
class TurnADU:
    session: str
    turn: int
    mode: str
    user_text: str
    assistant_text: str = ""
    rtt_ms: Optional[float] = None

    def header_ascii(self) -> str:
        rtt = f" rtt_ms={self.rtt_ms:.0f}" if self.rtt_ms is not None else ""
        return (
            f"ASCENT/1.0\n"
            f"session={self.session} turn={self.turn} mode={self.mode}{rtt}\n"
            f"ts={int(time.time())}\n"
        )

    def to_bytes(self) -> bytes:
        """Header + optional codec body + ROLE fence + assistant prose."""
        parts: list[bytes] = [self.header_ascii().encode("ascii")]

        if encode_text is not None:
            try:
                # ASCENT-7/V body with optional ROLE via package
                body = encode_text(self.user_text, header=False, role="guide")
                parts.append(body)
            except Exception:
                parts.append(self.user_text.encode("utf-8"))
                parts.append(b"\n")
                parts.append(ROLE_GUIDE)
        else:
            parts.append(self.user_text.encode("utf-8"))
            parts.append(b"\n")
            parts.append(ROLE_GUIDE)

        if self.assistant_text:
            parts.append(b"\n")
            # Prefer pure ASCII for greppability when possible
            try:
                parts.append(self.assistant_text.encode("ascii"))
            except UnicodeEncodeError:
                parts.append(self.assistant_text.encode("utf-8"))
            parts.append(b"\n")
        return b"".join(parts)


def try_ascent_d_wrap(unit: bytes, max_unit: int = 8192) -> Optional[bytes]:
    """Optional P9 wrap if ascent_d available and unit fits."""
    if len(unit) > max_unit:
        # Chunk note: Phase 1 keeps whole turn under MAX_UNIT or skips wrap
        return None
    try:
        from ascent_d import encode_p9  # type: ignore

        return encode_p9(unit)
    except Exception:
        return None


def spool_write(spool_dir: Path, adu: bytes, name: str) -> Path:
    spool_dir.mkdir(parents=True, exist_ok=True)
    path = spool_dir / name
    path.write_bytes(adu)
    return path


def list_pending(spool_dir: Path) -> list[Path]:
    if not spool_dir.exists():
        return []
    return sorted(p for p in spool_dir.glob("*.adu") if p.is_file())


def flush_queue(spool_dir: Path, archive_dir: Path) -> int:
    """Move pending ADUs to archive after successful cloud path (store-and-forward catch-up)."""
    pending = list_pending(spool_dir)
    if not pending:
        return 0
    archive_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in pending:
        dest = archive_dir / f"flushed-{p.name}"
        dest.write_bytes(p.read_bytes())
        p.unlink(missing_ok=True)
        n += 1
    return n
