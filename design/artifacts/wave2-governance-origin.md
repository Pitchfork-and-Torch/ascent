# governance-origin | wave 2

**node:** governance-origin  
**wave:** 2  
**parent:** name-judge  
**standard:** ASCENT  

---

## A. Official name (locked; polish only)

**NAME:** ASCENT  
**Expansion (public):** ASCII Successor with Compatible Encoding of Named Text  
**Committee title (heritage):** American Standard Code for Extended Named Text  
**Pronunciation:** /uh-SENT/  
**Manifesto:** Keep every classic ASCII byte sacred, then ascend scripts, agents, media refs, crypto control, and deep-space links into one self-describing stream - fixed-width control for machines, variable-width data for humans, never remapping `0x00-0x7F`.

Profiles: `ASCENT-7`, `ASCENT-E`, `ASCENT-D`, `ASCENT-A` (section F).

---

## B. Origin Story

*Minutes style, Ad Hoc Joint Working Group on Compatible Text Encoding, late 2020s - early 2030s. Coffee cited more often than quorum.*

The Committee notes that ANSI X3.4-1963 served teletypes, email, and the accidental Internet with distinction. Later decades produced approximately seventeen mutually incompatible "extended ASCII" notions, a script repertoire larger than any code page, agents that demand the same byte stream as prose, and deep-space links whose bit-error rates make UTF-8 look like a parlor game.

It was moved and carried, without enthusiasm, that a successor shall exist; that it shall not be named "ASCII2"; and that it shall not force operators to recompile every shebang and SMTP path on Earth.

Working title ASCENT survived three rejected expansions, two trademark searches, and one argument about whether "ascent" means progress or merely altitude. The minority preferred a purely recursive acronym and was filed under hobbies.

Design law on first reading: **if a byte is less than `0x80`, it is classic 7-bit ASCII, bit-identical, forever.** Novelty begins only at or above that threshold, or behind length-prefixed frames that never alias into the sacred range. The Chair observed this is the only guarantee implementers will actually remember.

Later sessions fixed planes P0-P10+, agent fences, multimodal markers, quantum-safe envelopes, self-describing DEF documents, and a deep-space outer frame for the subset that launches hardware. The Committee does not claim ASCENT ends encoding history. It claims greppers may continue to work.

Adjourned. Next meeting subject to launch windows and ISO calendar collisions.

---

## C. Acronym breakdown

Classical letter-by-letter style:

| Letter | Stands for | Note |
|--------|------------|------|
| **A** | **A**SCII / **A**merican | Roots in X3.4 / ISO 646 IRV identity |
| **S** | **S**uccessor / **S**tandard | Climb with a contract, not a fork |
| **C** | **C**ompatible / **C**ode | Bit-identical `0x00-0x7F`; no overlongs |
| **E** | **E**ncoding of | Wire form plus control grammar |
| **N** | **N**amed | Scalars, opcodes, algs, kinds in registries |
| **T** | **T**ext | Humans first-class; agents and media share the stream |

Public: **ASCII Successor with Compatible Encoding of Named Text.**  
Committee title: **American Standard Code for Extended Named Text.**  
Mnemonic: *ascent* - leave the 7-bit basement, do not burn the stairs.

---

## D. Governance model

### Maintainers

1. **ASCENT Joint Maintenance Group (AJMG)** - dual liaison to **ISO/IEC JTC 1** (character / IT vocabulary) and **IETF** (on-wire profiles, registries). Neither track may silently diverge P0-P2 grammar.
2. **Editors** for core wire grammar, plane registries, agent opcodes, PQ alg IDs, deep-space profiles. Changes land as append-only DEF history, not silent rewrites.
3. **Implementer council** (non-voting): greppability, skip-by-length safety, and "will this brick a cruise probe" review.

### Adding codepoints, opcodes, planes

| Kind | Process | Bar |
|------|---------|-----|
| P0 units | **Closed.** No additions. | Eternal freeze |
| P1 fences / state | Supermajority; major if fence semantics change | Compat impact statement |
| P2 opcodes / leads | Registry assign open IDs; unknown-with-length skippable | Cap max-frame; no ID reuse |
| P3/P4 scalars / clusters | Periodic repertoire updates | No surrogates; no overlongs |
| P5 agent opcodes | Opcode registry; fences mandatory | Safety opcodes not redefined in place |
| P6 multimodal kinds | Kind/codec/hash-alg tables | DoS caps in profiles |
| P7 PQ algs | Append-only alg-id registry | No silent downgrade |
| P8 DEF / self-map | Schema IDs; history chain | Bootstrap immutable without major |
| P9 outer ECC | Profile-scoped families | Hard-fail parity stays hard |
| P10+ private | Explicit plane-select; hash-named or IANA-like experimental | **Cannot redefine P0-P2** |

Private planes are sandboxes. Unregistered private extensions cannot claim pure E/D/A for those bits.

### Compatibility guarantees

- **P0 forever:** pure-ASCII files are valid under identity / E.
- **No overlongs, no remapping 0-127.**
- **Skip-unknown** with declared length (cap max-frame); strict profiles may hard-fault.
- **Major only on control grammar break.** Minor/patch for repertoire, registry adds, clarifications.
- **Deprecation append-only:** IDs never recycled; "do not emit" is a flag, not a reclaim.

### PQ freeze for mid-cruise probes

High-latency deployments may declare a **profile freeze**: content-addressed snapshot of the P7 alg registry (and related DEF slice) bound into the mission DEF. Mid-cruise receivers MUST NOT accept alg IDs outside that freeze without pre-authorized upgrade (ground-commanded VERSION_BUMP or dual-DEF handoff). Silent algorithm substitution is non-conformant. Earth registries may grow; frozen probes stay boring on purpose.

### Self-desc circularity bootstrap

1. Greppable P0 header: `ASCENT/1.0` (or later major) as plain ASCII.
2. Compiled defaults: every conformant decoder ships tables for known `schema:u8` values enough to parse the DEF shell (`0xC0` + schema + length).
3. DEF body: plane map, escape grammar, opcode/kind/alg tables, hash of normative prose (full text in profile A).
4. Validate tables against defaults; strict mismatch is fault. Unknown schema with length: skip or hard-fault per profile.
5. Default pin: first DEF wins unless upgrade policy allows mid-stream VERSION_BUMP. Optional P7 signature over DEF.
6. Circularity answer: open the envelope with eternal P0 header + fixed DEF shell + shipped defaults - never version N+1 knowledge first.

### Trademark and public registry

- Clear "ASCENT" for standards use; prefer open implementation over exclusive trademark (certification mark only if branding needs it).
- Registries public, secret-free, append-only. Content hashes of normative text are first-class.
- Process home: core grammar + repertoire lean ISO/IEC; on-wire registries, agent opcodes, PQ lists lean IETF (or joint). Conflict rule: P0-P2 parse law cannot be weakened by either track alone.

---

## F. Profiles and versioning

| Profile | Role | Notes |
|---------|------|--------|
| **ASCENT-7** | Identity-only | Pure P0; any classic ASCII file |
| **ASCENT-E** | Earth / general | Full control + scripts + agents + MM + crypto; light ECC optional |
| **ASCENT-D** | Deep-space | Strong outer ECC, long sync, low-entropy defaults; MM ref-only allowed; PQ freeze common |
| **ASCENT-A** | Archive / self-desc heavy | Max DEF + hash chain; full normative embed encouraged |

**Versioning**

- **Major:** only when control grammar breaks (fences, leads, DEF shell, parse law). Rare. Loud.
- **Minor:** registry growth, repertoire, opcodes, non-breaking clarifications.
- **Patch:** errata, examples, non-normative notes.
- **P0 forever** across majors: pure-ASCII remains valid under ASCENT-7 and as identity subset of E/D/A.
- Profile labels orthogonal to semver: `ASCENT-E/2.1` is Earth of major 2 minor 1.

Conformance claims MUST name profile + major (and freeze hash when D or mission-frozen).

---

*End governance-origin wave2. ASCENT locked; maintainers, freezes, bootstrap, profiles ready for synthesizer.*
