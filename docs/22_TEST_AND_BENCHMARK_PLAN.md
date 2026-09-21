# Test and Benchmark Plan

## Test layers
### Unit
Parsers, schemas, graph traversal, temporal rules, budget algorithms, codecs.

### Property tests
- round-trip IR semantics;
- supersession acyclicity;
- no unknown node references;
- source pointers preserved;
- negation/hardness never lost for L1 assertions.

### Integration
- Codex hook -> ContextOS -> additional context;
- Codex MCP query/expand/source;
- Ollama structured output validation;
- PostToolUse event ingestion;
- restart persistence.

### End-to-end
Use fixed repositories/conversations with known decisions and ask realistic continuation/debugging questions.

## Synthetic benchmark corpus
Minimum initial corpus:
- 250 entities;
- 1,000 relationships;
- 150 events;
- 100 decisions;
- 100 constraints;
- 50 contradictions;
- exact values and hashes;
- temporal supersession;
- distractor documents.

## Representation competitors
1. full relevant raw text
2. prose summary
3. structured English
4. JSON
5. NCC-VCL
6. CSC-VCL
7. native tables/graphs
8. VCL
9. VCL-A
10. later VCL-C

## Question classes
- direct recall
- current state
- temporal state
- supersession
- hard constraint
- multi-hop dependency
- causal explanation
- uncertainty/conflict
- provenance
- exact value
- unexpected query

## Ablations
- without graph slicing;
- without vector retrieval;
- without local reranking;
- without semantic verification;
- NCC without symbols;
- VCL without redundant labels;
- atlas with/without gutters;
- varying image resolution;
- varying context budget.

## Gate for production codec
A codec must demonstrate a statistically meaningful semantic-efficiency improvement over structured English on the target model while meeting critical-fidelity thresholds.
