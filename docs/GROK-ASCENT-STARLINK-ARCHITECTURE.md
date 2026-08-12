# Grok over ASCENT over Starlink

**Title:** Resilient terminal Grok via ASCENT on Starlink (and beyond)  
**Status:** Research synthesis + implementable architecture (v0.2, SkyPulse)  
**Date:** 2026-08-12  
**Scope:** Public evidence only. Legal stock Starlink kit. No RF hacks.  
**Product hooks:** Pitchfork-and-Torch/ascent SPEC 1.0.0-rc1, `ascent-wire` 2.1.0, SkyPulse PATHHINT, live Wire Lab.

ASCII hyphens only in this document.

---

## Executive truth (read first)

Three layers people collapse into one slogan:

| Layer | What it actually is |
|-------|---------------------|
| **Starlink** | Last-mile IP (dish <-> LEO <-> optional ISL mesh <-> ground gateway <-> PoP <-> public Internet) |
| **ASCENT** | Wire encoding + agent session grammar + optional ASCENT-D outer ECC. Not a network. |
| **Grok** | Frontier-scale **cloud** inference at xAI (`api.x.ai` / Colossus-class terrestrial GPUs) |

**Achievable today:** When your fiber/cell dies but the public Internet and xAI still live, Starlink restores the pipe; ASCENT structures flaky sessions; a local model keeps a brain when the API is gone.

**Not achievable as a consumer product today:** Full cloud Grok while "worldwide terrestrial Internet is completely unavailable." That scenario almost certainly kills gateways, PoPs, and xAI DCs. ISLs do not host Grok.

**One sentence:** Starlink keeps you on the public Internet when *your* last mile dies; ASCENT keeps sessions and payloads honest when the link is ugly; SkyPulse PATHHINT gives CCA/apps a fail-closed freeze/capacity seed so LEO flaps waste fewer retransmits; only local models keep a brain when the public Internet (and therefore xAI) is actually gone.

**SkyPulse does not make Starlink faster at RF.** It improves **usable session bandwidth** and session continuity. Not a bare "bandwidth upgrade."

---

## 0. SkyPulse (PATHHINT) on Starlink IP

Priority for this architecture: **usable session bandwidth**, not PHY Mbps slogans.

| Piece | Role |
|-------|------|
| PATHHINT / SKYSTATE `0xC5` schema `0x01` | Compact hint: path_id, next_capacity (predicted sender bottleneck bits/s, not RF PHY), freeze_until, confidence, ttl; optional obstruction/elev |
| Fail-closed | CRC/short-RS fail, stale TTL, unknown version => erase; never apply a bad hint to CCA |
| ASCENT-E-LEO | Usage profile of E: light CRC or short RS(255,239) I=1 (not stacked); **no full P9 RS** on interactive IP |
| ASCENT-D | Keep for spool / deep-space / high-BER; RS(255,223) erase-on-fail |
| QUEUE | Daemon mode when obstruction or RTT flaps; CLOUD/EDGE still name the brain honestly |

LeoAware (OrbitStack) hybrid fuse: PATHHINT may seed freeze + next_capacity; Orb pathID still owns REPROBE when not suppressed; assist suppress ~2s / no hybrid util-MD; predictive pre-hop freeze is **growth freeze only** and must **never** gate `ep:loss_burst`. Absolute dual-gate remains a paid OrbitStack product fence. See `docs/SKYPULSE.md` and `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`.

Canonical lab unit (50 Mbps is a *hint*, not a dish measurement):

```
c5 01 00 1a 0e 00 00 00 00 00 00 00 42 02 fa f0 80 ...
```

Python: `encode_pathhint` / `canonical_pathhint_bytes` in `ref/ascent_codec.py`.


## 1. Research dossier

### 1.1 ASCENT mapping (from SPEC 1.0.0-rc1 + local codec)

| Plane | Role | Satellite / LLM use |
|-------|------|---------------------|
| **P0** | Sacred ASCII `byte < 0x80` forever | Greppable logs, prompts, shell-safe transcripts over any path |
| **P1** | Fixed control fences | Stream structure survives partial readers |
| **P5** | Agent frames `0x9A`..`0x9B` + `0xC1` opcodes | ROLE, TOOL, THINK, HANDOFF, CAP, SAFETY, STOP for Grok turns |
| **P6** | Multimodal `0x9D 0x4D` | Prefer **REF** over INLINE on flaky links; hash-bound assets |
| **P7** | Quantum-safe control `0x9C` | Session keys/kids; keys stay OOB |
| **P8** | DEF self-maps | Profile negotiation, ECC table, freeze mid-cruise |
| **P9 / ASCENT-D** | Outer sync `D5 E5 C0 DE` + **RS(255,223)** GF(256) | Erase-on-parity-fail; no mojibake agents; I=8 default |

**Profiles:** ASCENT-7 (identity ASCII) | ASCENT-E (Earth) | **ASCENT-E-LEO** (usage of E: PATHHINT, light integrity) | ASCENT-D (deep outer) | ASCENT-A (archive).

**Fail policy (D):** parity/CRC fail => **erase unit**. Never soft-fill corrupt TOOL/SAFETY.

**Sources:** local `SPEC.md` C.1-C.5, `ref/ascent_d.py`, `docs/AGENT-LOOP.md`. Confidence: **High** (normative product).

### 1.2 Starlink / SpaceX state of the art (public, mid-2026)

| Claim | Confidence | Implication |
|-------|------------|-------------|
| User path needs **some** Earth gateway + PoP for public Internet apps | High | No pure-space Grok for customers |
| Optical ISLs form a mesh; can route to distant gateways | High | Helps remote/ocean coverage; still needs exit |
| Typical land RTT ~25-60 ms; residential tens-hundreds Mbps down, ~10-40 Mbps up | High | Fine for chat tokens; budget uplink for large prompts |
| Dish local gRPC `192.168.100.1:9200` (community RE; status/history) | High | Diagnostics only; not official residential API |
| Enterprise Management/Telemetry APIs exist for fleets | High | Ops, not inference |
| Direct-to-Cell: SMS/select apps; not full HTTPS agent sessions | High | Emergency C2 only |
| V3 / orbital AI / Marslink: roadmap or early deploy, not customer Grok path | Med | Phase 3+ speculation |
| Power: Standard dish tens of watts average; needs sky + account | High | UPS is part of the system |

**Primary anchors:** starlink.com/technology, starlink V3 updates, performance legal docs, RIPE Labs Starlink measurements, sparky8512/starlink-grpc-tools, T-Mobile T-Satellite, xAI `api.x.ai`.

### 1.3 DTN comparison

| Dimension | DTN (BPv7 + CLA + optional LTP) | ASCENT-D |
|-----------|----------------------------------|----------|
| Problem | Intermittent multi-hop store-forward, long delay | Frame integrity + erase-on-fail for agent wire |
| Layer | Overlay network | Application / codec |
| Starlink chat default | Poor (IP already exists) | Good with QUIC/TCP |
| Deep space later | Required for non-IP contacts | Complementary E2E integrity |

**Stacking decision:**

- **Today Starlink IP:** ASCENT (+ optional ASCENT-D) over **QUIC/TCP/HTTPS**. No BP daemon.  
- **True deep space later:** ASCENT as **bundle ADU** (A) + ASCENT-D E2E (C) + LTP red-part / optional ECLSA + CCSDS link coding.  
- **Reject:** ASCENT as a custom convergence-layer codec (breaks ION/HDTN/uD3TN interop).

**FEC note:** RS(255,223) rate ~0.875 matches classical CCSDS outer RS (t=16 errors / up to 32 erasures). ASCENT-D does **not** replace TM LDPC/turbo or LTP ARQ. On **Starlink IP**, do not stack P9 RS on top of PHY+TLS (double-FEC tax). Soft-decision LDPC/turbo beat hard RS on AWGN; RS + erase-on-fail wins for fail-closed agent safety on short **spool / deep-space** ADUs. PATHHINT optional IEEE CRC-32 is integrity, not FEC.

**Sources:** RFC 9171 BPv7, RFC 5326 LTP, CCSDS 131.0-B TM coding, ION/HDTN/uD3TN public trees. Confidence: High for standards; Medium for ECLSA packaging.

### 1.4 Interfaces usable today (legal)

| Interface | Use |
|-----------|-----|
| `https://api.x.ai/v1` (Bearer) | Cloud Grok |
| Normal IP over Starlink WAN | Transport |
| Dish gRPC :9200 status/history (community tools) | Link health gating |
| Local Ollama / edge OpenAI-compatible | Offline brain |
| Enterprise Starlink APIs | Multi-terminal ops (account-gated) |

**Do not invent:** residential dish REST for routing; space-side Grok endpoint; "secret Musk mesh" SLA.

---

## 2. End-to-end architecture

```
+------------------+     +-------------------+     +------------------+
| Operator TUI     |     | ascent-satd       |     | Local edge LLM   |
| (readline/CLI)   | <-> | session + queue   | <-> | (Ollama etc.)    |
+------------------+     | mode: cloud|edge  |     +------------------+
                         | sacred-meter      |
                         +---------+---------+
                                   |
                    ASCENT stream (P0+P5+P6+P7 + SkyPulse PATHHINT)
                    optional P9 ASCENT-D wrap (spool/D only)
                                   |
                         +---------v---------+
                         | Transport adapter |
                         | HTTPS/QUIC to API |
                         | or store-forward  |
                         +---------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
     +--------v-------+   +--------v-------+   +--------v-------+
     | Home fiber WAN |   | Starlink dish  |   | (future BP ADU)|
     | (primary)      |   | Ku LEO last mi |   | deep-space lab |
     +--------+-------+   +--------+-------+   +----------------+
              |                    |
              +----------+---------+
                         |
              SpaceX gateway + PoP  (must be up for cloud)
                         |
              public Internet -> api.x.ai -> Colossus GPUs
```

### Layering (normative intent)

```
Physical / RF (stock Starlink kit) or optical ISL (SpaceX internal)
    -> IP (Starlink provides)
        -> TLS 1.3 / QUIC (session crypto)
            -> optional app store-and-forward queue
                -> ASCENT wire (P0 prose + P5 agent + P6 REF + P7 + PATHHINT)
                    -> optional ASCENT-D P9 RS(255,223) erase-on-fail (not default on Starlink IP)
                        -> Grok session logic / local runtime
```

### Operating modes

| Mode | When | Brain |
|------|------|-------|
| **CLOUD** | `api.x.ai` reachable | Full Grok |
| **EDGE** | WAN up but API down, or forced offline | Local quantized model |
| **QUEUE** | Link flapping / rain / 15s reconfig / PATHHINT obstruction | Buffer ASCENT ADUs; flush on stable RTT |
| **DEAD** | No power / no sky / no model | Honest UX: cannot help until power or local model loads |

---

## 3. Protocol mapping + concrete ASCENT examples

### 3.1 Turn unit (Earth / Starlink IP)

Prefer ASCENT-7 for pure ASCII prompts. Add agent frames only when needed.

```
ASCENT/1.0
session=sat-demo-001 turn=42 mode=cloud

[user prose as P0 bytes]
Status of the Starlink failover path?

9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B
# ROLE=guide (canonical Hello Universe shape)
```

### 3.2 Tool call (idempotent; safe to retransmit)

```
9A C1 01 00 03 00 <flags> <len> <name_len> dish_status <TLV INVOKE_ARGS JSON> 9B
```

Args must escape raw `0x9A`/`0x9B` as `C1 1B <byte>`.

Tool results return inside **SAFETY** (data, never silent control):

```
9A C1 01 00 07 00 <flags> <len> <class:u8=untrusted_tool_result> <body> 9B
```

### 3.3 Multimodal REF (prefer on satellite)

Large images/logs: do **not** INLINE megabytes. Emit P6 kind=REF with sha-256.

```
9D 4D 01 <codec:u16be> <flags> 01 <32-byte sha256> <len:u64be> cid://...
```

### 3.4 ASCENT-D outer for high-erasure / store-forward disk

Logical unit U (<= 8192 B on D):

```
D5 E5 C0 DE | profile=0x44 | ecc_hdr RS(255,223) I=1..8 | len:u32be | unit | parity
```

On fail: erase unit; hunt next sync. Never display corrupt agent bytes.

### 3.5 Session state checkpoint (ASCII greppable)

```
ASCENT/1.0
DEF-lite: profile=E mode=cloud last_good_turn=41 api=ok dish=obstruction=0.02
```

### 3.6 Weight diffs / model updates

**Not** on interactive path. Treat as P6 REF or separate content-addressed annex (ASCENT-A style). Starlink can carry large downloads when Priority bandwidth allows; ASCENT only carries the **hash + metadata**, not the multi-GB blob in-band.

### 3.7 SkyPulse PATHHINT (Starlink IP)

Emit a PATHHINT unit on the turn ADU (before or after the greppable header). Receivers that do not implement `0xC5` must skip-by-length once they ship the reserved P2 skip rule; 2.1.0 codecs decode it natively.

```
0xC5 schema=0x01 len body
  path_id, next_capacity (sender bottleneck bps, not RF PHY),
  freeze_until (relative freeze_ms), confidence, ttl_ms,
  optional obstruction, optional elev_deg, optional CRC
```

On fail: erase (do not apply). Stale TTL or unknown version: erase. Optional P9 wrap only for spool. See `docs/SKYPULSE.md`.

---

## 4. Terminal client design + Python skeleton

### 4.1 Components

| Component | Responsibility |
|-----------|----------------|
| `tui` | Readline chat, mode banner, sacred-meter |
| `ascent_codec` | Existing `ascent-wire` / `ref/ascent_codec.py` |
| `ascent_d` | Optional P9 wrap (`ref/ascent_d.py`) |
| `transport` | HTTPS to xAI; offline queue to disk |
| `dish_probe` | Optional gRPC status (community tools) |
| `brain` | Cloud Grok client XOR local OpenAI-compatible |
| `queue` | SQLite or filesystem spool of ADUs |

### 4.2 Sacred-meter diagnostics (operator UX)

```
[ASCENT] sim mode=CLOUD  p0=1.00  api=ok  rtt=48ms  dish=ONLINE  queue=0  pathhint bottleneck_hint=50.0Mbps freeze_until=15000ms conf=0.80
[ASCENT] sim mode=EDGE   p0=1.00  api=DOWN dish=ONLINE  queue=3  model=llama3.1:8b
[ASCENT] sim mode=QUEUE  p0=1.00  api=ok   dish=OBSTRUCTED queue=12 pathhint obst=0.40
```

Prefix is **sim** unless a real dish probe ran (`obs`). `bottleneck_hint` is predicted sender bottleneck, not a Starlink RF reading. This client does not invent a Starlink telemetry API. TCP :9200 is reachability only.

### 4.3 Skeleton layout

See `examples/ascent_starlink_client/` in this repo:

- `daemon.py` - mode machine + queue flush + SkyPulse PATHHINT meter
- `codec_session.py` - build/parse turn ADUs (PATHHINT prefix)
- `brains.py` - cloud vs edge adapters
- `dish_health.py` - optional status stub + lab obstruction env
- `README.md` - run notes

### 4.4 Local vs remote inference trade-offs

| | Cloud Grok | Local 7B-70B |
|--|------------|--------------|
| Capability | Frontier | Ops-useful, not same class |
| Needs | Path to `api.x.ai` + key | VRAM/CPU + weights on disk |
| Fresh knowledge | Yes (with tools) | Only if pre-cached |
| Power | Low on PC | High if GPU |
| Honesty | Full product | Degraded agent |

---

## 5. Security model

| Concern | Design |
|---------|--------|
| Transport | TLS 1.3 / QUIC to `api.x.ai` only; pin if feasible |
| API auth | Bearer key in OS keyring / env; never in ASCENT P0 logs |
| P7 | Optional PQ envelopes for long offline spool encryption; kids OOB |
| THINK | Opaque on shared logs; redact |
| SAFETY | Untrusted tool results never promote to control |
| Dish gRPC | LAN-only diagnostics; not a trust boundary |
| Long offline | Pre-provision keys; rotate when online; spool ciphertext at rest |
| Adversary | Assume hostile Wi-Fi/LAN; encrypt spool; no cleartext API keys on disk |
| Legal | Stock kit; no firmware mods; export-compliant crypto |

ASCENT-D is **integrity + fail-closed**, not a substitute for TLS/BPSec.

---

## 6. Feasibility assessment + risk register

### 6.1 Scenario matrix

| Scenario | Starlink | Cloud Grok | Edge agent |
|----------|----------|------------|------------|
| Home fiber cut | High value | Usually OK | Backup |
| Regional cell/fiber outage | High | Usually OK | Backup |
| Grid down, you have UPS | Med-High if sky | If DCs powered | Critical |
| All gateways/PoPs dead | RF maybe | **No** | Only path |
| Global terrestrial collapse | Not enough for Grok | **Assumed dead** | Only path |

### 6.2 Risk register

| ID | Risk | Sev | Mitigation |
|----|------|-----|------------|
| R1 | Overclaim "Grok offline via Starlink" | High | Dual-mode UX; kill marketing fantasy |
| R2 | Dish power/sky | High | UPS + Mini option; duty cycle |
| R3 | API down while dish green | High | Edge fallback + probe |
| R4 | LEO reconfig jitter (~15s class) | Med | Queue, resume, ASCENT-D optional |
| R5 | ToS / RE dish firmware | High | Read-only diagnostics only |
| R6 | Export crypto / unauthorized RF | High | App-layer only; counsel if shipping PQ suite |
| R7 | Double FEC tax (D + LTP + TM) | Med | D alone off Starlink IP; E-LEO light CRC; full stack deep-space only |
| R8 | DTN scope creep for LEO IP | High | Phase 1 = pure IP |
| R9 | Local model mistaken for Grok liability | High | Banner "EDGE MODE" |
| R10 | Enterprise-only APIs assumed residential | Med | Feature-detect |

### 6.3 Kill criteria (bad designs)

1. Claims full Grok with zero terrestrial path and no evidence of space inference.  
2. Treats Starlink as compute.  
3. Requires Dishy reverse-engineering or custom RF.  
4. Equates 7B/70B with frontier Grok for high-stakes tasks.  
5. Uses ASCENT as a routing protocol instead of framing.  
6. No degrade path when API dies.  
7. No power budget.

---

## 7. Phased roadmap

### Phase 0 - Simulation and lab (now)

- ASCENT-D BER/erase lab with artificial erasure (already partial in Wire Lab / tests).  
- Starlink-like loss model: random datagram drop + 15s glitch windows.  
- Golden agent turn encode/decode + queue replay.  
- **Exit:** green tests; measured erase rate vs simulated BER.

### Phase 1 - Near-term prototype (works on stock kit)

- CLI/daemon: dual-mode cloud Grok + local Ollama.  
- ASCENT framing for turns (P0 + P5).  
- Failover WAN (fiber primary, Starlink secondary) optional at router.  
- Dish status optional via community tools when a real dish exists. This repo does not invent a Starlink telemetry API.
- Store-and-forward spool when API/RTT bad.  
- **Exit:** survive home ISP outage with cloud Grok still answering; survive API outage with edge mode.

### Phase 2 - DTN-enhanced hybrid + stronger edge

- Optional BPv7 lab (uD3TN AAP or HDTN) carrying ASCENT ADUs for delayed peers.  
- Stronger edge models; RAG over local continuity.  
- Optional ASCENT-D on spool files.  
- **Exit:** multi-hour delayed round-trip demo without lying about interactive Grok.

### Phase 3 - Deep-space ready / partnership

- Requires SpaceX and/or xAI cooperation, or mission hardware: contact plans, LTP, CCSDS coding, possible enterprise dual-home of inference.  
- Lunar/Mars class delays: one ADU per RTT budget; no chatty tool loops.  
- **Exit:** only with external partners or flight program - not a garage-only claim.

---

## 8. Open questions, experiments, today vs later

### Achievable today (no partnership)

- [x] ASCENT codec + agent frames on any IP path  
- [x] ASCENT-D encode/decode erase-on-fail in software  
- [x] Starlink as failover WAN for `api.x.ai`  
- [x] Local edge LLM when API unreachable  
- [x] App-level queue across link flaps  
- [x] SkyPulse PATHHINT encode/decode + fail-closed skip  
- [x] ASCENT-E-LEO vs D integrity helper (no double-FEC on Starlink IP)  
- [x] QUEUE on obstruction / RTT flap in the Phase 1 client

### Requires partnership or new public capability

- [ ] Space-resident Grok inference  
- [ ] Documented sat-only path that never touches public Internet but still reaches xAI  
- [ ] Official residential dish developer control plane  
- [ ] Mission-class BP/LTP over Starlink as a product  

### Recommended experiments

1. **Failover drill:** cut fiber; confirm Grok chat via Starlink; log RTT and failures.  
2. **API kill drill:** block `api.x.ai`; confirm EDGE banner + local answers.  
3. **Glitch inject:** drop 1-5% UDP or reset TCP mid-stream; measure queue recovery.  
4. **ASCENT-D spool:** corrupt random bytes on disk; confirm erase, never bad TOOL.  
5. **Power budget:** measure Watts for Mini vs Standard + PC for 2h and 8h UPS.  
6. **DTN lab only:** one delayed ADU via uD3TN loopback; do not put production chat on BP yet.

---

## Source and confidence index (abbreviated)

| Topic | Confidence | Notes |
|-------|------------|-------|
| ASCENT SPEC planes / P9 RS | High | Product normative |
| Starlink needs ground exit for public APIs | High | Architecture consensus + measurements |
| ISLs extend gateway reach | High | SpaceX marketing + RIPE-style studies |
| Dish :9200 gRPC community tools | High | sparky8512/starlink-grpc-tools |
| BPv7 / LTP standards | High | RFC 9171 / 5326 |
| ECLSA production packaging | Medium | Strong papers; verify fork |
| V3 / orbital AI timelines | Medium | Roadmap / early deploy |
| xAI dual-homed on Starlink for customers | Low / none public | Do not design on it |

---

## Appendix A - Army roles and synthesis

| Role | Outcome used |
|------|----------------|
| ASCENT Protocol Specialist | SPEC plane map, stream examples, P9 fail policy |
| Starlink Systems Researcher | Path model, interfaces, DTC, V2/V3, critical egress truth |
| DTN Expert | A/C vs D stacking; FEC comparison; reject ASCENT-as-CLA |
| Terminal Designer | Mode machine, sacred-meter, Python skeleton |
| Security | TLS + P7 + SAFETY + spool encryption posture |
| Feasibility Critic | Kill criteria, scenario matrix, honesty bar |
| Architecture Synthesizer | This document + roadmap |

Critique loop applied: every "space Grok forever" claim was reduced to dual-mode resilience that works on stock hardware.

---

## Appendix B - Related paths

- Spec: `SPEC.md`  
- SkyPulse: `docs/SKYPULSE.md`  
- OrbitStack / LeoAware: `docs/ORBITSTACK-LEOAWARE-BRIDGE.md`  
- Agent loop: `docs/AGENT-LOOP.md`  
- Codec: `ref/ascent_codec.py`, `ref/ascent_d.py`, `ref/ascent_skypulse.py`  
- Client skeleton: `examples/ascent_starlink_client/`  
- Skill: `~/.grok/skills/ascent-starlink-resilience/`  
- DTN stacking skill: `~/.grok/skills/ascent-dtn-space-stacking/`  
- Live lab: https://ascent.jonbailey.xyz/  
- Public repo: https://github.com/Pitchfork-and-Torch/ascent  
