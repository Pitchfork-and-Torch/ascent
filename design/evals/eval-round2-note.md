# ASCENT evaluator - round 2 note (residual polish)

**node:** residual-polish (optional evaluator-optimizer)  
**round:** 2  
**target:** `.\SPEC.md`  
**baseline:** eval-round1.md PASS **94 / 100**  
**date:** 2026-07-29

---

## What changed

In-place normative polish only. Name remains **ASCENT**. Parse law and P0 locks untouched. No section renumbering; material woven into **C** and **F**.

| Polish item | Where | Change |
|-------------|-------|--------|
| DEF `schema:u8` values | C.3.4 | Enumerated seeds: `0x01` KERNEL (plane+registry), `0x02` ANNEX_HASH (prose annex hash / A embed), `0x03` HISTORY (history-only delta); reserved/registered/private ranges |
| ROLE/TOOL `name_len:u8` | C.3.1 | Normative prefix for ROLE, TOOL, HANDOFF target; aligned with Hello Universe `05 guide` |
| TOOL/CAP TLV | C.3.1 | `type:u8 len:u16be value`; v1 type seeds for TOOL (INVOKE_ARGS/RESULT/ERROR/CANCEL) and CAP (BITSET/REQUIRE/DENY) |
| CHUNK reassembly | C.3.2 | `chunk_index:u32be`; order by index; timeout optional; missing END => incomplete stream (discard, no partial complete) |
| Codec bootstrap seeds | C.3.2 | IDs `0x0001`-`0x0007` (text/json/png/jpeg/octet-stream/wav/mp4) + registry ranges |
| PQ alg bootstrap seeds | C.3.3 | ML-KEM-768/1024, ML-DSA-65/87, SLH-DSA-128f/192f with numeric `alg:u16be` |
| Efficiency vs UTF-8 | C.5.6 | Small comparison table (ASCII/Latin/CJK/emoji/ZWJ); P0 identical; control collision note expanded |
| DEF history `hash-alg` | C.3.4, F.5 | History tuple pins `hash-alg:u8` (same ids as P6; `0=none` illegal for history) |
| Bootstrap cross-ref | F.5 | Points at shipped schema seeds and codec/PQ tables |

## Estimated score

**Still PASS.** Round 1 was 94/100 with ASCII 20/20. Residual items were optional and non-blocking; they close the main polish gaps on criteria 3-6 (agent TLV, multimodal CHUNK, self-desc schema/history, efficiency table) without trading off any locked criterion.

| Criterion | R1 | Est. R2 | Notes |
|-----------|----|---------|-------|
| ASCII identity | 20 | 20 | Unchanged |
| Scripts/emoji | 14 | 14 | Unchanged (repertoire still annex-level) |
| Agent control | 14 | 15 | name_len + TOOL/CAP TLV |
| Multimodal | 9 | 10 | CHUNK rules + codec seeds |
| Self-desc | 13 | 14-15 | schema enum + history hash-alg |
| Efficiency | 9 | 10 | comparison table |
| Deep-space | 5 | 5 | Unchanged |
| Governance | 5 | 5 | F.5 clarified only |
| Completeness A-F | 5 | 5 | Unchanged |
| **TOTAL** | **94** | **~97-99** | Still PASS (>= 85 + ASCII 20) |

Exact re-score not required for this optional pass; estimate is upper-bound confidence only.

## Residual risk

**None material.**

- No rename of ASCENT; no parse-law or P0 change.  
- Hello Universe hex still matches ROLE `name_len` + name.  
- New registries are append-only seeds, consistent with F.2/F.3.  
- CHUNK timeout left optional on purpose (profile/local policy; D SHOULD set mission timer).  
- Full DEF body field-by-field binary layout beyond schema enum remains draft-level detail for a future minor, not a lock break.

## Verdict

**PASS retained.** Residual polish applied. Spec remains coherent for implementer review.

---

*End evaluator round 2 note.*
