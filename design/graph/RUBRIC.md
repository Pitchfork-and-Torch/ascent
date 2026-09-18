# Evaluator rubric (0-100)

| Criterion | Points | Pass bar |
|-----------|--------|----------|
| ASCII 0-127 byte-identical + clear embed | 20 | Must be 20/20 |
| Scripts + emoji first-class (no surrogates) | 15 | >= 12 |
| Agent control tokens in-stream | 15 | >= 12 |
| Multimodal streamable refs/payloads | 10 | >= 7 |
| Self-describing meta-document | 15 | >= 12 |
| Efficiency (fixed control / var data / escapes) | 10 | >= 7 |
| Deep-space profile (ECC, low-entropy) | 5 | >= 3 |
| Governance (maintainers, add process, compat) | 5 | >= 3 |
| Completeness A-F + Hello Universe | 5 | 5/5 |

**Pass:** total >= 85 AND ASCII score = 20.

## Anti-patterns to reject

- "Unicode but better" with no novel control plane
- Breaking 0-127
- UTF-16 surrogate pair dependency for emoji
- Marketing name with no technical substance
- Missing self-description recursion
- Vague multimodal hand-wave without stream syntax
