# AEGIR 1.0 - ASCENT Encryption with Ghost-Immune Resilience

**Status:** Design specification (companion to ASCENT wire 1.0 / 1.1)  
**License intent:** MIT when published as a Pitchfork-and-Torch product surface  
**Normative wire host:** [ASCENT SPEC.md](../SPEC.md) (parse law, planes P0-P10+, profiles 7/E/D/A)  
**Live ASCENT:** https://ascent.jonbailey.xyz/  
**Repo:** https://github.com/Pitchfork-and-Torch/ascent  
**Ghost Continuum lineage:** polymorphic defense, NSGA-II genomes, Merkle-sealed forensics (https://ghost.jonbailey.xyz/)  

**Version:** 1.0.0-draft  
**Date:** 2026-07-29  

This document is self-contained for implementers. Where it extends ASCENT algorithm tables, extensions are **append-only P8 registry entries** and never redefine sacred P0 or the P1/P2 shell.

---

## A. Name, Abstract, and Design Laws

### A.1 Name

**AEGIR** (AY-gur).

| Letter | Stands for |
|--------|------------|
| **A** | **A**SCENT-native |
| **E** | **E**ncryption |
| **G** | **G**host-immune (living immune fabric) |
| **I** | **I**ntegrity-first (fail closed, seal, freeze) |
| **R** | **R**esilient hybrid cores (classical + PQ + outer pad) |

Public title: **ASCENT Encryption with Ghost-Immune Resilience.**  
Committee title: **Agent-native Envelope for Greppable Interplanetary Records.**  
Mnemonic: *aegir* - deep water, storm-proof hull, no silent leaks.

### A.2 Abstract

AEGIR is a hybrid post-quantum encryption and key-lifecycle system that is a **first-class citizen of the ASCENT wire**. Every ciphertext, envelope, signature, nonce, and control token lives inside ASCENT planes. Primary sealed material rides in **P7 CRYPTO** frames (`0x9C 0x4B ...`). Key ceremony, role attestation, capability grants, handoff, and safety quarantine use **P5 agent fences**. Integrity commitments use **P6 content hashes**. Algorithm agility, version history, and mid-mission freeze use **P8 DEF** with append-only history. Transport resilience for deep space uses **P9 outer ECC** with erase-on-fail. Private planes may carry **decoy ciphertexts** that pattern-matchers accept and real verification rejects.

AEGIR does not treat "algebraic hardness + expert review" as enough for a fifty-year horizon. Frontier autonomous cryptanalysis (Mythos-class) has already found lattice automorphisms and novel algebraic bridges that human review missed. Open-weight agentic models (Kimi-class) can fine-tune on protocol traces and chain unmonitored exploits. Therefore AEGIR layers:

1. **Dual-Core Hybrid (DCH)** classical + NIST PQ primitives with **AND** composition (no silent single-core fallback).  
2. **History-Bound Outer Pad (HBOP)** derived from cumulative P8 history roots plus high-min-entropy physical or probe entropy, so an algebraic break is **contained**.  
3. **Sparse Combinatorial Core (SCC)** key schedule on expander structure, not lattice-only.  
4. **Manifold Poisoning Register (MPR)** and **Mobius Trap** decoy structure that burns transformer search budget without carrying real secrets.  
5. **Agent Consensus Gate (ACG)** via ROLE / CAP / HANDOFF / SAFETY with **CRITICAL hard-fault** on unknown opcodes in sealed sessions.  
6. **Immune Merkle Seal (IMS)** from Ghost Continuum philosophy: continuous integrity, sealed forensic ledger, freeze or erase rather than silent degrade.  
7. **No Silent Downgrade Registry (NSDR)** and **ASCENT-D freeze** of the allowed algorithm set.

Philosophy, in the voice of the parent standard:

> Keep every classic ASCII byte sacred. Then ascend hybrid post-quantum envelopes, agent-fenced ceremony, content-addressed integrity, and deep-space resilience into one greppable stream - without burning the stairs, without silent downgrade, and without trusting a single algebraic family against a Mythos-class mind.

### A.3 Design Laws (eternal for AEGIR 1.x)

1. **Sacred P0.** `byte < 0x80` is classic 7-bit ASCII, bit-identical, width 1, forever. Overlong encodings of `0x00-0x7F` are illegal forever. Pure-ASCII subsets of any AEGIR stream remain valid **ASCENT-7**, non-executing, greppable.  
2. **Plane citizenship.** No parallel proprietary framing that bypasses ASCENT parse law. AEGIR material nests in P5-P9 (and optional P10+ decoys).  
3. **No silent downgrade.** Algorithm IDs come only from the append-only P8 PQ / AEGIR registry. Receivers MUST reject or skip-by-length; they MUST NOT substitute a weaker suite because "it decrypts." ASCENT-D freezes are binding mid-mission.  
4. **Keys out of band.** Private keys never appear in P7 bodies. `kid` names key material. Ceremony may transport public keys and attestations only.  
5. **AND hybrid, not OR.** In suite profiles that declare Dual-Core Hybrid, both cores MUST succeed. Falling back to classical-only or PQ-only under attack is non-conformant.  
6. **Outer containment.** Bulk plaintext confidentiality in sealed profiles is protected by HBOP outside the algebraic AEAD. Breaking lattices or AES alone is not enough.  
7. **Fail closed.** Truncation, illegal constructs, unknown CRITICAL opcodes, CAP mismatch, freeze violation, or parity failure (profile D) => hard-fault, erase unit, or freeze session. Never invent mojibake or "best effort" plaintext.  
8. **Decoys never authenticate.** MPR, Mobius Trap, and P10 decoy ciphertexts MUST NOT be used as key material. Real verification rejects them.  
9. **Agent control only inside fences.** P0-P4 prose never runs as crypto opcodes. Untrusted bytes that *look* like fences remain data until a trusted boundary re-encodes a legal frame (ASCENT injection model).  
10. **Evolution is append-only.** Parameter evolution lands as P8 history records under constrained policy (NSGA-II-style multi-objective gates). No silent rewrite of the algorithm set.

### A.4 Profiles

| Profile | Role |
|---------|------|
| **AEGIR-7** | Greppable bootstrap only: ASCENT-7 labels, no ciphertext (ceremony headers, kids, public suite names). |
| **AEGIR-E** | Earth: full DCH + HBOP + agent gates + IMS optional. |
| **AEGIR-D** | Deep-space: AEGIR-E plus ASCENT-D outer ECC, mid-mission alg freeze, erase-on-fail. |
| **AEGIR-A** | Archive: AEGIR-E plus SLH-DSA long-term signatures, full DEF annex hashes, Merkle-sealed ledger. |
| **AEGIR-DEMO** | Implementer path: classical hybrid only (X25519 + AES-GCM-SIV or ChaCha20-Poly1305) + HBOP skeleton; **not** Mythos-grade. For vectors and CI. |

---

## B. Threat Model

### B.1 Assets

- Plaintext of agent streams, human text, multimodal logical payloads (after reassembly).  
- Long-term identity keys, session keys, ratchet state.  
- P8 registry integrity and freeze bindings.  
- Ceremony integrity (who held which ROLE / CAP).  
- Forensic ledger authenticity (IMS seals).  
- Physical / probe entropy commitments used by HBOP.

### B.2 Adversaries

| Class | Capability | AEGIR stance |
|-------|------------|--------------|
| **Classical** | Passive wiretap, active MITM, offline brute force, traffic analysis | Standard hybrid AEAD + FS/PCS ratchets |
| **Quantum** | CRQC-scale Shor on discrete log / factoring; Grover on symmetric | NIST ML-KEM / ML-DSA / SLH-DSA baseline; 256-bit symmetric targets |
| **Mythos-class** | Autonomous cryptanalysis inventing lattice automorphisms, Mobius-style algebraic bridges, chained 0-days in TLS/AES-GCM/SSH stacks; ~$100k+ semi-autonomous attack families | Dual hardness + outer IT pad + manifold poisoning + no single-family dependence |
| **Kimi-class** | Open-weight MoE, 1M context, fine-tune on traces, strip safeguards, unmonitored agent harnesses, long-context protocol reconstruction | ROLE/CAP consensus, CRITICAL hard-fault, polymorphic constrained evolution, sealed ledgers, injection model |
| **Generic LLM** | Pattern reconstruction from training data, side-channel assist, implementation suggestion for attackers | Spec does not hide behind obscurity; hardness is in keys + hybrid + pad + ops discipline |
| **Physical / SCA** | Power, EM, cache, timing, fault injection | Constant-time reference goals; erase-on-fail; limited claim without platform proof |
| **50-100 year horizon** | New AI cryptanalysis, registry growth, deep-space latency, frozen missions | Append-only registry, D freeze, archive signatures, outer pad from history |

### B.3 Explicit Mythos-class attack surface (2026 demonstrated class)

1. **Lattice automorphism discovery** reducing claimed hardness (HAWK-256 class event: nontrivial automorphism, scheme withdrawn).  
2. **Novel algebraic bridges** (Mobius Bridge class: large speedups on reduced-round AES-class analysis).  
3. **Meet-in-the-middle fingerprints** across protocol layers.  
4. **Differential / linear improvements** found by search rather than human insight.  
5. **Agentic custom-tool attacks** chaining library bugs, not only pure math.

### B.4 Explicit Kimi-class attack surface

1. Long-context statistical and structural analysis of the *protocol text and traces*.  
2. Fine-tuning attack models on captured handshake and AEAD traffic.  
3. Unmonitored exploit chaining against reference implementations.  
4. Injection into key-exchange or implementation logic via tool/agent channels.  
5. Social / ROLE spoofing inside multi-agent systems.

### B.5 Out of scope (honest limits)

- Compromised endpoint with full RAM dump of live pad material and keys.  
- Malicious RNG with total entropy failure *and* broken ceremony attestation.  
- Political coercion of all parties holding CAP shares.  
- Side-channel resistance is a **goal** for reference code; formal SCA proofs are platform-specific and not claimed complete here.  
- AEGIR does not claim "unbreakable forever." It claims **layered containment**: algebraic breaks do not freely yield plaintext under sealed profiles, and registry/ops discipline prevents silent degradation.

### B.6 Deep-space and freeze

High-latency links may freeze the allowed algorithm set into a content-addressed DEF snapshot. Receivers MUST NOT accept alg IDs outside the freeze without pre-authorized VERSION_BUMP. Outer P9 parity failure hard-erases the unit (ASCENT-D law). Crypto and media ride HE=1: no opportunistic recompress of ciphertext.

---

## C. Core Primitives and Hybrid Construction

### C.1 Named techniques (AEGIR inventions)

| Acronym | Full name | Role |
|---------|-----------|------|
| **DCH** | Dual-Core Hybrid | Classical + PQ, AND composition for KEM and key schedule |
| **HBOP** | History-Bound Outer Pad | Information-theoretic containment from P8 roots + physical entropy |
| **SCC** | Sparse Combinatorial Core | Expander-based key schedule; not lattice-only |
| **MPR** | Manifold Poisoning Register | Public decoy algebraic structure; never key material |
| **MT** | Mobius Trap | Planted bridge-like decoys that attract gradient/attention search |
| **AQ** | Automorphism Quarantine | Lattice schemes never solo; diversity of hardness families |
| **ACG** | Agent Consensus Gate | ROLE/CAP/HANDOFF consensus for critical ops |
| **CHFD** | Critical Hard-Fault Discipline | Unknown CRITICAL ops/algs hard-fault in sealed sessions |
| **IMS** | Immune Merkle Seal | Ghost Continuum continuous integrity + sealed forensics |
| **NSDR** | No Silent Downgrade Registry | Append-only P8; reject/skip never weaken |
| **DPC** | Decoy Plane Ciphertext | P10+ fake envelopes for pattern matchers |
| **DSR** | Double-core Session Ratchet | FS + PCS with dual-core binding |

### C.2 Baseline primitives (grounded, not novel)

These are the **known hardness** anchors. Novel AEGIR layers compose them; they do not replace them with snake-oil.

| Primitive | Standard / construction | Use in AEGIR |
|-----------|-------------------------|--------------|
| ML-KEM-768 / 1024 | NIST FIPS 203 | PQ KEM core |
| ML-DSA-65 / 87 | NIST FIPS 204 | PQ signatures |
| SLH-DSA-128f / 192f | NIST FIPS 205 | Long-term / archive signatures |
| X25519 | RFC 7748 | Classical KEM core (DCH) |
| Ed25519 | RFC 8032 | Classical signatures (hybrid) |
| AES-256-GCM-SIV | RFC 8452 | Primary bulk AEAD (nonce-misuse resistant) |
| ChaCha20-Poly1305 | RFC 8439 | Alternate bulk AEAD |
| HKDF-SHA-512 | RFC 5869 | KDF for DCH, HBOP, SCC |
| SHA-256 / SHA-512 / BLAKE3 | NIST / community | P6 hashes, freeze binding, IMS |
| HMAC-SHA-512 | FIPS 198-1 | MAC where AEAD not used |

**Reduction posture (honest):**

- **Confidentiality of AEAD layer** reduces to AEAD security under chosen-ciphertext (standard game) *and* secrecy of the AEAD key.  
- **AEAD key** is derived from DCH: adversary must break **both** ML-KEM *and* X25519 (AND composition) *or* the HKDF domain separation must fail.  
- **HBOP** provides Shannon-style containment for the outer layer when pad material is one-time (or ratcheted with high entropy) and unknown to the adversary:  
  `C_outer = C_aead XOR Pad`, with `|Pad| = |C_aead|` from high-entropy KDF output expanded via a stream keyed by pad material. If pad is secret and uniform, `C_outer` alone leaks no information about `C_aead` (and thus plaintext) beyond length.  
- **Mythos lattice automorphism** against ML-KEM alone does **not** recover the DCH shared secret without also breaking X25519 (or the classical core in use).  
- **Mobius-style AES attacks** that accelerate reduced-round analysis do not apply to full-round AES-256-GCM-SIV as standardized; AEGIR still refuses AES-only profiles for sealed missions and keeps HBOP outside.  
- **SCC** adds non-lattice structure so a pure lattice breakthrough does not linearize the entire key schedule.

### C.3 Dual-Core Hybrid (DCH) - key agreement

```
Inputs:
  pk_pq, sk_pq     # ML-KEM
  pk_cl, sk_cl     # X25519
  context          # suite_id || freeze_hash || session_id || role_chain_hash

Encaps (sender):
  (ct_pq, ss_pq) <- ML-KEM.Encaps(pk_pq)
  (ct_cl, ss_cl) <- X25519.Encaps(pk_cl)   # ephemeral * peer static or ephemeral-ephemeral per mode
  ss_raw = ss_pq || ss_cl
  ss = HKDF-SHA-512(
         ikm  = ss_raw,
         salt = freeze_hash,
         info = "AEGIR-DCH-KEM-v1" || context,
         L    = 64
       )
  Output: (ct_pq || ct_cl, ss)

Decaps (receiver):
  ss_pq <- ML-KEM.Decaps(sk_pq, ct_pq)
  ss_cl <- X25519.Decaps(sk_cl, ct_cl)
  same HKDF
  # If either core fails, abort. No single-core fallback.
```

**Modes:**

| Mode | Classical | PQ | FS | Notes |
|------|-----------|----|----|-------|
| DCH-ES | Ephemeral X25519 + static ML-KEM | yes | yes for CL | Earth interactive |
| DCH-EE | Ephemeral-ephemeral both | yes | yes | Preferred interactive |
| DCH-SS | Static-static (rare) | yes | no | Requires outer ratchet; discouraged |
| DCH-DEMO | X25519 only | no | yes | AEGIR-DEMO only |

### C.4 Sparse Combinatorial Core (SCC)

After DCH produces `ss` (64 bytes):

```
seed = HKDF(ss, salt=session_id, info="AEGIR-SCC-SEED-v1", L=32)
# Public expander: fixed Ramanujan / LPS-style graph parameters in registry (not secret)
# Walk length W=128 (suite-1), steps derived from seed via SHA-512 counter mode
walk = ExpanderWalk(public_graph_params, seed, W)
k_sched = HKDF(walk_transcript_hash || ss, info="AEGIR-SCC-SCHED-v1", L=96)
k_aead  = k_sched[0:32]
k_mac   = k_sched[32:64]   # optional separate MAC key
k_ratchet = k_sched[64:96]
```

**Hardness argument:** Recovering `k_aead` requires `ss` (DCH) *or* inverting the expander walk transcript binding without seed. The walk is not a lattice problem. Automorphisms of a lattice scheme do not map onto the public expander parameters.

### C.5 History-Bound Outer Pad (HBOP)

```
H_root = MerkleRoot(P8 history records accepted for this freeze)
         # or SHA-512 chain of (parent-hash || delta-hash) as in ASCENT history tuples
E_phys = physical_entropy_commitment   # 32+ bytes; sealed at ceremony; not on wire in clear as raw secret
         # deep space: probe TRNG + ground-sealed seed split; see E.4
session = session_id || message_counter

pad_key = HKDF-SHA-512(
            ikm  = H_root || E_phys || ss[0:32],  # binds pad to session secrets partially
            salt = freeze_hash,
            info = "AEGIR-HBOP-v1" || session,
            L    = 32
          )
Pad = AES-256-CTR(pad_key, nonce=HBOP_DOMAIN || msg_counter, len=|C_aead|)
      # CTR here is a pad expander, not the confidentiality AEAD
C_outer = C_aead XOR Pad
```

**Containment claim:** An adversary who recovers `k_aead` via algebraic cryptanalysis of ML-KEM / AES still needs `H_root` integrity *and* `E_phys` *and* (for this binding) partial `ss` material as specified. Mission profiles may strengthen to **pure one-time pad** when `|E_phys|` supplies full message entropy (rare; deep-space pre-shared pad vaults). Default Earth profile uses HBOP as a **second independent layer**, not a claim of perfect secrecy unless entropy budget is proven.

**Important:** HBOP keys are **never** derived from MPR decoy material.

### C.6 Bulk AEAD

```
AAD = suite_id || freeze_hash || kid || alg_list || role_chain_hash || mm_hash_optional
C_aead || tag = AES-256-GCM-SIV.Seal(k_aead, nonce, plaintext, AAD)
# then HBOP:
C_wire_body = C_outer || tag   # tag may ride outside pad or inside per suite flag TAG_OUTSIDE_PAD=1 (default)
```

Default suite-1: **tag outside pad** so authentication fails closed before pad inversion games.

### C.7 Manifold Poisoning Register (MPR) and Mobius Trap (MT)

**Purpose:** Deliberately plant near-symmetries and bridge-like algebraic decorations that transformer attention / gradient-guided search latches onto, producing expensive false paths. True hardness remains in DCH + SCC + HBOP.

**Rules (normative):**

1. MPR blobs are **public** and marked `alg = 0x0109 AEGIR-MPR-V1` or private-plane DPC.  
2. Implementations MUST zeroize and refuse any API that treats MPR as IKM, key, or pad.  
3. Verification of real envelopes ignores MPR except for optional "decoy present" telemetry.  
4. MT structures are generated by a public PRG from a **non-secret** domain string `"AEGIR-MT-DECOY-v1"` so they are reproducible and clearly non-secret.  
5. Security MUST NOT depend on attackers "not noticing" MPR. MPR is budget-burning camouflage, not a secret.

**Concrete countermeasures to Mythos-class events:**

| Mythos-class event | AEGIR countermeasure |
|--------------------|----------------------|
| Lattice automorphism halves PQ core | AQ: lattice never solo; DCH AND with classical; HBOP containment |
| Mobius Bridge accelerates reduced-round AES search | Full-round AES-256-GCM-SIV; no reduced-round modes; MT decoys attract similar search; hybrid + HBOP |
| Meet-in-the-middle fingerprints | Domain-separated HKDF labels; AAD binds freeze + role chain; large nonces |
| Agentic 0-day chains in stacks | Prefer memory-safe ref path; CHFD; IMS freeze; minimal dependency surface |
| Training-distribution reconstruction of "similar protocols" | Greppable honesty; secrets not in weights; pad + keys OOB |

### C.8 Signatures and transcript binding

Hybrid signature (suite-1):

```
sig = ML-DSA-65.Sign(sk_pq, transcript) || Ed25519.Sign(sk_cl, transcript)
verify = both valid  # AND
transcript = SHA-512("AEGIR-TRANSCRIPT-v1" || freeze_hash || msgs...)
```

Archive profile may require SLH-DSA alone or hybrid with SLH-DSA for long-term.

### C.9 Forward secrecy and post-compromise security

**DSR (Double-core Session Ratchet):**

- Symmetric ratchet steps use `k_ratchet` from SCC.  
- DH ratchet steps use fresh DCH-EE whenever possible.  
- After compromise of a single message key, future keys require new DCH material.  
- PCS: after compromise of session state, a successful DCH-EE rekey restores secrecy for subsequent messages **if** HBOP `E_phys` epoch also advances (mission option `HBOP_EPOCH_ON_REKEY=1`).

### C.10 AEGIR algorithm registry seeds (append into P8; never reuse ids)

ASCENT bootstrap PQ ids `0x0001-0x0006` remain as in SPEC.md. AEGIR **suite and container** ids:

| alg:u16be | Name | Role |
|-----------|------|------|
| `0x0100` | AEGIR-SUITE-1 | Suite descriptor / versioned profile |
| `0x0101` | AEGIR-DCH-KEM-768 | Hybrid KEM container (ML-KEM-768 + X25519) |
| `0x0102` | AEGIR-DCH-KEM-1024 | Hybrid KEM high |
| `0x0103` | AEGIR-AEAD-AES256-GCMSIV | Bulk AEAD |
| `0x0104` | AEGIR-AEAD-CHACHA20POLY | Bulk AEAD alternate |
| `0x0105` | AEGIR-HBOP-SHA512 | Outer pad KDF family |
| `0x0106` | AEGIR-SIG-HYBRID-65 | ML-DSA-65 + Ed25519 |
| `0x0107` | AEGIR-SIG-SLH-128f | Archive signature |
| `0x0108` | AEGIR-DSR-STATE | Ratchet state blob (encrypted) |
| `0x0109` | AEGIR-MPR-V1 | Manifold poison decoy (non-key) |
| `0x010A` | AEGIR-IMS-SEAL | Immune Merkle seal record |
| `0x010B` | AEGIR-DEMO-X25519-GCM | Demo classical path only |
| `0x010C-0x01FF` | AEGIR reserved | future suite cores |
| `0x0200-0x7FFF` | registered extensions | public process |
| `0x8000-0xFFFF` | private | profile-declared; cannot redefine P0-P2 |

---

## D. ASCENT Wire Integration

### D.1 Planes used

| Plane | AEGIR use |
|-------|-----------|
| **P0** | Greppable headers (`ASCENT/1.0`, `AEGIR/1.0`), kids as ASCII when possible, human labels |
| **P1** | `0x9A/0x9B` agent, `0x9C` crypto, `0x9D` multimodal |
| **P2** | `0xC0` DEF, `0xC1` AGENT_OP |
| **P5** | Ceremony: ROLE, CAP, HANDOFF, SAFETY, THINK (opaque), STOP |
| **P6** | Content hashes of plaintext, media, freeze slices |
| **P7** | All sealed material (KEM, AEAD, HBOP meta, seals, decoys) |
| **P8** | Suite registry, history, freeze, VERSION_BUMP policy |
| **P9** | Outer ECC under AEGIR-D |
| **P10+** | DPC decoys only; cannot redefine P0-P2 |

### D.2 Frame formats

#### D.2.1 P7 CRYPTO (host grammar - ASCENT normative)

```
0x9C 0x4B <alg:u16be> <kid-len:u8> <kid> <nonce-len:u8> <nonce> <ct-len:u32be> <ct>
```

AEGIR packs **typed bodies** inside `ct` when `alg` is an AEGIR container id. Unknown alg: do not decrypt; skip-by-length if lengths valid (Earth). Sealed sessions with CHFD: hard-fault instead of skip for critical channel.

#### D.2.2 AEGIR sealed message body (`alg = 0x0100` suite envelope, preferred single frame)

When using a single suite envelope, `ct` layout:

```
struct AegirSuiteEnvelopeV1 {
  u8  version;           // 1
  u8  flags;             // bit0 TAG_OUTSIDE_PAD=1, bit1 HBOP_PRESENT=1, bit2 IMS_PRESENT, bit3 MPR_ATTACHED
  u16 suite_id;          // 0x0100
  u16 kem_alg;           // 0x0101 or 0x0102
  u16 aead_alg;          // 0x0103 or 0x0104
  u8  freeze_hash_alg;   // 1=sha-256
  u8  freeze_hash[32];
  u8  aad_hash[32];      // SHA-256(AAD)
  u16 kem_ct_len;
  u8  kem_ct[kem_ct_len]; // ct_pq || ct_cl
  u8  aead_nonce_len;    // typically 12 or 16
  u8  aead_nonce[aead_nonce_len];
  u32 aead_ct_len;
  u8  aead_ct[aead_ct_len]; // ciphertext || tag  OR ciphertext only if TAG_OUTSIDE
  u16 tag_len;           // 16 when TAG_OUTSIDE_PAD
  u8  tag[tag_len];
  u16 hbop_meta_len;     // 0 if no HBOP
  u8  hbop_meta[hbop_meta_len]; // see below
  u16 ims_len;           // 0 if none
  u8  ims[ims_len];
}
```

All multi-byte integers **big-endian**.

#### D.2.3 HBOP meta

```
struct HbopMetaV1 {
  u8  version;        // 1
  u8  hash_alg;       // 2 = sha-512 for H_root display
  u8  h_root[32];     // truncated SHA-512/256 of history root (commitment)
  u8  e_phys_commit[32]; // SHA-256(E_phys) - commitment only
  u32 msg_counter;
  u8  domain[8];      // ASCII "HBOP0001"
}
```

Raw `E_phys` never appears here.

#### D.2.4 Split frames (optional)

Implementations MAY emit separate P7 frames:

1. `alg=0x0101` KEM container only  
2. `alg=0x0103` AEAD body only  
3. `alg=0x0105` HBOP meta only  
4. `alg=0x010A` IMS seal  

Order on the wire SHOULD be KEM -> AEAD -> HBOP -> IMS. Receivers accept any order if lengths parse; sealed profiles SHOULD require canonical order.

#### D.2.5 Agent ceremony frames (P5)

ASCENT agent grammar:

```
0x9A 0xC1 <ver:u8> <opcode:u16be> <flags:u8> <len:u16be> <args> 0x9B
```

Opcodes used by AEGIR:

| opcode | name | AEGIR use |
|--------|------|-----------|
| 1 | STOP | End ceremony / sealed session |
| 2 | ROLE | Attest role: `seal`, `sender`, `receiver`, `auditor`, `probe` |
| 3 | TOOL | Optional tool attestation (name only; no secrets) |
| 4 | THINK | Opaque reasoning; MUST NOT carry keys; strip on shared logs |
| 5 | HANDOFF | Transfer seal authority; args include from/to role digests |
| 6 | CAP | Capability grant/revoke: `encrypt`, `decrypt`, `rekey`, `freeze`, `export` |
| 7 | SAFETY | Quarantine untrusted material; mark stream untrusted |

**CRITICAL flag** (flags bit0 = 1): unknown opcode or malformed args => hard-fault (CHFD).  
Nested agent frames forbidden in ASCENT v1 (parent law).

#### D.2.6 Multimodal integrity (P6)

```
0x9D 0x4D <kind:u8> <codec:u16be> <flags:u8> <hash-alg:u8> <hash:N> <len:u64be> [body]
```

AEGIR binds optional `plaintext_commit = SHA-256(plaintext)` as a P6 REF or INLINE of empty body with EXTERNAL flag and hash only, or includes the commit in AAD only (preferred: AAD only, no plaintext leak).

#### D.2.7 DEF / freeze (P8)

Greppable bootstrap remains:

```
ASCENT/1.0\n
AEGIR/1.0\n
0xC0 <schema:u8> <len:u32be> <DEF body>
```

DEF KERNEL (`schema=0x01`) MUST list AEGIR alg ids in use. HISTORY (`0x03`) appends records with parent/delta hashes. Freeze binds `freeze_hash = SHA-256(canonical_freeze_slice)`.

### D.3 Encrypted "Hello, Universe" unit (worked example)

Profile: **AEGIR-E** with **AEGIR-DEMO** cores for a concrete, reproducible vector (classical hybrid). Full DCH-768 replaces `kem_ct` with ML-KEM-768 ct || X25519 ct of the same structural layout.

#### D.3.1 Readable annotation

```
ASCENT/1.0\n                              # P0 parent magic
AEGIR/1.0\n                               # P0 suite magic (greppable)
# Agent: ROLE=sender
9A C1 01 00 02 00 00 07 06 73 65 6E 64 65 72 9B
# Agent: CAP=encrypt (name_len + "encrypt")
9A C1 01 00 06 00 00 08 07 65 6E 63 72 79 70 74 9B
# P7 suite envelope alg=0x0100 (demo body uses 0x010B path inside flags)
9C 4B 01 00 <kid> <nonce> <ct suite envelope>
# Optional MPR decoy (alg=0x0109) - non-secret
9C 4B 01 09 ...
```

Sacred P0 bytes `ASCENT/1.0` and `AEGIR/1.0` remain greppable. The plaintext `Hello, Universe.\n` does **not** appear in the clear after the ceremony labels.

#### D.3.2 Deterministic demo test vector (AEGIR-DEMO)

Reference code: `ref/aegir_sketch.py`. Fixed demo secrets are **for vectors only**, never for production.

```
suite_magic     = "ASCENT/1.0\nAEGIR/1.0\n"
plaintext       = "Hello, Universe.\n"
kid             = "demo-kid-1"
freeze_hash     = SHA-256("AEGIR-DEMO-FREEZE-v1")
E_phys          = 32 x 0x42   # demo only
# X25519 static demo keypair from seed SHA-256("AEGIR-DEMO-X25519-SEED")
# AEAD: AES-256-GCM (demo; suite-1 prefers GCM-SIV when available)
# HBOP applied with msg_counter=1
```

**Measured demo stream (2026-07-29 self-test; nonce/ephemeral vary per run):**

| Field | Value |
|-------|-------|
| wire_len | 472 bytes (DEMO golden with MPR + IMS; random DEMO without IMS ~368 B) |
| freeze_hash | `bf51cf956d1b2b2abb2c17e11bb82827c96c644672111711fc2238c1adee4bb7` |
| hex_prefix (fixed ceremony) | `415343454e542f312e300a41454749522f312e300a9ac10100020000070673656e6465729b9ac101000600000807656e...` |

Fixed structure prefix:

```
0000: 41 53 43 45 4E 54 2F 31 2E 30 0A 41 45 47 49 52   |ASCENT/1.0.AEGIR|
0010: 2F 31 2E 30 0A 9A C1 01 00 02 00 00 07 06 73 65   |/1.0..........se|
0020: 6E 64 65 72 9B 9A C1 01 00 06 00 00 08 07 65 6E   |nder..........en|
0030: 63 72 79 70 74 9B 9C 4B 01 0B ...                 |crypt..K...|
```

Note `0x4B` = ASCII `K` (ASCENT crypto mark). Greppers find `ASCENT/1.0`, `AEGIR/1.0`, ROLE/CAP names, and kid `demo-kid-1`. Ciphertext body is high-entropy; no plaintext greeting after the ceremony.

Run:

```powershell
cd $env:USERPROFILE\Projects\next-ascii
py -3 ref/aegir_sketch.py --self-test
```

Expect: `PASS` - encrypt -> decrypt of `Hello, Universe.\n`, P0 magic true, no plaintext leak.

### D.4 Deep-space wrap (AEGIR-D)

Logical AEGIR stream becomes payload of ASCENT-D P9:

```
sync = D5 E5 C0 DE
profile + Reed-Solomon RS(255,223) default (or stronger)
interleave; hard-erase unit on parity/CRC failure
```

HE=1 when any P7 present: no compress of ciphertext. Prefer P6 REF for bulk media; encrypt small control plaintext in AEGIR envelopes.

---

## E. Key Lifecycle, Ceremony, and Protocols

### E.1 Key types

| Key | Storage | Wire |
|-----|---------|------|
| Identity PQ (ML-DSA / SLH-DSA) | OOB HSM / sealed vault | public only |
| Identity classical (Ed25519) | OOB | public only |
| KEM static PQ (ML-KEM) | OOB | public only |
| KEM classical (X25519) | OOB | public only |
| Session / ratchet | memory, sealed | encrypted in `0x0108` if needed |
| E_phys / pad vault | split, mission sealed | commitment only |
| MPR | public | public decoy |

### E.2 Ceremony (two-party interactive)

```
1. P0: ASCENT/1.0 + AEGIR/1.0
2. Optional DEF KERNEL + HISTORY pin -> freeze_hash
3. ROLE=sender / ROLE=receiver (CRITICAL optional)
4. CAP grants: encrypt/decrypt/rekey as needed (CRITICAL for high assurance)
5. Exchange public keys (OOB or signed P6 INLINE of SPKI-like blobs - never private keys)
6. DCH encaps/decaps -> ss -> SCC -> k_aead
7. Seal first message with AEAD + HBOP
8. Optional IMS seal of ceremony transcript
9. STOP or continue ratchet
```

### E.3 Multi-party (agent-fenced)

Critical operations (`rekey`, `freeze`, `export`):

1. ROLE attestations from all required parties.  
2. CAP consensus: each party emits CAP grant for the op; threshold policy in DEF (e.g. 2-of-3).  
3. HANDOFF when seal authority moves (from probe to ground, or agent to agent).  
4. SAFETY marks any untrusted third-party content; decrypt path refuses SAFETY-quarantined bodies for key material.  
5. THINK remains opaque and is stripped from shared forensic logs (parent ASCENT law).

### E.4 Physical / probe entropy (E_phys)

| Environment | Source | Seal |
|-------------|--------|------|
| Earth | OS CSPRNG + optional hardware TRNG | local vault |
| Deep space | Onboard TRNG + pre-launch split pad | ground holds half commitment; probe holds half |
| Archive | Offline ceremony dice/HSM | dual-control |

`e_phys_commit = SHA-256(E_phys)` may appear in HBOP meta. Raw `E_phys` rotation is a ceremony event logged under IMS.

### E.5 Rekey and compromise

1. Emit ROLE + CAP=rekey (CRITICAL).  
2. Fresh DCH-EE.  
3. Advance HBOP epoch if `HBOP_EPOCH_ON_REKEY=1`.  
4. Seal IMS record of rekey transcript hash.  
5. Old message keys erased; old pad epoch discarded.

### E.6 Export and audit

Export of plaintext requires CAP=export. Auditors hold ROLE=auditor with verify-only CAP (no decrypt) unless dual-control grants temporary decrypt. THINK frames never exported to shared channels.

---

## F. Security Arguments and AI-Resistance Analysis

### F.1 Classical / quantum

- Wiretap: AEAD + HBOP.  
- MITM: hybrid signatures on transcripts + freeze bind; CAP on identity change.  
- CRQC: ML-KEM / ML-DSA / SLH-DSA; classical cores alone insufficient (AND).  
- Nonce misuse: GCM-SIV preferred.  
- Downgrade: NSDR + freeze; no OR fallback.

### F.2 Simulated Mythos red-team (outcomes)

| Attack | Simulated outcome under AEGIR-E sealed |
|--------|----------------------------------------|
| Autonomous discovery of ML-KEM automorphism reducing PQ core | Classical core + HBOP still required; session does not silent-fail to PQ-only; IMS alerts on anomalous decaps timing optional |
| Mobius-style bridge search on AEAD | Full-round primitive; MT decoys consume search; HBOP still outside; no reduced-round suite id registered |
| Meet-in-the-middle across KEM and AEAD | HKDF domain separation + AAD freeze bind; requires joint break |
| Agentic exploit of reference Python | Threat is real for *implementations*; CHFD + minimal deps + IMS freeze; claim is protocol containment, not bug-free code forever |
| Training-set protocol clone | Secrets not in spec; keys OOB; pad entropy OOB |

**Why automorphisms fail to fully win:** AQ + DCH AND + HBOP.  
**Why Mobius-style bridges fail to fully win:** no reduced-round modes; dual layer; decoy budget.  
**Why "spec-only" breaks fail:** security is not obscurity; resistance is compositional.

### F.3 Simulated Kimi red-team (outcomes)

| Attack | Outcome |
|--------|---------|
| 1M-context structural analysis of this SPEC | Learns public structure (intended); does not learn keys, E_phys, or private history roots |
| Fine-tune on handshake traces | Sees public KEM cts and outer ciphertext; still needs secrets; distributional IMS can flag anomalous online queries in operator deployments |
| Unmonitored exploit chaining | Against software: always a risk; sealed sessions hard-fault unknowns; recommend memory-safe production impl |
| Injection into key-exchange via agent tools | SAFETY quarantine + injection model (data until trusted re-encode) + CAP consensus |
| ROLE spoofing | Signature-bound ROLE + CAP; unsigned ROLE is advisory only in sealed profiles |

### F.4 What we refuse to claim

- "LLM-proof" as a mathematical theorem about all future models.  
- Perfect secrecy without entropy budget.  
- Side-channel freedom without platform proof.  
- That decoys stop a perfect algebraic break of **all** cores plus pad theft.

We claim: **layered, fail-closed, ASCENT-native encryption with explicit countermeasures to the 2026 Mythos/Kimi attack class**, suitable as a fifty-year engineering baseline if registries freeze honestly and keys remain OOB.

---

## G. Reference Implementation Sketch

See `ref/aegir_sketch.py` for executable AEGIR-DEMO path (stdlib + `cryptography` when present).

### G.1 Zero-dependency pseudocode (encrypt)

```
function aegir_encrypt(plaintext, pk_peer, sk_self, kid, freeze_hash, E_phys, msg_counter, role_chain_hash):
  context = suite_id || freeze_hash || session_id || role_chain_hash
  (kem_ct, ss) = DCH_Encaps(pk_peer, context)   # or DEMO X25519 only
  (k_aead, k_mac, k_ratchet) = SCC_Schedule(ss, session_id)
  AAD = suite_id || freeze_hash || kid || role_chain_hash
  aad_hash = SHA-256(AAD)
  nonce = CSPRNG(12)
  C_aead, tag = AES_256_GCM_SIV_Seal(k_aead, nonce, plaintext, AAD)
  H_root = HistoryRoot()  # from accepted P8
  pad_key = HKDF_SHA512(H_root || E_phys || ss[0:32], salt=freeze_hash,
                        info="AEGIR-HBOP-v1" || session_id || msg_counter, L=32)
  Pad = AES_CTR(pad_key, "HBOP0001" || msg_counter, len(C_aead))
  C_outer = xor(C_aead, Pad)
  body = SuiteEnvelopeV1(..., kem_ct, nonce, C_outer, tag, HbopMeta(...))
  return P7_Frame(alg=0x0100, kid=kid, nonce=empty_or_outer, ct=body)
```

### G.2 Decrypt

```
function aegir_decrypt(frame, sk_self, pk_peer, E_phys, history):
  parse P7; require alg in freeze set
  open SuiteEnvelopeV1
  ss = DCH_Decaps(sk_self, kem_ct, context)  # abort if either core fails
  (k_aead, ...) = SCC_Schedule(ss, session_id)
  verify HbopMeta commitments against history and E_phys
  Pad = AES_CTR(...)
  C_aead = xor(C_outer, Pad)
  plaintext = AES_256_GCM_SIV_Open(k_aead, nonce, C_aead, tag, AAD)
  # hard-fault on any failure; no partial plaintext
  return plaintext
```

### G.3 Greppable stream builder

```
stream  = b"ASCENT/1.0\nAEGIR/1.0\n"
stream += agent_frame(ROLE, "sender")
stream += agent_frame(CAP, "encrypt")
stream += p7_frame(...)
# optional: agent_frame(STOP)
```

---

## H. Evolution, Freeze, and Ghost Continuum Integration

### H.1 Append-only evolution

Parameter changes (suite ids, graph params, walk length, AEAD choice) land only as:

1. P8 HISTORY record with parent-hash, delta-hash, semver, date.  
2. Optional hybrid signature over the DEF delta.  
3. Receivers update only under upgrade policy; default pin: first DEF wins.

### H.2 NSGA-II-style constrained evolution (Ghost Continuum)

When AEGIR is coupled to a live immune fabric (Ghost Continuum OMEGA lineage):

**Objectives (example vector, minimize risk / maximize resilience):**

1. Estimated cryptanalytic residual risk (human + AI red-team scores).  
2. Wire overhead (bytes per message).  
3. Latency on target profile (E vs D).  
4. Implementation complexity / attack surface.  
5. Novelty (avoid monoculture of suite parameters).

**Constraints (hard):**

- Never remove sacred P0 law.  
- Never allow OR-only hybrid in sealed profiles.  
- Never register reduced-round or toy AEAD.  
- Never shrink HBOP commitments below suite minimums.  
- Evolution candidates are genomes of **public parameters only**; private keys are not evolved by the GA.

Winning genomes become P8 proposals, not silent runtime mutation of crypto cores.

### H.3 Immune Merkle Seal (IMS)

```
state_root = MerkleRoot(config || suite || freeze_hash || last_n_transcript_hashes)
on anomaly (CAP fail, unknown CRITICAL, decaps anomaly policy, integrity fail):
  seal_record = { time, state_root, event_hash, action: FREEZE|ERASE|QUARANTINE }
  emit P7 alg=0x010A with signature
  prefer FREEZE session over silent continue
```

Holographic / local-first monitoring is an **operator deployment** concern (Ghost Continuum Command Nexus). AEGIR specifies the **wire-visible seal** and fail-closed actions.

### H.4 ASCENT-D freeze

```
freeze_slice = canonical encoding of { allowed alg ids, suite_id, SCC params, HBOP policy }
freeze_hash = SHA-256(freeze_slice)
bind freeze_hash into every AAD and suite envelope
mid-cruise: reject alg not in freeze unless dual-DEF VERSION_BUMP pre-authorized
```

Silent algorithm substitution is non-conformant (parent SPEC + AEGIR NSDR).

### H.5 Polymorphic defense without breaking greppers

Allowed polymorphism:

- Optional MPR/DPC decoy frames.  
- Variable kid strings.  
- Optional THINK frames (stripped on shared logs).  
- Suite evolution via P8 (append-only).

Forbidden polymorphism:

- Remapping P0.  
- Silent alg change.  
- Nested agent frames (v1).  
- Using decoys as keys.

---

## I. Test Vectors, Migration Path, and Open Questions

### I.1 Test vectors

| Vector | Purpose |
|--------|---------|
| TV-DEMO-1 | AEGIR-DEMO Hello Universe round-trip (`aegir_sketch.py --self-test`) |
| TV-STRUCT-1 | Parse-only stream with P0 + ROLE + CAP + empty P7 skip |
| TV-FREEZE-1 | Reject alg not in freeze_hash set |
| TV-CHFD-1 | Unknown CRITICAL opcode hard-faults |
| TV-HBOP-1 | Wrong E_phys fails decrypt |
| TV-MPR-1 | MPR frame ignored for key schedule; decrypt still works |
| TV-D-1 | P9 parity fail erases unit (ASCENT-D harness) |

Full DCH-768 vectors SHOULD be added when liboqs / mlkem bindings are pinned in CI (not required for DEMO path).

### I.2 Migration path

| From | To AEGIR | Notes |
|------|----------|-------|
| TLS 1.3 hybrid (X25519MLKEM768) | Map shared secrets into DCH context; re-wrap in P7 | Different wire; gateway |
| Age / OpenPGP PQ drafts | Re-encrypt under AEGIR suite; keep signatures as P6 commits | One-shot migration |
| AES-GCM only archives | Re-seal with DCH+HBOP; keep old ciphertext as P6 REF historical | Dual-era readers |
| ASCENT streams without crypto | Add AEGIR ceremony + P7; keep P0 text until seal boundary | Non-breaking for greppers |

Migration MUST NOT silent-downgrade: old classical-only ciphertext remains labeled classical; sealed missions require suite-1+.

### I.3 Open questions

1. **Formal game-based proof** of AND hybrid + HBOP composition under a Mythos-capable ideal adversary model (new models needed; classical IND-CCA alone is incomplete for AI cryptanalysis claims).  
2. **Standard expander graph parameters** for SCC (which LPS/Ramanujan family, encoding on wire).  
3. **Threshold CAP** encoding in agent args (2-of-3 etc.) - currently policy-in-DEF.  
4. **Constant-time** goals for Python demo vs Rust/C production path.  
5. **HBOP pure-OTP mode** entropy accounting for multi-megabyte media.  
6. ~~Whether to register AEGIR suite ids into the public ASCENT PQ registry~~ **Done (2026-07-30):** registered block `0x0100-0x010B` in SPEC.md C.3.3.  
7. **Side-channel** lab results for DCH decaps on target MCUs (deep-space).  
8. **Interaction with THINK opacity** when auditors demand full forensic replay (policy tension).

### I.4 Compliance checklist (implementer)

- [ ] Sacred P0 preserved; greppable `ASCENT/1.0` / `AEGIR/1.0`  
- [ ] P7 frames only for sealed material; keys OOB  
- [ ] No OR fallback in sealed profiles  
- [ ] Freeze hash bound into AAD  
- [ ] HBOP meta commitments verified  
- [ ] MPR never used as IKM  
- [ ] CRITICAL unknown => hard-fault in sealed mode  
- [ ] ASCENT-D erase-on-fail when profile D  
- [ ] Test vectors pass  
- [ ] No em/en dashes in product copy (operator machine rule)

---

## Appendix J. Relationship to ASCENT and Ghost Continuum

AEGIR does not replace ASCENT. It **inhabits** ASCENT.  
Ghost Continuum does not replace AEGIR crypto cores. It **watches, seals, and evolves policy** around them under hard constraints.

```
ASCENT wire (sacred stairs)
   └── AEGIR envelopes (sealed rooms)
          └── Ghost Continuum immune fabric (watchers, seals, genomes)
```

Keep the stairs. Seal the rooms. Watch the walls.

---

## Appendix K. Document control

| Field | Value |
|-------|-------|
| Title | AEGIR 1.0 - ASCENT Encryption with Ghost-Immune Resilience |
| Parent | ASCENT SPEC 1.0 / 1.1 |
| Authors | Pitchfork-and-Torch design synthesis (agent-assisted) |
| Classification | Public design draft when shipped; no secrets in this file |
| Changelog | 1.0.0-draft 2026-07-29 initial complete design |

**End of AEGIR 1.0 design specification.**
