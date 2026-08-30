# Graph engineering design - Next ASCII

- **Task:** Invent, fully specify, and document the official successor to ASCII (1963).
- **Loop enough?** Yes. Name/architecture search is parallelizable; full spec needs critique against hard constraints.
- **Nodes:** invent-A/B/C/D -> name-judge -> specialists (planes, agents-mm, deep-space, governance-origin) -> synthesizer -> evaluator (loop-back if score < threshold)
- **Edges:** fan-out | fan-in | sequential | loop-back
- **Shared state:** `.\` (artifacts/, graph/, evals/)
- **Metric + evaluator:** Rubric 0-100: (compat 20, scripts/emoji 15, agent tokens 15, multimodal 10, self-describing 15, efficiency 10, deep-space 5, governance 5, completeness A-F 5). Pass >= 85.
- **Budgets:** Wave1 = 4 inventors; Wave2 = 4 specialists; 1 synthesizer; up to 2 evaluator-revise cycles. No paid swarm storms.
- **Provenance:** Each artifact has authoring node id + wave + timestamp in YAML frontmatter-style header.
- **Traceability:** Every section of final SPEC.md maps to a graph node path.
- **Stop when:** Final SPEC.md covers A-F, Hello-Universe example is valid per encoding rules, evaluator score >= 85.

## Hard constraints (from operator prompt)

1. Perfect backward compatibility with classic 7-bit ASCII (0-127 identical, byte-identical).
2. Native first-class: living languages + major historical scripts; emoji without surrogate pairs; LLM/agent control tokens; multimodal streamable payloads; quantum-safe crypto control sequences.
3. Self-describing: encoding carries its own complete definition + version history in one valid document.
4. Efficient: fixed-width control planes + variable-width data planes + clear escapes.
5. Agent-native + deep-space profile with strong ECC and low-entropy defaults.

## Deliverables A-F

A. Name + expanded acronym + one-sentence manifesto
B. Origin Story (1960s committee style + dry Grok humor)
C. Full technical overview (planes, ASCII embed, controls, encoding rules)
D. Acronym breakdown (classic ASCII explanation style)
E. Hello, Universe example (human + agent token + multimodal ref)
F. Governance model

## Tone

Precise, slightly mischievous, maximally useful. Ship-ready, not marketing fluff.
