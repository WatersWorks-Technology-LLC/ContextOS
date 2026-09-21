# Context Compiler

## Input
- user task/prompt;
- workspace;
- active session state;
- target Codex model/profile;
- token/image budget;
- canonical memory and indexes.

## Output
A verified context packet containing only task-relevant working state plus expansion handles.

## Pipeline
1. Resolve workspace.
2. Record prompt event.
3. Classify task locally.
4. Resolve task entities.
5. Run hybrid retrieval.
6. Expand graph candidates.
7. Apply semantic dead-code elimination.
8. Fetch invariants, conflicts, open questions, recent deltas.
9. Local rerank if needed.
10. Generate Z0–Z4 capsule alternatives.
11. Allocate budget.
12. Choose native representation per object.
13. Compile structured text/NCC/etc.
14. Select minimal evidence set.
15. Verify semantic integrity.
16. Fall back if verification fails.
17. Return packet and log metrics.

## Task classification schema
```json
{
  "task_type":"debugging",
  "entities":["..."],
  "temporal_scope":"current",
  "needs_exact_sources":false,
  "needs_history":true,
  "likely_memory_classes":["decisions","recent_changes","constraints"]
}
```

## Native representation selector
- exact strings/code/commands -> exact text;
- repeated rows -> columnar/table;
- topology -> graph/VCL;
- sequence/history -> timeline;
- boolean finite state -> bitset/compact columns;
- ordinary semantic relationships -> NCC-VCL;
- uncertain critical evidence -> structured natural language + provenance.

## Compile principle
Do not compress prose directly when a semantic IR can be extracted first. Normalize meaning, then choose a surface representation.
