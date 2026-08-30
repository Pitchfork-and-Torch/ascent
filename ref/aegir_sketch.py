#!/usr/bin/env python3
# AEGIR reference sketch - ASCENT-native hybrid encryption (design/AEGIR.md).
# Profiles:
#   AEGIR-DEMO (0x010B): X25519 + AES-GCM + HBOP  - CI golden vectors
#   AEGIR-DCH-768 (0x0101): ML-KEM-768 + X25519 AND hybrid when kyber_py present
# No production secrets. Demo seeds are fixed for vectors only.
# ASCII hyphens only. Optional deps: cryptography (required), kyber_py (DCH).

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Registry seeds (SPEC.md C.3.3 registered AEGIR range + design/AEGIR.md)
# ---------------------------------------------------------------------------

ALG_AEGIR_SUITE_1 = 0x0100
ALG_AEGIR_DCH_KEM_768 = 0x0101
ALG_AEGIR_DCH_KEM_1024 = 0x0102
ALG_AEGIR_AEAD_AES256_GCMSIV = 0x0103
ALG_AEGIR_AEAD_CHACHA20POLY = 0x0104
ALG_AEGIR_HBOP_SHA512 = 0x0105
ALG_AEGIR_SIG_HYBRID_65 = 0x0106
ALG_AEGIR_SIG_SLH_128F = 0x0107
ALG_AEGIR_DSR_STATE = 0x0108
ALG_AEGIR_MPR_V1 = 0x0109
ALG_AEGIR_IMS_SEAL = 0x010A
ALG_AEGIR_DEMO = 0x010B

ALG_NAMES = {
    ALG_AEGIR_SUITE_1: "AEGIR-SUITE-1",
    ALG_AEGIR_DCH_KEM_768: "AEGIR-DCH-KEM-768",
    ALG_AEGIR_DCH_KEM_1024: "AEGIR-DCH-KEM-1024",
    ALG_AEGIR_AEAD_AES256_GCMSIV: "AEGIR-AEAD-AES256-GCMSIV",
    ALG_AEGIR_AEAD_CHACHA20POLY: "AEGIR-AEAD-CHACHA20POLY",
    ALG_AEGIR_HBOP_SHA512: "AEGIR-HBOP-SHA512",
    ALG_AEGIR_SIG_HYBRID_65: "AEGIR-SIG-HYBRID-65",
    ALG_AEGIR_SIG_SLH_128F: "AEGIR-SIG-SLH-128f",
    ALG_AEGIR_DSR_STATE: "AEGIR-DSR-STATE",
    ALG_AEGIR_MPR_V1: "AEGIR-MPR-V1",
    ALG_AEGIR_IMS_SEAL: "AEGIR-IMS-SEAL",
    ALG_AEGIR_DEMO: "AEGIR-DEMO-X25519-GCM",
}

OPCODE_STOP = 0x0001
OPCODE_ROLE = 0x0002
OPCODE_CAP = 0x0006
OPCODE_SAFETY = 0x0007

SUITE_MAGIC = b"ASCENT/1.0\nAEGIR/1.0\n"
PLAINTEXT_HELLO = b"Hello, Universe.\n"
DEMO_KID = b"demo-kid-1"
DEMO_FREEZE_LABEL = b"AEGIR-DEMO-FREEZE-v1"
DEMO_X25519_SEED_LABEL = b"AEGIR-DEMO-X25519-SEED"
DEMO_EPH_SEED_LABEL = b"AEGIR-DEMO-EPH-SEED"
DEMO_AEAD_NONCE_LABEL = b"AEGIR-DEMO-AEAD-NONCE"
DEMO_EPHYS = bytes([0x42]) * 32
DEMO_SESSION = b"demo-session-1"
HBOP_DOMAIN = b"HBOP0001"

# Ghost Continuum IMS domain strings (wire-visible seal only)
IMS_DOMAIN = b"AEGIR-IMS-SEAL-v1"


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def hkdf_sha512(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    if not salt:
        salt = bytes(64)
    prk = hmac.new(salt, ikm, hashlib.sha512).digest()
    okm = b""
    t = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha512).digest()
        okm += t
        counter += 1
    return okm[:length]


def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("xor length mismatch")
    return bytes(x ^ y for x, y in zip(a, b))


def has_ml_kem() -> bool:
    try:
        from kyber_py.ml_kem import ML_KEM_768  # noqa: F401

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# AEAD / CTR via cryptography
# ---------------------------------------------------------------------------

def _require_crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except ImportError as e:
        raise RuntimeError("AEGIR requires the 'cryptography' package.") from e


def _aes_gcm_encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes) -> Tuple[bytes, bytes]:
    _require_crypto()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    ct_tag = AESGCM(key).encrypt(nonce, plaintext, aad)
    return ct_tag[:-16], ct_tag[-16:]


def _aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes) -> bytes:
    _require_crypto()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return AESGCM(key).decrypt(nonce, ciphertext + tag, aad)


def _aes_ctr_keystream(key: bytes, nonce16: bytes, n: int) -> bytes:
    _require_crypto()
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if len(nonce16) != 16:
        raise ValueError("CTR nonce must be 16 bytes")
    enc = Cipher(algorithms.AES(key), modes.CTR(nonce16), backend=default_backend()).encryptor()
    return enc.update(bytes(n)) + enc.finalize()


# ---------------------------------------------------------------------------
# X25519
# ---------------------------------------------------------------------------

def _x25519_from_seed(seed: bytes):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    sk = X25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return seed, pk


def _x25519_demo_keypair() -> Tuple[bytes, bytes]:
    return _x25519_from_seed(sha256(DEMO_X25519_SEED_LABEL))


def _x25519_encaps(peer_pk: bytes, eph_seed: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey,
        X25519PublicKey,
    )
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    if eph_seed is None:
        eph = X25519PrivateKey.generate()
    else:
        eph = X25519PrivateKey.from_private_bytes(eph_seed)
    eph_pk = eph.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ss = eph.exchange(X25519PublicKey.from_public_bytes(peer_pk))
    return eph_pk, ss


def _x25519_decaps(sk_bytes: bytes, eph_pk: bytes) -> bytes:
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey,
        X25519PublicKey,
    )

    return X25519PrivateKey.from_private_bytes(sk_bytes).exchange(
        X25519PublicKey.from_public_bytes(eph_pk)
    )


# ---------------------------------------------------------------------------
# ML-KEM-768 (optional)
# ---------------------------------------------------------------------------

def _mlkem768_keygen() -> Tuple[bytes, bytes]:
    from kyber_py.ml_kem import ML_KEM_768

    return ML_KEM_768.keygen()  # ek, dk


def _mlkem768_encaps(ek: bytes) -> Tuple[bytes, bytes]:
    """Return (ct, ss) FIPS-order."""
    from kyber_py.ml_kem import ML_KEM_768

    ss, ct = ML_KEM_768.encaps(ek)
    return ct, ss


def _mlkem768_decaps(dk: bytes, ct: bytes) -> bytes:
    from kyber_py.ml_kem import ML_KEM_768

    return ML_KEM_768.decaps(dk, ct)


# ---------------------------------------------------------------------------
# ASCENT framing
# ---------------------------------------------------------------------------

def agent_frame(opcode: int, name: bytes, ver: int = 1, flags: int = 0) -> bytes:
    if len(name) > 255:
        raise ValueError("name too long")
    args = bytes([len(name)]) + name
    body = struct.pack("!BHBH", ver, opcode, flags, len(args)) + args
    return b"\x9a\xc1" + body + b"\x9b"


def p7_frame(alg: int, kid: bytes, nonce: bytes, ct: bytes) -> bytes:
    if len(kid) > 255 or len(nonce) > 255:
        raise ValueError("kid/nonce too long")
    if len(ct) > 0xFFFFFFFF:
        raise ValueError("ct too long")
    return (
        b"\x9c\x4b"
        + struct.pack("!H", alg)
        + bytes([len(kid)])
        + kid
        + bytes([len(nonce)])
        + nonce
        + struct.pack("!I", len(ct))
        + ct
    )


def build_aad(suite_id: int, freeze_hash: bytes, kid: bytes, role_chain_hash: bytes) -> bytes:
    return struct.pack("!H", suite_id) + freeze_hash + kid + role_chain_hash


def scc_schedule(ss: bytes, session_id: bytes) -> Tuple[bytes, bytes, bytes]:
    seed = hkdf_sha512(ss, salt=session_id, info=b"AEGIR-SCC-SEED-v1", length=32)
    walk_parts = [sha512(seed + struct.pack("!I", i)) for i in range(8)]
    walk_transcript_hash = sha512(b"".join(walk_parts))
    k_sched = hkdf_sha512(
        walk_transcript_hash + ss, salt=b"", info=b"AEGIR-SCC-SCHED-v1", length=96
    )
    return k_sched[0:32], k_sched[32:64], k_sched[64:96]


def hbop_pad(
    h_root: bytes,
    e_phys: bytes,
    ss_prefix: bytes,
    freeze_hash: bytes,
    session_id: bytes,
    msg_counter: int,
    n: int,
) -> Tuple[bytes, bytes]:
    pad_key = hkdf_sha512(
        h_root + e_phys + ss_prefix,
        salt=freeze_hash,
        info=b"AEGIR-HBOP-v1" + session_id + struct.pack("!I", msg_counter),
        length=32,
    )
    nonce16 = (HBOP_DOMAIN + struct.pack("!I", msg_counter) + b"\x00" * 4)[:16]
    stream = _aes_ctr_keystream(pad_key, nonce16, n)
    meta = (
        bytes([1, 2])
        + h_root[:32]
        + sha256(e_phys)
        + struct.pack("!I", msg_counter)
        + HBOP_DOMAIN
    )
    return stream, meta


def ims_seal_body(
    state_root: bytes,
    event_hash: bytes,
    action: int = 1,
) -> bytes:
    """
    Immune Merkle Seal record (alg 0x010A).
    action: 1=FREEZE 2=ERASE 3=QUARANTINE
    Wire body is public; signature is out of band or future hybrid-sig append.
    """
    if len(state_root) != 32 or len(event_hash) != 32:
        raise ValueError("state_root and event_hash must be 32 bytes")
    return (
        bytes([1, action])  # version, action
        + IMS_DOMAIN
        + state_root
        + event_hash
        + struct.pack("!Q", 0)  # time placeholder (0 in vectors)
    )


def build_ims_frame(
    state_root: bytes,
    event_hash: bytes,
    action: int = 1,
    kid: bytes = b"ims",
) -> bytes:
    return p7_frame(ALG_AEGIR_IMS_SEAL, kid, b"", ims_seal_body(state_root, event_hash, action))


# ---------------------------------------------------------------------------
# Dual-Core Hybrid
# ---------------------------------------------------------------------------

@dataclass
class DchResult:
    kem_ct: bytes
    ss: bytes
    mode: str  # "demo" | "dch-768"


def dch_encaps(
    peer_x25519_pk: bytes,
    context: bytes,
    freeze_hash: bytes,
    *,
    peer_mlkem_ek: Optional[bytes] = None,
    eph_x25519_seed: Optional[bytes] = None,
    require_pq: bool = False,
) -> DchResult:
    eph_pk, ss_cl = _x25519_encaps(peer_x25519_pk, eph_seed=eph_x25519_seed)

    if peer_mlkem_ek is not None:
        if not has_ml_kem():
            raise RuntimeError("ML-KEM peer key provided but kyber_py is not installed")
        ct_pq, ss_pq = _mlkem768_encaps(peer_mlkem_ek)
        kem_ct = ct_pq + eph_pk
        ss_raw = ss_pq + ss_cl
        mode = "dch-768"
        suite_marker = struct.pack("!H", ALG_AEGIR_DCH_KEM_768)
    else:
        if require_pq:
            raise RuntimeError("PQ required but no ML-KEM peer key")
        # DEMO: zero PQ share is explicit; sealed profiles must not use this path
        ss_pq = bytes(32)
        kem_ct = eph_pk
        ss_raw = ss_pq + ss_cl
        mode = "demo"
        suite_marker = struct.pack("!H", ALG_AEGIR_DEMO)

    ss = hkdf_sha512(
        ss_raw,
        salt=freeze_hash,
        info=b"AEGIR-DCH-KEM-v1" + suite_marker + context,
        length=64,
    )
    return DchResult(kem_ct=kem_ct, ss=ss, mode=mode)


def dch_decaps(
    sk_x25519: bytes,
    kem_ct: bytes,
    context: bytes,
    freeze_hash: bytes,
    *,
    sk_mlkem_dk: Optional[bytes] = None,
    require_pq: bool = False,
) -> DchResult:
    if sk_mlkem_dk is not None:
        if not has_ml_kem():
            raise RuntimeError("ML-KEM secret provided but kyber_py is not installed")
        if len(kem_ct) < 1088 + 32:
            raise ValueError("kem_ct too short for DCH-768")
        ct_pq = kem_ct[:1088]
        eph_pk = kem_ct[1088 : 1088 + 32]
        ss_pq = _mlkem768_decaps(sk_mlkem_dk, ct_pq)
        ss_cl = _x25519_decaps(sk_x25519, eph_pk)
        ss_raw = ss_pq + ss_cl
        mode = "dch-768"
        suite_marker = struct.pack("!H", ALG_AEGIR_DCH_KEM_768)
        full_ct = kem_ct
    else:
        if require_pq:
            raise RuntimeError("PQ required but no ML-KEM secret")
        eph_pk = kem_ct[:32]
        ss_pq = bytes(32)
        ss_cl = _x25519_decaps(sk_x25519, eph_pk)
        ss_raw = ss_pq + ss_cl
        mode = "demo"
        suite_marker = struct.pack("!H", ALG_AEGIR_DEMO)
        full_ct = kem_ct

    ss = hkdf_sha512(
        ss_raw,
        salt=freeze_hash,
        info=b"AEGIR-DCH-KEM-v1" + suite_marker + context,
        length=64,
    )
    return DchResult(kem_ct=full_ct, ss=ss, mode=mode)


# ---------------------------------------------------------------------------
# Encrypt / decrypt streams
# ---------------------------------------------------------------------------

def encrypt_stream(
    plaintext: bytes,
    *,
    kid: bytes = DEMO_KID,
    e_phys: bytes = DEMO_EPHYS,
    msg_counter: int = 1,
    session_id: bytes = DEMO_SESSION,
    deterministic: bool = False,
    use_dch768: bool = False,
    attach_ims: bool = False,
    attach_mpr: bool = True,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Build greppable ASCENT+AEGIR stream with ROLE, CAP, P7 suite, optional MPR/IMS.
    """
    freeze_hash = sha256(DEMO_FREEZE_LABEL)
    sk_x, pk_x = _x25519_demo_keypair()

    mlkem_ek = mlkem_dk = None
    if use_dch768:
        if not has_ml_kem():
            raise RuntimeError("use_dch768 requires kyber_py (pip install kyber-py)")
        mlkem_ek, mlkem_dk = _mlkem768_keygen()

    role_sender = agent_frame(OPCODE_ROLE, b"sender")
    cap_enc = agent_frame(OPCODE_CAP, b"encrypt")
    role_chain_hash = sha256(role_sender + cap_enc)

    eph_seed = sha256(DEMO_EPH_SEED_LABEL) if deterministic else None
    if use_dch768 and deterministic:
        # ML-KEM encaps is not seedable in kyber_py public API; force non-det PQ
        # but keep X25519 eph fixed when deterministic flag set.
        pass

    context = freeze_hash + session_id + role_chain_hash
    dch = dch_encaps(
        pk_x,
        context,
        freeze_hash,
        peer_mlkem_ek=mlkem_ek,
        eph_x25519_seed=eph_seed,
        require_pq=use_dch768,
    )

    k_aead, _k_mac, _k_ratchet = scc_schedule(dch.ss, session_id)
    suite_id = ALG_AEGIR_DCH_KEM_768 if use_dch768 else ALG_AEGIR_DEMO
    aad = build_aad(suite_id, freeze_hash, kid, role_chain_hash)
    aad_hash = sha256(aad)

    if deterministic:
        nonce = sha256(DEMO_AEAD_NONCE_LABEL)[:12]
    else:
        nonce = os.urandom(12)

    c_aead, tag = _aes_gcm_encrypt(k_aead, nonce, plaintext, aad)
    h_root = sha256(b"HISTORY:" + DEMO_FREEZE_LABEL)
    pad, hbop_meta = hbop_pad(
        h_root, e_phys, dch.ss[:32], freeze_hash, session_id, msg_counter, len(c_aead)
    )
    c_outer = xor_bytes(c_aead, pad)

    flags = 0x03  # TAG_OUTSIDE_PAD | HBOP_PRESENT
    body = bytearray()
    body.append(1)
    body.append(flags)
    body += struct.pack("!H", suite_id)
    body += struct.pack("!H", suite_id)  # kem container id
    body += struct.pack("!H", ALG_AEGIR_DEMO if not use_dch768 else ALG_AEGIR_AEAD_AES256_GCMSIV)
    body.append(1)
    body += freeze_hash
    body += aad_hash
    body += struct.pack("!H", len(dch.kem_ct)) + dch.kem_ct
    body.append(len(nonce))
    body += nonce
    body += struct.pack("!I", len(c_outer)) + c_outer
    body += struct.pack("!H", len(tag)) + tag
    body += struct.pack("!H", len(hbop_meta)) + hbop_meta
    body += struct.pack("!H", 0)

    stream = bytearray()
    stream += SUITE_MAGIC
    stream += role_sender
    stream += cap_enc
    stream += p7_frame(suite_id, kid, b"", bytes(body))

    if attach_mpr:
        mpr_blob = sha256(b"AEGIR-MT-DECOY-v1" + freeze_hash) + b"MPR-DEMO"
        stream += p7_frame(ALG_AEGIR_MPR_V1, b"mpr", b"", mpr_blob)

    if attach_ims:
        state_root = sha256(bytes(stream) + freeze_hash)
        event_hash = sha256(b"ceremony-complete" + aad_hash)
        stream += build_ims_frame(state_root, event_hash, action=1)

    info: Dict[str, Any] = {
        "mode": dch.mode,
        "suite_id": suite_id,
        "suite_name": ALG_NAMES.get(suite_id, "unknown"),
        "freeze_hash": freeze_hash.hex(),
        "aad_hash": aad_hash.hex(),
        "wire_len": len(stream),
        "ml_kem": has_ml_kem(),
        "deterministic": deterministic,
        # keep demo secret material out of default prints; tests may use sk via recompute
        "has_mlkem_keys": mlkem_dk is not None,
    }
    # Return keys only for in-process round-trip helpers (not written to golden files)
    info["_sk_x"] = sk_x
    info["_mlkem_dk"] = mlkem_dk
    info["_mlkem_ek"] = mlkem_ek
    return bytes(stream), info


def _skip_agent(stream: bytes, i: int) -> int:
    if stream[i : i + 2] != b"\x9a\xc1":
        raise ValueError("expected agent frame")
    _ver, _op, _fl, alen = struct.unpack_from("!BHBH", stream, i + 2)
    i = i + 2 + 1 + 2 + 1 + 2 + alen + 1
    if stream[i - 1] != 0x9B:
        raise ValueError("agent frame missing close")
    return i


def decrypt_stream(
    stream: bytes,
    *,
    e_phys: bytes = DEMO_EPHYS,
    session_id: bytes = DEMO_SESSION,
    mlkem_dk: Optional[bytes] = None,
    require_pq: bool = False,
) -> bytes:
    if not stream.startswith(SUITE_MAGIC):
        raise ValueError("missing ASCENT/AEGIR greppable magic")

    i = len(SUITE_MAGIC)
    i = _skip_agent(stream, i)
    i = _skip_agent(stream, i)

    if stream[i : i + 2] != b"\x9c\x4b":
        raise ValueError("expected P7 crypto frame")
    i += 2
    alg = struct.unpack_from("!H", stream, i)[0]
    i += 2
    kid_len = stream[i]
    i += 1
    kid = stream[i : i + kid_len]
    i += kid_len
    nonce_len = stream[i]
    i += 1
    i += nonce_len  # outer nonce unused
    ct_len = struct.unpack_from("!I", stream, i)[0]
    i += 4
    body = stream[i : i + ct_len]

    j = 0
    version = body[j]
    j += 1
    flags = body[j]
    j += 1
    if version != 1:
        raise ValueError("bad suite version")
    suite_id = struct.unpack_from("!H", body, j)[0]
    j += 2
    j += 2  # kem_alg
    j += 2  # aead_alg
    j += 1  # freeze hash alg
    freeze_hash = body[j : j + 32]
    j += 32
    aad_hash = body[j : j + 32]
    j += 32
    kem_ct_len = struct.unpack_from("!H", body, j)[0]
    j += 2
    kem_ct = body[j : j + kem_ct_len]
    j += kem_ct_len
    aead_nonce_len = body[j]
    j += 1
    aead_nonce = body[j : j + aead_nonce_len]
    j += aead_nonce_len
    aead_ct_len = struct.unpack_from("!I", body, j)[0]
    j += 4
    c_outer = body[j : j + aead_ct_len]
    j += aead_ct_len
    tag_len = struct.unpack_from("!H", body, j)[0]
    j += 2
    tag = body[j : j + tag_len]
    j += tag_len
    hbop_meta_len = struct.unpack_from("!H", body, j)[0]
    j += 2
    hbop_meta = body[j : j + hbop_meta_len]

    if freeze_hash != sha256(DEMO_FREEZE_LABEL):
        raise ValueError("freeze hash mismatch (NSDR / freeze)")

    if alg not in (ALG_AEGIR_DEMO, ALG_AEGIR_DCH_KEM_768, ALG_AEGIR_SUITE_1):
        raise ValueError(f"alg not in demo/dch freeze set: {alg:#06x}")

    sk_x, _pk = _x25519_demo_keypair()
    role_sender = agent_frame(OPCODE_ROLE, b"sender")
    cap_enc = agent_frame(OPCODE_CAP, b"encrypt")
    role_chain_hash = sha256(role_sender + cap_enc)
    context = freeze_hash + session_id + role_chain_hash

    # Fail closed: DCH suite without dk never falls back to DEMO decaps
    if suite_id == ALG_AEGIR_DCH_KEM_768 and mlkem_dk is None:
        raise ValueError("DCH-768 ciphertext requires ML-KEM decapsulation key")
    if require_pq and mlkem_dk is None:
        raise ValueError("PQ required but no ML-KEM decapsulation key")

    dch = dch_decaps(
        sk_x,
        kem_ct,
        context,
        freeze_hash,
        sk_mlkem_dk=mlkem_dk,
        require_pq=mlkem_dk is not None,
    )
    k_aead, _, _ = scc_schedule(dch.ss, session_id)
    aad = build_aad(suite_id, freeze_hash, kid, role_chain_hash)
    if sha256(aad) != aad_hash:
        raise ValueError("aad hash mismatch")

    if flags & 0x02:
        msg_counter = struct.unpack_from("!I", hbop_meta, 2 + 32 + 32)[0]
        h_root = sha256(b"HISTORY:" + DEMO_FREEZE_LABEL)
        if hbop_meta[2:34] != h_root[:32]:
            raise ValueError("hbop h_root commitment mismatch")
        if hbop_meta[34:66] != sha256(e_phys):
            raise ValueError("hbop e_phys commitment mismatch")
        pad, _ = hbop_pad(
            h_root, e_phys, dch.ss[:32], freeze_hash, session_id, msg_counter, len(c_outer)
        )
        c_aead = xor_bytes(c_outer, pad)
    else:
        c_aead = c_outer

    return _aes_gcm_decrypt(k_aead, aead_nonce, c_aead, tag, aad)


# Back-compat aliases
def encrypt_demo(plaintext: bytes, **kwargs) -> Tuple[bytes, dict]:
    kwargs.setdefault("deterministic", False)
    return encrypt_stream(plaintext, use_dch768=False, **kwargs)


def decrypt_demo(stream: bytes, **kwargs) -> bytes:
    return decrypt_stream(stream, **kwargs)


# ---------------------------------------------------------------------------
# Golden vector I/O
# ---------------------------------------------------------------------------

def make_golden_demo() -> dict:
    stream, info = encrypt_stream(
        PLAINTEXT_HELLO,
        deterministic=True,
        use_dch768=False,
        attach_mpr=True,
        attach_ims=True,
    )
    pt = decrypt_stream(stream)
    assert pt == PLAINTEXT_HELLO
    return {
        "name": "TV-DEMO-1-hello-universe",
        "profile": "AEGIR-DEMO",
        "alg": f"0x{ALG_AEGIR_DEMO:04X}",
        "plaintext_utf8": PLAINTEXT_HELLO.decode("utf-8"),
        "freeze_hash_hex": info["freeze_hash"],
        "aad_hash_hex": info["aad_hash"],
        "wire_len": info["wire_len"],
        "wire_hex": stream.hex(),
        "p0_prefix_hex": stream[: len(SUITE_MAGIC)].hex(),
        "notes": "Deterministic DEMO: fixed X25519 eph seed + AEAD nonce. Not Mythos-grade.",
    }


def self_test() -> int:
    print("AEGIR self-test")
    # DEMO random
    stream, info = encrypt_stream(PLAINTEXT_HELLO, deterministic=False)
    pt = decrypt_stream(stream)
    ok_rt = pt == PLAINTEXT_HELLO
    p0_ok = stream.startswith(SUITE_MAGIC)
    leak = PLAINTEXT_HELLO in stream[len(SUITE_MAGIC) :]
    print(f"  demo_rt       = {ok_rt} wire_len={info['wire_len']} mode={info['mode']}")
    print(f"  p0_magic      = {p0_ok}")
    print(f"  no_pt_leak    = {not leak}")

    # DEMO deterministic stability
    g1 = make_golden_demo()
    g2 = make_golden_demo()
    det_ok = g1["wire_hex"] == g2["wire_hex"]
    print(f"  demo_det      = {det_ok} wire_len={g1['wire_len']}")

    # Freeze reject
    bad = bytearray(bytes.fromhex(g1["wire_hex"]))
    # corrupt freeze inside body is hard; test via wrong e_phys
    try:
        decrypt_stream(bytes.fromhex(g1["wire_hex"]), e_phys=bytes([0x00]) * 32)
        hbop_ok = False
    except ValueError:
        hbop_ok = True
    print(f"  hbop_reject   = {hbop_ok}")

    # MPR alg name registry
    reg_ok = ALG_NAMES[ALG_AEGIR_DCH_KEM_768] == "AEGIR-DCH-KEM-768"
    print(f"  registry      = {reg_ok}")

    # IMS frame parse
    ims = build_ims_frame(sha256(b"s"), sha256(b"e"), action=1)
    ims_ok = ims[:2] == b"\x9c\x4b" and struct.unpack_from("!H", ims, 2)[0] == ALG_AEGIR_IMS_SEAL
    print(f"  ims_frame     = {ims_ok}")

    # DCH-768 optional
    dch_ok = True
    if has_ml_kem():
        s2, i2 = encrypt_stream(PLAINTEXT_HELLO, use_dch768=True, deterministic=False)
        pt2 = decrypt_stream(s2, mlkem_dk=i2["_mlkem_dk"])
        dch_ok = pt2 == PLAINTEXT_HELLO and i2["mode"] == "dch-768"
        print(f"  dch768_rt     = {dch_ok} wire_len={i2['wire_len']}")
        # AND hybrid: wrong mlkem should fail
        try:
            _ek, wrong_dk = _mlkem768_keygen()
            decrypt_stream(s2, mlkem_dk=wrong_dk)
            and_ok = False
        except Exception:
            and_ok = True
        print(f"  dch768_and    = {and_ok}")
        dch_ok = dch_ok and and_ok
    else:
        print("  dch768_rt     = SKIP (kyber_py not installed)")

    all_ok = ok_rt and p0_ok and (not leak) and det_ok and hbop_ok and reg_ok and ims_ok and dch_ok
    print("PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="AEGIR reference sketch (ASCENT-native)")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--golden", action="store_true", help="print deterministic DEMO golden JSON")
    p.add_argument("--write-golden", metavar="PATH", help="write golden JSON + .bin beside it")
    p.add_argument("--encrypt", metavar="TEXT")
    p.add_argument("--dch768", action="store_true", help="use ML-KEM-768 + X25519 DCH")
    p.add_argument("--decrypt-hex", metavar="HEX")
    p.add_argument("--list-algs", action="store_true")
    args = p.parse_args(argv)

    if args.list_algs:
        for k, v in sorted(ALG_NAMES.items()):
            print(f"0x{k:04X}  {v}")
        return 0

    if args.golden or args.write_golden:
        g = make_golden_demo()
        text = json.dumps(g, indent=2) + "\n"
        if args.write_golden:
            path = Path(args.write_golden)
            path.write_text(text, encoding="utf-8", newline="\n")
            bin_path = path.with_suffix(".bin")
            if bin_path.suffix != ".bin":
                bin_path = path.parent / (path.stem + ".ascent.bin")
            # Prefer examples naming
            if path.name.endswith(".json"):
                bin_path = path.with_name(path.stem.replace("_vectors", "") + ".ascent.bin")
            bin_path.write_bytes(bytes.fromhex(g["wire_hex"]))
            print(f"wrote {path} and {bin_path} ({g['wire_len']} bytes)", file=sys.stderr)
        else:
            sys.stdout.write(text)
        return 0

    if args.encrypt is not None:
        stream, info = encrypt_stream(
            args.encrypt.encode("utf-8"),
            use_dch768=args.dch768,
            deterministic=False,
        )
        print(stream.hex())
        print(f"# mode={info['mode']} wire_len={info['wire_len']}", file=sys.stderr)
        return 0

    if args.decrypt_hex:
        stream = bytes.fromhex(args.decrypt_hex.replace(" ", ""))
        pt = decrypt_stream(stream)
        sys.stdout.buffer.write(pt)
        return 0

    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
