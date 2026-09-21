# System Architecture

## Top-level architecture

```text
USER
  |
  v
Codex UserPromptSubmit hook
  |
  v
ContextOS MCP/daemon
  |
  +--> task classifier
  +--> exact/BM25 retrieval
  +--> vector retrieval
  +--> graph relevance/slicing
  +--> current-state projection
  +--> conflicts/invariants/deltas
  +--> Ollama rerank/extract/compress when useful
  +--> context budget allocator
  +--> representation compiler
  +--> semantic verifier
  |
  v
compact context packet
  |
  v
CODEX executive reasoning/action
  |
  +--> ContextOS MCP expansion/source queries
  +--> normal tools
  |
  v
PostToolUse / Stop hooks
  |
  v
append-only events -> local consolidation -> updated memory
```

## Dual-loop design

### Fast synchronous loop
Runs on the critical path before a Codex turn:
- resolve workspace;
- classify task;
- retrieve candidates;
- apply metadata and graph slicing;
- attach invariants/conflicts/recent deltas;
- choose semantic resolution;
- compile and verify packet.

The fast loop must avoid large-model inference unless necessary.

### Deep asynchronous loop
Runs outside the user's critical path:
- episodic consolidation;
- duplicate/entity reconciliation;
- contradiction analysis;
- answerability indexing;
- VCL regeneration;
- codec benchmarking;
- cache promotion/demotion;
- keyframe creation;
- research experiments.

## Trust layers
1. Raw primary source
2. Deterministic observation
3. Verified canonical assertion
4. High-confidence derived assertion
5. Local-model inference
6. Compressed representation
7. Speculative association

Lower layers never override higher layers without an explicit correction event.

## Core subsystems
- **MCP Gateway** — Codex-facing operations.
- **Hook Adapter** — maps Codex lifecycle events to ContextOS operations.
- **Event Store** — immutable historical record.
- **Source Store** — evidence payloads and pointers.
- **Semantic Store** — entities, assertions, relations, temporal state.
- **Episodic Store** — interaction/event clusters.
- **Vector Index** — semantic retrieval.
- **Knowledge Graph** — explicit dependency/causal/topological retrieval.
- **Context Compiler** — produces task-specific working set.
- **Codec Layer** — structured text, NCC-VCL, CSC-VCL, VCL, VCL-A.
- **Verifier** — semantic round trip, checksums, critical assertion testing.
- **Model Router** — local Ollama model selection.
- **Cache/Pager** — hot/warm/cold and semantic page faults.
- **Telemetry** — costs, latency, codec quality, retrieval behavior.

## Failure philosophy
ContextOS must degrade in this order:
1. aggressive compact representation;
2. less-compressed structured representation;
3. direct relevant excerpts;
4. no injected context.

It must never degrade by inventing context.
