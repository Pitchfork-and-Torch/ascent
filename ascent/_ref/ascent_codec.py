#!/usr/bin/env python3
# ASCENT 1.0 lab reference - shared encode/decode codec (Earth profile subset)
# ASCENT-7 (P0 ASCII identity), frozen Cont + ASCENT-V short forms, bridge INLINE.
# ASCII hyphens only. No network I/O. No personal PII.

from __future__ import annotations

import hashlib
import struct
import zlib
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPCODE = {
    0x0001: "STOP",
    0x0002: "ROLE",
    0x0003: "TOOL",
    0x0004: "THINK",
    0x0005: "HANDOFF",
    0x0006: "CAP",
    0x0007: "SAFETY",
}
OPCODE_BY_NAME = {name: code for code, name in OPCODE.items()}
FLAG_CRITICAL = 0x80
AGENT_VER_V1 = 0x01
AGENT_MAX_ARGS = 8192
AGENT_NAME_MAX = 64
# SPEC C.3.1 ROLE/TOOL/HANDOFF: A-Z a-z 0-9 _ - . and 1..64 bytes
_AGENT_NAME_EXTRA = frozenset(b"_.-")

MM_KIND = {1: "REF", 2: "INLINE", 3: "CHUNK", 4: "END"}
HASH_ALG = {0: "none", 1: "sha-256", 2: "sha-512", 3: "blake3-256"}
HASH_LEN = {0: 0, 1: 32, 2: 64, 3: 32}

HEADER_MAGIC = b"ASCENT/1.0\n"
PLANE_P3 = 0x03

# SkyPulse / PATHHINT (additive P2 lead from reserved 0xC4-0xCE). Cont freeze untouched.
LEAD_VERSION_BUMP = 0xC2
LEAD_REGISTRY_DELTA = 0xC3
LEAD_SKYSTATE = 0xC5
LEAD_TURN = 0xC6
LEAD_PRIVATE_OP = 0xCF
PATHHINT_SCHEMA_V1 = 0x01
TURN_SCHEMA_V1 = 0x01
TURN_BODY_LEN = 27
TURN_BODY_LEN_CRC = 31
TURN_MAX_BODY = 256
TURN_FLAG_CRC = 0x01
TURN_FLAG_RESERVED_MASK = 0xFE
TURN_ROLE_REQUEST = 1
TURN_ROLE_RESPONSE = 2
TURN_ROLE_ACK_ERASE = 3
MM_FLAG_EXTERNAL = 0x01
MM_FLAG_FINAL_HASH = 0x02
MM_FLAG_STREAM_ID = 0x04
PATHHINT_BODY_LEN = 26
PATHHINT_BODY_LEN_CRC = 30
PATHHINT_MAX_BODY = 256
P2_SKIP_CAP = 16384
FLAG_CAP_KBPS = 0x01
FLAG_HAS_OBSTRUCTION = 0x02
FLAG_HAS_ELEV = 0x04
FLAG_RELATIVE_FREEZE = 0x08
FLAG_CRC = 0x10
FLAG_RESERVED_MASK = 0xE0
ELEV_ABSENT = 0x7FFF
OBSTRUCTION_ABSENT = 0xFF

# First scalar that requires LONG (F5 03 + u24be). 4-byte residual
# v = cp - 0x4280 fits while v < (5 << 15); max 4-byte cp is U+2C27F.
ASCENT_V_LONG_MIN = 0x2C280

# Hex from SPEC.md E.2 (source of truth for interop tests)
HELLO_UNIVERSE_HEX = (
    "415343454E542F312E300A48656C6C6F"
    "2C20556E6976657273652E0A9AC10100"
    "020000060567756964659B9D4D010005"
    "0101E491921182DA9CB7B24E4B8A579D"
    "5E78EDC23E40141D015FAA097C3ECC6D"
    "65EB000000000000002A6369643A7368"
    "613235363A6161626263636464656566"
    "66303031313232333334343535363637"
    "37383839"
)

# Alias used by older call sites
SPEC_HELLO_HEX = HELLO_UNIVERSE_HEX


class AscentCodecError(Exception):
    """Encode/decode hard fault."""


# ---------------------------------------------------------------------------
# Cont class (FROZEN) - primary continuation 0xA0-0xBF, 5 payload bits
# ---------------------------------------------------------------------------


class Cont:
    """FROZEN primary continuation bytes: 0xA0-0xBF (32 values, 5 payload bits)."""

    MIN = 0xA0
    MAX = 0xBF
    MASK = 0x1F

    @staticmethod
    def cont_byte(n5: int) -> int:
        return 0xA0 | (n5 & 0x1F)

    @staticmethod
    def cont_val(b: int) -> int:
        if not (0xA0 <= b <= 0xBF):
            raise AscentCodecError(f"not a Cont byte: {b:#04x}")
        return b & 0x1F

    @staticmethod
    def is_cont(b: int) -> bool:
        return 0xA0 <= b <= 0xBF


def cont_byte(n5: int) -> int:
    return Cont.cont_byte(n5)


def cont_val(b: int) -> int:
    return Cont.cont_val(b)


# ---------------------------------------------------------------------------
# ASCENT-7
# ---------------------------------------------------------------------------


def encode_text_ascent7(text: str) -> bytes:
    """Encode pure ASCII as P0. Reject any codepoint > 0x7F."""
    for ch in text:
        cp = ord(ch)
        if cp > 0x7F:
            raise AscentCodecError(
                f"ASCENT-7 rejects non-ASCII U+{cp:04X}"
            )
    return text.encode("ascii")


# ---------------------------------------------------------------------------
# ASCENT-V scalar packing (FROZEN lab map)
# ---------------------------------------------------------------------------


def _reject_surrogate(cp: int) -> None:
    if 0xD800 <= cp <= 0xDFFF:
        raise AscentCodecError(
            f"UTF-16 surrogates are illegal on ASCENT wire: U+{cp:04X}"
        )
    if cp < 0 or cp > 0x10FFFF:
        raise AscentCodecError(f"codepoint out of range: {cp:#x}")


def long_form_required(cp: int) -> bool:
    """True iff shortest ASCENT-V form for cp is LONG (F5 03 + u24be)."""
    if cp < 0x80 or cp > 0x10FFFF:
        return False
    if 0xD800 <= cp <= 0xDFFF:
        return False
    if cp <= 0x427F:
        return False
    return (cp - 0x4280) >= (5 << 15)


def _reject_long_scalar(cp: int) -> None:
    """SPEC C.4.1: LONG payload MUST be a scalar that cannot use a shorter form."""
    if 0xD800 <= cp <= 0xDFFF:
        raise AscentCodecError(f"surrogate on wire U+{cp:04X}")
    if cp > 0x10FFFF:
        raise AscentCodecError(f"scalar out of range U+{cp:04X}")
    if cp < 0x80:
        raise AscentCodecError(f"overlong ASCII via LONG form U+{cp:04X}")
    if not long_form_required(cp):
        raise AscentCodecError(f"non-minimal LONG form for U+{cp:04X}")


def encode_scalar(cp: int) -> List[int]:
    """
    Encode one Unicode scalar to ASCENT wire bytes (list of ints 0..255).
    P0 for cp < 0x80; ASCENT-V short forms or F5 03 long form for higher.
    """
    _reject_surrogate(cp)
    if cp < 0x80:
        return [cp]

    # 2-byte: U+0080..U+027F
    if cp <= 0x027F:
        v = cp - 0x80
        b0 = 0xD0 | ((v >> 5) & 0x0F)
        b1 = cont_byte(v & 0x1F)
        return [b0, b1]

    # 3-byte: U+0280..U+427F
    if cp <= 0x427F:
        v = cp - 0x280
        b0 = 0xE0 | ((v >> 10) & 0x0F)
        b1 = cont_byte((v >> 5) & 0x1F)
        b2 = cont_byte(v & 0x1F)
        return [b0, b1, b2]

    # 4-byte: U+4280.. when v fits in 18 bits with top field 0..4 (F0-F4)
    # Max v = (5 << 15) - 1 => max cp = 0x4280 + 0x27FFF = 0x2C27F
    v = cp - 0x4280
    if 0 <= v < (5 << 15):
        top = v >> 15  # 0..4
        b0 = 0xF0 | top
        b1 = cont_byte((v >> 10) & 0x1F)
        b2 = cont_byte((v >> 5) & 0x1F)
        b3 = cont_byte(v & 0x1F)
        return [b0, b1, b2, b3]

    # LONG form: F5 03 + cp as u24be (P3 default plane)
    if cp > 0xFFFFFF:
        raise AscentCodecError(f"scalar exceeds u24: U+{cp:04X}")
    return [
        0xF5,
        PLANE_P3,
        (cp >> 16) & 0xFF,
        (cp >> 8) & 0xFF,
        cp & 0xFF,
    ]


def decode_ascent_v_at(
    data: Union[bytes, bytearray, Sequence[int]], i: int
) -> Optional[Tuple[int, int]]:
    """
    If data[i] is an ASCENT-V lead, return (cp, end_i).
    Return None if not a V lead (caller handles control frames / hard fault).
    Raises AscentCodecError on truncated or malformed V unit.
    """
    n = len(data)
    if i >= n:
        return None
    b0 = data[i]

    # 2-byte D0-DF + Cont
    if 0xD0 <= b0 <= 0xDF:
        if i + 1 >= n:
            raise AscentCodecError(f"truncated ASCENT-V 2-byte at {i}")
        c1 = data[i + 1]
        if not Cont.is_cont(c1):
            raise AscentCodecError(f"bad ASCENT-V 2-byte cont at {i}")
        v = ((b0 & 0x0F) << 5) | cont_val(c1)
        return 0x80 + v, i + 2

    # 3-byte E0-EF + 2 Cont
    if 0xE0 <= b0 <= 0xEF:
        if i + 2 >= n:
            raise AscentCodecError(f"truncated ASCENT-V 3-byte at {i}")
        c1, c2 = data[i + 1], data[i + 2]
        if not (Cont.is_cont(c1) and Cont.is_cont(c2)):
            raise AscentCodecError(f"bad ASCENT-V 3-byte cont at {i}")
        v = ((b0 & 0x0F) << 10) | (cont_val(c1) << 5) | cont_val(c2)
        return 0x280 + v, i + 3

    # 4-byte F0-F4 + 3 Cont
    if 0xF0 <= b0 <= 0xF4:
        if i + 3 >= n:
            raise AscentCodecError(f"truncated ASCENT-V 4-byte at {i}")
        c1, c2, c3 = data[i + 1], data[i + 2], data[i + 3]
        if not (Cont.is_cont(c1) and Cont.is_cont(c2) and Cont.is_cont(c3)):
            raise AscentCodecError(f"bad ASCENT-V 4-byte cont at {i}")
        v = (
            ((b0 & 0x07) << 15)
            | (cont_val(c1) << 10)
            | (cont_val(c2) << 5)
            | cont_val(c3)
        )
        cp = 0x4280 + v
        # 4-byte residual range includes U+D800..DFFF; parse law forbids them.
        _reject_surrogate(cp)
        return cp, i + 4

    # LONG form F5 03 + u24be(cp)
    if b0 == 0xF5:
        if i + 1 >= n:
            raise AscentCodecError(f"truncated F5 plane at {i}")
        plane = data[i + 1]
        if plane != PLANE_P3:
            # Not the lab long-scalar form; not a V lead for text merge
            return None
        if i + 4 >= n:
            raise AscentCodecError(f"truncated F5 03 u24 at {i}")
        cp = (data[i + 2] << 16) | (data[i + 3] << 8) | data[i + 4]
        _reject_long_scalar(cp)
        return cp, i + 5

    return None


# ---------------------------------------------------------------------------
# Encode text (header / role / non-ascii modes)
# ---------------------------------------------------------------------------


def validate_agent_name(name: str) -> bytes:
    """ROLE/TOOL/HANDOFF name: 1..64 bytes, charset A-Z a-z 0-9 _ - ."""
    if not isinstance(name, str) or not name:
        raise AscentCodecError("agent name must be 1..64 charset bytes")
    try:
        raw = name.encode("ascii")
    except UnicodeEncodeError as ex:
        raise AscentCodecError("agent name must be ASCII") from ex
    if not (1 <= len(raw) <= AGENT_NAME_MAX):
        raise AscentCodecError("agent name too long (max 64)")
    for b in raw:
        ok = (
            0x41 <= b <= 0x5A
            or 0x61 <= b <= 0x7A
            or 0x30 <= b <= 0x39
            or b in _AGENT_NAME_EXTRA
        )
        if not ok:
            raise AscentCodecError("agent name charset")
    return raw


def escape_agent_args(raw: bytes) -> bytes:
    """Args escape: C1 1B <byte> for 0x9A, 0x9B, and 0xC1 (injective)."""
    out = bytearray()
    for b in raw:
        if b in (0x9A, 0x9B, 0xC1):
            out.append(0xC1)
            out.append(0x1B)
            out.append(b)
        else:
            out.append(b)
    return bytes(out)


def encode_agent_frame(
    opcode: Optional[int] = None,
    *,
    opcode_name: Optional[str] = None,
    ver: int = AGENT_VER_V1,
    flags: int = 0,
    args: Optional[bytes] = None,
    name: Optional[str] = None,
    payload: Optional[Union[str, bytes]] = None,
) -> bytes:
    """Encode a P5 frame: 9A C1 ver opcode:u16be flags len:u16be args 9B."""
    if opcode is None:
        if not opcode_name:
            raise AscentCodecError("agent opcode required")
        key = str(opcode_name).upper()
        if key not in OPCODE_BY_NAME:
            raise AscentCodecError(f"unknown agent opcode name {opcode_name!r}")
        opcode = OPCODE_BY_NAME[key]
    if opcode < 0 or opcode > 0xFFFF:
        raise AscentCodecError("agent opcode out of u16")
    if ver < 0 or ver > 0xFF:
        raise AscentCodecError("agent ver out of u8")
    if flags < 0 or flags > 0xFF:
        raise AscentCodecError("agent flags out of u8")

    if args is not None:
        raw_args = bytes(args)
    elif name is not None and opcode in (0x0002, 0x0003, 0x0005):
        nb = validate_agent_name(name)
        raw_args = bytes([len(nb)]) + nb
    elif payload is not None:
        if isinstance(payload, str):
            raw_args = payload.encode("utf-8")
        else:
            raw_args = bytes(payload)
    else:
        raw_args = b""

    wire_args = escape_agent_args(raw_args)
    if len(wire_args) > AGENT_MAX_ARGS:
        raise AscentCodecError("agent args exceed max 8192")

    out = bytearray()
    out.append(0x9A)
    out.append(0xC1)
    out.append(ver & 0xFF)
    out += struct.pack(">H", opcode)
    out.append(flags & 0xFF)
    out += struct.pack(">H", len(wire_args))
    out += wire_args
    out.append(0x9B)
    return bytes(out)


def _encode_role_frame(role: str) -> bytes:
    return encode_agent_frame(0x0002, name=role)


def encode_mm_unit(
    kind: int,
    body: bytes,
    *,
    codec: int = 0x0005,
    flags: int = 0,
    hash_alg: int = 0,
    digest: bytes = b"",
) -> bytes:
    """MM frame: 9D 4D kind codec:u16be flags hash-alg hash len:u64be body."""
    if hash_alg == 0:
        digest = b""
    elif hash_alg in (1, 3):
        if len(digest) != 32:
            raise AscentCodecError("sha-256/blake3 digest must be 32 bytes")
    elif hash_alg == 2:
        if len(digest) != 64:
            raise AscentCodecError("sha-512 digest must be 64 bytes")
    else:
        raise AscentCodecError(f"unknown hash-alg {hash_alg}")
    out = bytearray()
    out.append(0x9D)
    out.append(0x4D)
    out.append(kind & 0xFF)
    out += struct.pack(">H", codec)
    out.append(flags & 0xFF)
    out.append(hash_alg & 0xFF)
    out += digest
    out += struct.pack(">Q", len(body))
    out += body
    return bytes(out)


def _encode_mm_inline_utf8(body: bytes, codec: int = 0x0001) -> bytes:
    """MM INLINE: 9D 4D kind=2 codec flags=0 hash-alg=0 len=u64be body."""
    return encode_mm_unit(2, body, codec=codec, flags=0, hash_alg=0)


def encode_mm_chunk(
    payload: bytes,
    chunk_index: int,
    stream_id: Optional[int] = None,
    *,
    codec: int = 0x0005,
) -> bytes:
    """CHUNK body: optional stream_id:u64be, then chunk_index:u32be, then payload."""
    if chunk_index < 0 or chunk_index > 0xFFFFFFFF:
        raise AscentCodecError("chunk_index out of u32")
    flags = 0
    body = bytearray()
    if stream_id is not None:
        if stream_id < 0 or stream_id > 0xFFFFFFFFFFFFFFFF:
            raise AscentCodecError("stream_id out of u64")
        flags |= MM_FLAG_STREAM_ID
        body += struct.pack(">Q", stream_id)
    body += struct.pack(">I", chunk_index)
    body += payload
    return encode_mm_unit(3, bytes(body), codec=codec, flags=flags, hash_alg=0)


def encode_mm_end(
    stream_id: Optional[int] = None,
    *,
    codec: int = 0x0005,
    digest: bytes = b"",
    hash_alg: int = 0,
    final_hash: bool = False,
) -> bytes:
    """END closes a CHUNK stream. Hash is over logical media, not framing."""
    flags = MM_FLAG_FINAL_HASH if final_hash else 0
    body = b""
    if stream_id is not None:
        if stream_id < 0 or stream_id > 0xFFFFFFFFFFFFFFFF:
            raise AscentCodecError("stream_id out of u64")
        flags |= MM_FLAG_STREAM_ID
        body = struct.pack(">Q", stream_id)
    if final_hash and hash_alg == 0 and len(digest) == 32:
        hash_alg = 1
    return encode_mm_unit(
        4, body, codec=codec, flags=flags, hash_alg=hash_alg, digest=digest
    )


def encode_text(
    text: str,
    header: bool = False,
    role: Optional[str] = None,
    non_ascii: str = "v",
) -> bytes:
    """
    Encode plain text to ASCENT wire bytes.

    header: prefix b"ASCENT/1.0\\n"
    role: optional ASCII ROLE agent frame after body
    non_ascii:
      "reject" - raise on cp > 0x7F
      "v" - encode_scalar for each non-ascii
      "bridge" - non-ascii runs as MM INLINE text/plain UTF-8; ASCII stays P0
    """
    if non_ascii not in ("v", "bridge", "reject"):
        raise AscentCodecError(f"unknown non_ascii mode: {non_ascii!r}")

    out = bytearray()
    if header:
        out += HEADER_MAGIC

    if non_ascii == "reject":
        out += encode_text_ascent7(text)
    elif non_ascii == "v":
        for ch in text:
            cp = ord(ch)
            out += bytes(encode_scalar(cp))
    else:
        # bridge: ASCII runs P0; non-ascii runs -> MM INLINE utf-8
        i = 0
        chars = list(text)
        while i < len(chars):
            cp = ord(chars[i])
            _reject_surrogate(cp)
            if cp < 0x80:
                out.append(cp)
                i += 1
                continue
            # gather non-ascii run
            run = []
            while i < len(chars):
                c2 = ord(chars[i])
                _reject_surrogate(c2)
                if c2 < 0x80:
                    break
                run.append(chars[i])
                i += 1
            body = "".join(run).encode("utf-8")
            out += _encode_mm_inline_utf8(body)

    if role is not None:
        out += _encode_role_frame(role)

    return bytes(out)


# ---------------------------------------------------------------------------
# Decode helpers (agent / mm / crypto / def)
# ---------------------------------------------------------------------------


def _u16be(b: bytes, i: int) -> Tuple[int, int]:
    if i + 2 > len(b):
        raise AscentCodecError("truncated u16")
    return struct.unpack_from(">H", b, i)[0], i + 2


def _u32be(b: bytes, i: int) -> Tuple[int, int]:
    if i + 4 > len(b):
        raise AscentCodecError("truncated u32")
    return struct.unpack_from(">I", b, i)[0], i + 4


def _u64be(b: bytes, i: int) -> Tuple[int, int]:
    if i + 8 > len(b):
        raise AscentCodecError("truncated u64")
    return struct.unpack_from(">Q", b, i)[0], i + 8


def unescape_agent_args(raw: bytes) -> bytes:
    """C1 1B <byte> => literal byte; used only inside agent args.

    Bare 0x9A/0x9B is nested-fence illegal. Truncated C1 1B is a hard fault
    (not a best-effort pair of literals).
    """
    out = bytearray()
    i = 0
    n = len(raw)
    while i < n:
        b = raw[i]
        if b == 0xC1:
            if i + 1 < n and raw[i + 1] == 0x1B:
                if i + 2 >= n:
                    raise AscentCodecError("truncated fence escape")
                out.append(raw[i + 2])
                i += 3
                continue
            out.append(0xC1)
            i += 1
            continue
        if b in (0x9A, 0x9B):
            raise AscentCodecError("bare fence byte inside agent args")
        out.append(b)
        i += 1
    return bytes(out)


def parse_role_or_name(args: bytes) -> dict:
    if not args:
        raise AscentCodecError("agent name missing")
    n = args[0]
    if n < 1:
        raise AscentCodecError("agent name must be 1..64 charset bytes")
    if 1 + n > len(args):
        raise AscentCodecError("name_len exceeds args")
    name = args[1 : 1 + n]
    rest = args[1 + n :]
    try:
        name_s = name.decode("ascii")
    except UnicodeDecodeError as ex:
        raise AscentCodecError("agent name must be ASCII") from ex
    validate_agent_name(name_s)
    return {
        "name": name_s,
        "name_bytes": name.hex(),
        "rest_hex": rest.hex(),
    }


def decode_agent(body: bytes, start: int) -> Tuple[dict, int]:
    i = start + 1
    if i >= len(body) or body[i] != 0xC1:
        raise AscentCodecError("AGENT_OPEN without C1 AGENT_OP")
    i += 1
    if i + 1 + 2 + 1 + 2 > len(body):
        raise AscentCodecError("truncated agent header")
    ver = body[i]
    i += 1
    opcode, i = _u16be(body, i)
    flags = body[i]
    i += 1
    alen, i = _u16be(body, i)
    if alen > AGENT_MAX_ARGS:
        raise AscentCodecError("agent args exceed max 8192")
    if i + alen > len(body):
        raise AscentCodecError("truncated agent args")
    args_wire = body[i : i + alen]
    i += alen
    if i >= len(body) or body[i] != 0x9B:
        raise AscentCodecError("AGENT missing CLOSE 0x9B")
    i += 1

    ev: Dict[str, Any] = {
        "kind": "agent",
        "ver": ver,
        "opcode": opcode,
        "opcode_name": OPCODE.get(opcode, f"UNKNOWN_{opcode:#06x}"),
        "flags": flags,
        "args_wire_len": alen,
        "args_hex": args_wire.hex(),
        "skipped": False,
        "reason": "",
        "offset": start,
        "end": i,
    }

    # Unknown ver: skip-by-length if len was readable; never execute.
    if ver != AGENT_VER_V1:
        ev["skipped"] = True
        ev["reason"] = "unknown_ver"
        return ev, i

    args = unescape_agent_args(args_wire)
    ev["args_hex"] = args.hex()

    known = opcode in OPCODE
    if not known:
        if flags & FLAG_CRITICAL:
            raise AscentCodecError(
                f"unknown CRITICAL opcode {opcode:#06x}"
            )
        ev["skipped"] = True
        ev["reason"] = "unknown_opcode"
        return ev, i

    if opcode in (0x0002, 0x0003, 0x0005):
        ev.update(parse_role_or_name(args))
    return ev, i


def decode_mm(body: bytes, start: int) -> Tuple[dict, int]:
    """Decode multimodal frame. Event kind stays 'multimodal'; wire kind -> mm_kind."""
    i = start + 1
    if i >= len(body) or body[i] != 0x4D:
        raise AscentCodecError("MM_MARK without 0x4D 'M'")
    i += 1
    if i >= len(body):
        raise AscentCodecError("truncated MM kind")
    wire_kind = body[i]
    i += 1
    codec, i = _u16be(body, i)
    if i >= len(body):
        raise AscentCodecError("truncated MM flags")
    flags = body[i]
    i += 1
    if i >= len(body):
        raise AscentCodecError("truncated MM hash-alg")
    hash_alg = body[i]
    i += 1
    hlen = HASH_LEN.get(hash_alg)
    if hlen is None:
        raise AscentCodecError(f"unknown hash-alg {hash_alg}")
    if i + hlen > len(body):
        raise AscentCodecError("truncated MM hash")
    digest = body[i : i + hlen]
    i += hlen
    mlen, i = _u64be(body, i)
    if mlen > 256 * 1024 * 1024:
        raise AscentCodecError("MM body over hard cap")
    if i + mlen > len(body):
        raise AscentCodecError("truncated MM body")
    payload = body[i : i + mlen]
    i += mlen
    # Never put wire kind in field "kind" - that is the event type string.
    ev: Dict[str, Any] = {
        "kind": "multimodal",
        "mm_kind": wire_kind,
        "kind_name": MM_KIND.get(wire_kind, f"UNKNOWN_{wire_kind}"),
        "codec": codec,
        "flags": flags,
        "hash_alg": HASH_ALG.get(hash_alg, str(hash_alg)),
        "hash_hex": digest.hex(),
        "len": mlen,
        "offset": start,
        "end": i,
    }
    if wire_kind == 1:  # REF
        try:
            ev["ref"] = payload.decode("utf-8")
        except UnicodeDecodeError:
            ev["ref_hex"] = payload.hex()
    elif wire_kind == 2:  # INLINE
        if codec == 0x0001:
            try:
                ev["text"] = payload.decode("utf-8")
            except UnicodeDecodeError:
                ev["body_hex"] = payload.hex() if mlen <= 64 else payload[:32].hex() + "..."
        else:
            ev["body_hex"] = payload.hex() if mlen <= 64 else payload[:32].hex() + "..."
    else:
        ev["body_hex"] = payload.hex() if mlen <= 64 else payload[:32].hex() + "..."
    if wire_kind in (3, 4):
        _annotate_mm_chunk(ev, payload, flags, wire_kind)
    return ev, i


def _annotate_mm_chunk(ev: dict, payload: bytes, flags: int, wire_kind: int) -> None:
    """Parse CHUNK/END body. Malformed marks the event; reassembly discards it."""
    rest = payload
    if flags & MM_FLAG_STREAM_ID:
        if len(rest) < 8:
            ev["malformed"] = True
            ev["reason"] = "truncated_stream_id"
            return
        ev["stream_id"] = struct.unpack_from(">Q", rest, 0)[0]
        rest = rest[8:]
    if wire_kind == 3:
        if len(rest) < 4:
            ev["malformed"] = True
            ev["reason"] = "truncated_chunk_index"
            return
        ev["chunk_index"] = struct.unpack_from(">I", rest, 0)[0]
        ev["payload_hex"] = rest[4:].hex()
    else:
        ev["end_body_hex"] = rest.hex()
        ev["final_hash"] = bool(flags & MM_FLAG_FINAL_HASH)


def reassemble_chunks(events: Sequence[dict]) -> List[dict]:
    """SPEC C.3.2. Missing END discards. Duplicate index is malformed.

    Gaps may sit open until END. A gap still open at END is incomplete.
    Without stream_id only one CHUNK stream is legal in the consumer context.
    Hash (FINAL_HASH + sha-256) is checked only after a complete reassembly.
    """
    buffers: Dict[Any, dict] = {}
    order: List[Any] = []

    def slot(key: Any) -> dict:
        if key not in buffers:
            buffers[key] = {
                "chunks": {},
                "ended": False,
                "malformed": False,
                "reason": "",
                "hash_hex": "",
                "hash_alg": "",
                "final_hash": False,
            }
            order.append(key)
        return buffers[key]

    for ev in events:
        if ev.get("kind") != "multimodal":
            continue
        mk = ev.get("mm_kind")
        if mk not in (3, 4):
            continue
        has_sid = "stream_id" in ev
        key: Any = ev["stream_id"] if has_sid else None
        if not has_sid and None in buffers and buffers[None]["ended"] and mk == 3:
            s = slot(None)
            s["malformed"] = True
            s["reason"] = "second_bare_stream"
            continue
        s = slot(key)
        if ev.get("malformed"):
            s["malformed"] = True
            s["reason"] = ev.get("reason") or "malformed"
            s["chunks"].clear()
            continue
        if s["malformed"]:
            continue
        if mk == 3:
            idx = ev.get("chunk_index")
            if idx is None:
                s["malformed"] = True
                s["reason"] = "truncated_chunk_index"
                s["chunks"].clear()
                continue
            if idx in s["chunks"]:
                s["malformed"] = True
                s["reason"] = "duplicate_chunk_index"
                s["chunks"].clear()
                continue
            s["chunks"][idx] = bytes.fromhex(ev.get("payload_hex") or "")
        else:
            s["ended"] = True
            s["hash_hex"] = ev.get("hash_hex") or ""
            s["hash_alg"] = ev.get("hash_alg") or ""
            s["final_hash"] = bool(ev.get("final_hash") or (ev.get("flags", 0) & MM_FLAG_FINAL_HASH))

    out: List[dict] = []
    for key in order:
        s = buffers[key]
        base: Dict[str, Any] = {
            "stream_id": key,
            "status": "incomplete",
            "reason": s["reason"],
            "payload": b"",
            "payload_hex": "",
            "hash_valid": False,
            "emitted": False,
        }
        if s["malformed"]:
            base["status"] = "malformed"
            out.append(base)
            continue
        if not s["ended"]:
            base["reason"] = "missing_end"
            out.append(base)
            continue
        indexes = sorted(s["chunks"])
        if not indexes:
            base["reason"] = "empty"
            out.append(base)
            continue
        contiguous = list(range(indexes[0], indexes[0] + len(indexes)))
        if indexes != contiguous:
            base["reason"] = "gap_at_end"
            out.append(base)
            continue
        payload = b"".join(s["chunks"][i] for i in indexes)
        if s["final_hash"] and s["hash_alg"] == "sha-256":
            digest = hashlib.sha256(payload).hexdigest()
            if digest != s["hash_hex"]:
                base["status"] = "malformed"
                base["reason"] = "hash_mismatch"
                out.append(base)
                continue
            base["hash_valid"] = True
        elif s["final_hash"]:
            base["hash_valid"] = False
        else:
            base["hash_valid"] = True
        base["status"] = "complete"
        base["reason"] = ""
        base["payload"] = payload
        base["payload_hex"] = payload.hex()
        base["emitted"] = True
        out.append(base)
    return out


def decode_crypto(body: bytes, start: int) -> Tuple[dict, int]:
    i = start + 1
    if i >= len(body) or body[i] != 0x4B:
        raise AscentCodecError("CRYPTO_MARK without 0x4B 'K'")
    i += 1
    alg, i = _u16be(body, i)
    if i >= len(body):
        raise AscentCodecError("truncated crypto kid-len")
    kid_len = body[i]
    i += 1
    if i + kid_len > len(body):
        raise AscentCodecError("truncated kid")
    kid = body[i : i + kid_len]
    i += kid_len
    if i >= len(body):
        raise AscentCodecError("truncated nonce-len")
    nonce_len = body[i]
    i += 1
    if i + nonce_len > len(body):
        raise AscentCodecError("truncated nonce")
    nonce = body[i : i + nonce_len]
    i += nonce_len
    ct_len, i = _u32be(body, i)
    if i + ct_len > len(body):
        raise AscentCodecError("truncated ciphertext")
    ct = body[i : i + ct_len]
    i += ct_len
    return (
        {
            "kind": "crypto",
            "alg": alg,
            "kid_hex": kid.hex(),
            "nonce_hex": nonce.hex(),
            "ct_len": ct_len,
            "ct_sha256": hashlib.sha256(ct).hexdigest() if ct else "",
            "offset": start,
            "end": i,
        },
        i,
    )


def decode_def(body: bytes, start: int) -> Tuple[dict, int]:
    i = start + 1
    if i >= len(body):
        raise AscentCodecError("truncated DEF schema")
    schema = body[i]
    i += 1
    dlen, i = _u32be(body, i)
    if dlen > 16 * 1024 * 1024:
        raise AscentCodecError("DEF over hard cap")
    if i + dlen > len(body):
        raise AscentCodecError("truncated DEF body")
    dbody = body[i : i + dlen]
    i += dlen
    return (
        {
            "kind": "def",
            "schema": schema,
            "len": dlen,
            "body_sha256": hashlib.sha256(dbody).hexdigest(),
            "offset": start,
            "end": i,
        },
        i,
    )


def _p2_skip_event(
    *,
    lead: int,
    lead_name: str,
    start: int,
    end: int,
    body_len: int,
    extra: Optional[Dict[str, Any]] = None,
) -> dict:
    ev: Dict[str, Any] = {
        "kind": "skip",
        "lead": lead,
        "lead_name": lead_name,
        "skipped": True,
        "len": body_len,
        "offset": start,
        "end": end,
    }
    if extra:
        ev.update(extra)
    return ev


def decode_p2_u16_skip(
    body: bytes, start: int, lead_name: str
) -> Tuple[dict, int]:
    """VERSION_BUMP (C2): len:u16be body. Unknown unit => skip-by-length."""
    i = start + 1
    blen, i = _u16be(body, i)
    if blen > P2_SKIP_CAP:
        raise AscentCodecError(f"{lead_name} body over skip cap")
    if i + blen > len(body):
        raise AscentCodecError(f"truncated {lead_name} body")
    i += blen
    return (
        _p2_skip_event(
            lead=body[start],
            lead_name=lead_name,
            start=start,
            end=i,
            body_len=blen,
        ),
        i,
    )


def decode_p2_u32_skip(
    body: bytes, start: int, lead_name: str
) -> Tuple[dict, int]:
    """REGISTRY_DELTA (C3): len:u32be body. Unknown unit => skip-by-length."""
    i = start + 1
    blen, i = _u32be(body, i)
    if blen > P2_SKIP_CAP:
        raise AscentCodecError(f"{lead_name} body over skip cap")
    if i + blen > len(body):
        raise AscentCodecError(f"truncated {lead_name} body")
    i += blen
    return (
        _p2_skip_event(
            lead=body[start],
            lead_name=lead_name,
            start=start,
            end=i,
            body_len=blen,
        ),
        i,
    )


def decode_private_op_skip(body: bytes, start: int) -> Tuple[dict, int]:
    """PRIVATE_OP (CF): plane:u16be len:u32be body. Skip-by-length."""
    i = start + 1
    plane, i = _u16be(body, i)
    blen, i = _u32be(body, i)
    if blen > P2_SKIP_CAP:
        raise AscentCodecError("PRIVATE_OP body over skip cap")
    if i + blen > len(body):
        raise AscentCodecError("truncated PRIVATE_OP body")
    i += blen
    return (
        _p2_skip_event(
            lead=LEAD_PRIVATE_OP,
            lead_name="PRIVATE_OP",
            start=start,
            end=i,
            body_len=blen,
            extra={"plane": plane},
        ),
        i,
    )


def crc32_ieee(data: bytes) -> int:
    """IEEE CRC-32 (ISO-HDLC / zlib). Used for optional PATHHINT light integrity."""
    return zlib.crc32(data) & 0xFFFFFFFF


def encode_pathhint(
    *,
    path_id: int = 0,
    next_capacity_bps: Optional[int] = None,
    next_capacity_kbps: Optional[int] = None,
    freeze_ms: int = 0,
    freeze_until_ms: Optional[int] = None,
    confidence: float = 0.0,
    ttl_ms: int = 0,
    obstruction: Optional[float] = None,
    elev_deg: Optional[float] = None,
    crc: bool = False,
) -> bytes:
    """Encode a SkyPulse PATHHINT / SKYSTATE unit (P2 lead 0xC5, schema 0x01).

    next_capacity is predicted bottleneck bits/s as seen by the sender, never
    an RF PHY rate. Required v1 fields (always on the wire): path_id/epoch,
    freeze_until (relative freeze_ms), confidence, ttl_ms. elev/obstruction
    optional. v1 freeze is relative milliseconds (FLAG_RELATIVE_FREEZE). If
    freeze_until_ms is supplied without freeze_ms, it is treated as a relative
    window (not Unix epoch) so goldens stay deterministic.
    """
    if path_id < 0 or path_id > 0xFFFFFFFFFFFFFFFF:
        raise AscentCodecError("path_id out of u64 range")
    if not (0.0 <= confidence <= 1.0):
        raise AscentCodecError("confidence must be in [0, 1]")
    if freeze_ms < 0 or ttl_ms < 0:
        raise AscentCodecError("freeze_ms and ttl_ms must be >= 0")
    if freeze_until_ms is not None and freeze_ms == 0:
        freeze_ms = int(freeze_until_ms)
    if freeze_ms > 0xFFFFFFFF or ttl_ms > 0xFFFFFFFF:
        raise AscentCodecError("freeze_ms/ttl_ms exceed u32")

    flags = FLAG_RELATIVE_FREEZE
    cap_kbps = 0
    if next_capacity_kbps is not None and next_capacity_bps is not None:
        raise AscentCodecError("pass next_capacity_bps or next_capacity_kbps, not both")
    if next_capacity_kbps is not None:
        flags |= FLAG_CAP_KBPS
        cap_kbps = int(next_capacity_kbps)
    elif next_capacity_bps is None:
        cap_kbps = 0
    elif next_capacity_bps > 0xFFFFFFFF:
        flags |= FLAG_CAP_KBPS
        cap_kbps = (int(next_capacity_bps) + 999) // 1000
    else:
        cap_kbps = int(next_capacity_bps)
    if cap_kbps < 0 or cap_kbps > 0xFFFFFFFF:
        raise AscentCodecError("next_capacity out of u32 range")

    obst_u8 = OBSTRUCTION_ABSENT
    if obstruction is not None:
        if not (0.0 <= obstruction <= 1.0):
            raise AscentCodecError("obstruction must be in [0, 1]")
        flags |= FLAG_HAS_OBSTRUCTION
        obst_u8 = int(round(obstruction * 255.0))
        if obst_u8 > 255:
            obst_u8 = 255

    elev_i16 = ELEV_ABSENT
    if elev_deg is not None:
        if not (-90.0 <= elev_deg <= 90.0):
            raise AscentCodecError("elev_deg must be in [-90, 90]")
        flags |= FLAG_HAS_ELEV
        elev_i16 = int(round(elev_deg * 10.0))
        if elev_i16 < -32768 or elev_i16 > 32767 or elev_i16 == ELEV_ABSENT:
            raise AscentCodecError("elev_deg_x10 unrepresentable")

    if crc:
        flags |= FLAG_CRC

    conf_u16 = int(round(confidence * 10000.0))
    if conf_u16 < 0 or conf_u16 > 10000:
        raise AscentCodecError("confidence quantize out of range")

    body = bytearray()
    body.append(flags & 0xFF)
    body += struct.pack(">Q", path_id)
    body += struct.pack(">I", cap_kbps)
    body += struct.pack(">I", int(freeze_ms))
    body += struct.pack(">H", conf_u16)
    body += struct.pack(">I", int(ttl_ms))
    body.append(obst_u8)
    body += struct.pack(">h", elev_i16)
    if len(body) != PATHHINT_BODY_LEN:
        raise AscentCodecError("PATHHINT v1 body length bug")
    if crc:
        body += struct.pack(">I", crc32_ieee(bytes(body)))

    if len(body) > PATHHINT_MAX_BODY:
        raise AscentCodecError("PATHHINT body over schema cap")
    out = bytearray()
    out.append(LEAD_SKYSTATE)
    out.append(PATHHINT_SCHEMA_V1)
    out += struct.pack(">H", len(body))
    out += body
    return bytes(out)


def _pathhint_skip_event(
    start: int,
    end: int,
    schema: int,
    reason: str,
    flags: int = 0,
    body_len: int = 0,
) -> dict:
    return {
        "kind": "pathhint",
        "schema": schema,
        "applied": False,
        "skipped": True,
        "reason": reason,
        "flags": flags,
        "len": body_len,
        "offset": start,
        "end": end,
    }


def _parse_pathhint_v1_body(body: bytes, start: int, end: int, schema: int) -> dict:
    """Fail-closed: corrupt/unknown => applied=False (unit already skipped by length)."""
    if len(body) < 1:
        return _pathhint_skip_event(start, end, schema, "truncated_body", body_len=len(body))
    flags = body[0]
    if flags & FLAG_RESERVED_MASK:
        return _pathhint_skip_event(
            start, end, schema, "unknown_flags", flags=flags, body_len=len(body)
        )
    want = PATHHINT_BODY_LEN_CRC if (flags & FLAG_CRC) else PATHHINT_BODY_LEN
    if len(body) != want:
        return _pathhint_skip_event(
            start, end, schema, "bad_body_len", flags=flags, body_len=len(body)
        )
    if not (flags & FLAG_RELATIVE_FREEZE):
        return _pathhint_skip_event(
            start, end, schema, "missing_freeze_until", flags=flags, body_len=len(body)
        )
    if flags & FLAG_CRC:
        got = struct.unpack_from(">I", body, PATHHINT_BODY_LEN)[0]
        expect = crc32_ieee(body[:PATHHINT_BODY_LEN])
        if got != expect:
            return _pathhint_skip_event(
                start, end, schema, "crc_fail", flags=flags, body_len=len(body)
            )
    path_id = struct.unpack_from(">Q", body, 1)[0]
    cap_raw = struct.unpack_from(">I", body, 9)[0]
    freeze_ms = struct.unpack_from(">I", body, 13)[0]
    conf_u16 = struct.unpack_from(">H", body, 17)[0]
    ttl_ms = struct.unpack_from(">I", body, 19)[0]
    obst_u8 = body[23]
    elev_i16 = struct.unpack_from(">h", body, 24)[0]
    if conf_u16 > 10000:
        return _pathhint_skip_event(
            start, end, schema, "confidence_range", flags=flags, body_len=len(body)
        )
    if flags & FLAG_CAP_KBPS:
        next_bps = cap_raw * 1000
        next_kbps = cap_raw
    else:
        next_bps = cap_raw
        next_kbps = (cap_raw + 999) // 1000 if cap_raw else 0
    obst = None
    if flags & FLAG_HAS_OBSTRUCTION:
        obst = obst_u8 / 255.0
    elev = None
    if flags & FLAG_HAS_ELEV and elev_i16 != ELEV_ABSENT:
        elev = elev_i16 / 10.0
    return {
        "kind": "pathhint",
        "schema": schema,
        "applied": True,
        "skipped": False,
        "reason": "",
        "flags": flags,
        "path_id": path_id,
        "next_capacity_bps": next_bps,
        "next_capacity_kbps": next_kbps,
        "next_capacity_meaning": "predicted_bottleneck_bps_sender",
        "freeze_ms": freeze_ms,
        "freeze_until_ms": freeze_ms,
        "confidence": conf_u16 / 10000.0,
        "ttl_ms": ttl_ms,
        "obstruction": obst,
        "elev_deg": elev,
        "crc": bool(flags & FLAG_CRC),
        "len": len(body),
        "offset": start,
        "end": end,
    }


def decode_skystate(body: bytes, start: int) -> Tuple[dict, int]:
    """Decode P2 0xC5 SKYSTATE. Unknown/corrupt => skip-by-length, applied=False."""
    i = start + 1
    if i >= len(body):
        raise AscentCodecError("truncated SKYSTATE schema")
    schema = body[i]
    i += 1
    blen, i = _u16be(body, i)
    if blen > P2_SKIP_CAP:
        raise AscentCodecError("SKYSTATE body over skip cap")
    if i + blen > len(body):
        raise AscentCodecError("truncated SKYSTATE body")
    payload = body[i : i + blen]
    i += blen
    if schema != PATHHINT_SCHEMA_V1:
        return (
            _pathhint_skip_event(
                start, i, schema, "unknown_schema", body_len=blen
            ),
            i,
        )
    if blen > PATHHINT_MAX_BODY:
        return (
            _pathhint_skip_event(
                start, i, schema, "over_schema_cap", body_len=blen
            ),
            i,
        )
    return _parse_pathhint_v1_body(payload, start, i, schema), i


def canonical_pathhint_bytes(*, crc: bool = False) -> bytes:
    """Lab golden: 50 Mbps goodput *hint* (not an RF claim), 15s freeze, obst 0.20, el 42.0."""
    return encode_pathhint(
        path_id=0x42,
        next_capacity_bps=50_000_000,
        freeze_ms=15_000,
        confidence=0.80,
        ttl_ms=30_000,
        obstruction=0.20,
        elev_deg=42.0,
        crc=crc,
    )


def encode_turn(
    *,
    session: int,
    turn: int,
    corr: int,
    lifetime_s: int,
    role: int,
    crc: bool = True,
) -> bytes:
    """Encode a Delay Hull TURN / ADUHEAD unit (P2 lead 0xC6, schema 0x01)."""
    if role not in (TURN_ROLE_REQUEST, TURN_ROLE_RESPONSE, TURN_ROLE_ACK_ERASE):
        raise AscentCodecError("role must be 1, 2, or 3")
    for name, val, bits in (
        ("session", session, 64),
        ("corr", corr, 64),
        ("turn", turn, 32),
        ("lifetime_s", lifetime_s, 32),
    ):
        if val < 0 or val >= (1 << bits):
            raise AscentCodecError(f"{name} out of range")
    flags = TURN_FLAG_CRC if crc else 0
    body = bytearray()
    body.append(flags & 0xFF)
    body += struct.pack(">Q", session)
    body += struct.pack(">I", turn)
    body += struct.pack(">Q", corr)
    body += struct.pack(">I", lifetime_s)
    body.append(role & 0xFF)
    body.append(0)
    if len(body) != TURN_BODY_LEN:
        raise AscentCodecError("TURN v1 body length bug")
    if crc:
        body += struct.pack(">I", crc32_ieee(bytes(body)))
    if len(body) > TURN_MAX_BODY:
        raise AscentCodecError("TURN body over schema cap")
    out = bytearray()
    out.append(LEAD_TURN)
    out.append(TURN_SCHEMA_V1)
    out += struct.pack(">H", len(body))
    out += body
    return bytes(out)


def _turn_skip_event(
    start: int,
    end: int,
    schema: int,
    reason: str,
    flags: int = 0,
    body_len: int = 0,
) -> dict:
    return {
        "kind": "turn",
        "schema": schema,
        "applied": False,
        "skipped": True,
        "reason": reason,
        "flags": flags,
        "len": body_len,
        "offset": start,
        "end": end,
    }


def _parse_turn_v1_body(body: bytes, start: int, end: int, schema: int) -> dict:
    if len(body) < 1:
        return _turn_skip_event(start, end, schema, "truncated_body", body_len=len(body))
    flags = body[0]
    if flags & TURN_FLAG_RESERVED_MASK:
        return _turn_skip_event(
            start, end, schema, "unknown_flags", flags=flags, body_len=len(body)
        )
    want = TURN_BODY_LEN_CRC if (flags & TURN_FLAG_CRC) else TURN_BODY_LEN
    if len(body) != want:
        return _turn_skip_event(
            start, end, schema, "bad_body_len", flags=flags, body_len=len(body)
        )
    if flags & TURN_FLAG_CRC:
        got = struct.unpack_from(">I", body, TURN_BODY_LEN)[0]
        expect = crc32_ieee(body[:TURN_BODY_LEN])
        if got != expect:
            return _turn_skip_event(
                start, end, schema, "crc_fail", flags=flags, body_len=len(body)
            )
    session = struct.unpack_from(">Q", body, 1)[0]
    turn = struct.unpack_from(">I", body, 9)[0]
    corr = struct.unpack_from(">Q", body, 13)[0]
    lifetime_s = struct.unpack_from(">I", body, 21)[0]
    role = body[25]
    reserved = body[26]
    if reserved != 0:
        return _turn_skip_event(
            start, end, schema, "bad_reserved", flags=flags, body_len=len(body)
        )
    if role not in (TURN_ROLE_REQUEST, TURN_ROLE_RESPONSE, TURN_ROLE_ACK_ERASE):
        return _turn_skip_event(
            start, end, schema, "bad_role", flags=flags, body_len=len(body)
        )
    role_name = {1: "request", 2: "response", 3: "ack-erase"}[role]
    return {
        "kind": "turn",
        "schema": schema,
        "applied": True,
        "skipped": False,
        "reason": "",
        "flags": flags,
        "session": session,
        "turn": turn,
        "corr": corr,
        "lifetime_s": lifetime_s,
        "role": role,
        "role_name": role_name,
        "crc": bool(flags & TURN_FLAG_CRC),
        "len": len(body),
        "offset": start,
        "end": end,
    }


def decode_turn(body: bytes, start: int) -> Tuple[dict, int]:
    """Decode P2 0xC6 TURN. Unknown/corrupt => skip-by-length, applied=False."""
    i = start + 1
    if i >= len(body):
        raise AscentCodecError("truncated TURN schema")
    schema = body[i]
    i += 1
    blen, i = _u16be(body, i)
    if blen > P2_SKIP_CAP:
        raise AscentCodecError("TURN body over skip cap")
    if i + blen > len(body):
        raise AscentCodecError("truncated TURN body")
    payload = body[i : i + blen]
    i += blen
    if schema != TURN_SCHEMA_V1:
        return (
            _turn_skip_event(start, i, schema, "unknown_schema", body_len=blen),
            i,
        )
    if blen > TURN_MAX_BODY:
        return (
            _turn_skip_event(start, i, schema, "over_schema_cap", body_len=blen),
            i,
        )
    return _parse_turn_v1_body(payload, start, i, schema), i


def canonical_turn_bytes(*, crc: bool = True) -> bytes:
    """Lab golden: one request ADU head, 1 hour lifetime, CRC on."""
    return encode_turn(
        session=0xA5CE47,
        turn=1,
        corr=0x1001,
        lifetime_s=3600,
        role=TURN_ROLE_REQUEST,
        crc=crc,
    )


def decode_stream(data: bytes) -> List[dict]:
    """
    Full decode to list of event dicts.
    P0 + ASCENT-V scalars merge into continuous text events
    (kind="text", text=..., offset, end).
    agent / multimodal (mm_kind) / def / crypto / pathhint / turn / pad / skip as events.
    Never overwrite event kind with numeric wire fields.
    """
    events: List[dict] = []
    i = 0
    text_chars: List[str] = []
    text_start = 0

    def flush_text(end: int) -> None:
        nonlocal text_chars, text_start
        if not text_chars:
            return
        s = "".join(text_chars)
        events.append(
            {
                "kind": "text",
                "text": s,
                "ascii": s,  # back-compat for CLI / older tests
                "len": len(s.encode("utf-8", errors="surrogatepass"))
                if any(ord(c) > 0x7F for c in s)
                else len(s),
                "offset": text_start,
                "end": end,
            }
        )
        text_chars = []

    def push_char(ch: str, at: int) -> None:
        nonlocal text_start, text_chars
        if not text_chars:
            text_start = at
        text_chars.append(ch)

    while i < len(data):
        b = data[i]
        if b < 0x80:
            push_char(chr(b), i)
            i += 1
            continue

        # ASCENT-V (including F5 03 long scalar)
        try:
            v = decode_ascent_v_at(data, i)
        except AscentCodecError:
            # If lead looks like V but is broken, surface the error
            if 0xD0 <= b <= 0xF4 or b == 0xF5:
                raise
            v = None
        if v is not None:
            cp, end_i = v
            push_char(chr(cp), i)
            i = end_i
            continue

        flush_text(i)

        if b == 0x9A:
            ev, i = decode_agent(data, i)
            events.append(ev)
            continue
        if b == 0x9D:
            ev, i = decode_mm(data, i)
            events.append(ev)
            continue
        if b == 0x9C:
            ev, i = decode_crypto(data, i)
            events.append(ev)
            continue
        if b == 0xC0:
            ev, i = decode_def(data, i)
            events.append(ev)
            continue
        if b == LEAD_VERSION_BUMP:
            ev, i = decode_p2_u16_skip(data, i, "VERSION_BUMP")
            events.append(ev)
            continue
        if b == LEAD_REGISTRY_DELTA:
            ev, i = decode_p2_u32_skip(data, i, "REGISTRY_DELTA")
            events.append(ev)
            continue
        if b == LEAD_SKYSTATE:
            ev, i = decode_skystate(data, i)
            events.append(ev)
            continue
        if b == LEAD_TURN:
            ev, i = decode_turn(data, i)
            events.append(ev)
            continue
        if b == LEAD_PRIVATE_OP:
            ev, i = decode_private_op_skip(data, i)
            events.append(ev)
            continue
        if b == 0x9F:
            events.append({"kind": "pad", "count": 1, "offset": i, "end": i + 1})
            i += 1
            continue
        # Cont alone is illegal as lead
        if Cont.is_cont(b):
            raise AscentCodecError(f"orphan Cont lead {b:#04x} at offset {i}")
        raise AscentCodecError(f"unsupported lead byte {b:#04x} at offset {i}")

    flush_text(i)
    return events


# ---------------------------------------------------------------------------
# Hello Universe product sample
# ---------------------------------------------------------------------------


def hello_universe_bytes() -> bytes:
    """Canonical Hello Universe sample from SPEC.md section E."""
    media = b"ASCENT Hello Universe sample media v1"
    digest = hashlib.sha256(media).digest()
    ref = b"cid:sha256:aabbccddeeff0011223344556677889"
    assert len(ref) == 42
    out = bytearray()
    out += HEADER_MAGIC
    out += b"Hello, Universe.\n"
    # agent ROLE=guide
    out.append(0x9A)
    out.append(0xC1)
    out.append(0x01)
    out += struct.pack(">H", 0x0002)
    out.append(0x00)
    args = bytes([5]) + b"guide"
    out += struct.pack(">H", len(args))
    out += args
    out.append(0x9B)
    # MM REF
    out.append(0x9D)
    out.append(0x4D)
    out.append(0x01)  # REF
    out += struct.pack(">H", 0x0005)  # octet-stream
    out.append(0x01)  # EXTERNAL
    out.append(0x01)  # sha-256
    out += digest
    out += struct.pack(">Q", len(ref))
    out += ref
    return bytes(out)


def events_to_jsonable(events: Sequence[Any]) -> List[dict]:
    """
    Flatten events for JSON. Event kind string is always authoritative;
    detail fields never overwrite kind (mm wire kind lives in mm_kind).
    """
    out: List[dict] = []
    for e in events:
        if isinstance(e, dict):
            kind = e.get("kind", "unknown")
            detail = {k: v for k, v in e.items() if k != "kind"}
            # Defense: never let a nested kind clobber
            detail.pop("kind", None)
            row = {"kind": kind}
            row.update(detail)
            out.append(row)
        else:
            # Event dataclass-like: .kind + .detail
            kind = getattr(e, "kind", "unknown")
            detail = dict(getattr(e, "detail", {}) or {})
            detail.pop("kind", None)
            row = {"kind": kind}
            row.update(detail)
            out.append(row)
    return out
