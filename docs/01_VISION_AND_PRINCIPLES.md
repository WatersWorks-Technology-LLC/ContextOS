# Vision and Design Principles

## Vision

ContextOS gives an AI agent effectively unbounded historical memory while keeping each expensive reasoning call small, accurate, current, provenance-aware, and task-specific.

The system treats the LLM context window as **working memory**, not long-term storage.

## Primary optimization objective

Maximize:

`TaskQuality × SemanticFidelity`

while minimizing:

`PaidModelInputCost + Latency + RetrievalCost + ContextNoise`

Token count is a component of cost, not the sole objective.

## Design laws

1. **Raw history is immutable evidence.** Summaries and semantic projections are disposable derivatives.
2. **Current state is not history.** The model should receive current truth by default and historical evidence only when needed.
3. **Compile context per task.** There is no universally optimal summary.
4. **Local first.** Deterministic computation and local models perform all context work they can do reliably before Codex is invoked.
5. **Codex remains executive.** Local models prepare, classify, retrieve, compress, and suggest; Codex performs high-value reasoning and action.
6. **Provenance survives compression.** Important assertions remain traceable to original evidence.
7. **Uncertainty survives compression.** Unknown, proposed, inferred, contradicted, and current are distinct states.
8. **Use the native representation.** Tables stay tabular, graphs stay relational, code stays code, exact values stay exact.
9. **Use the least aggressive representation that meets the budget.** Compression failures fall back automatically.
10. **Memory may forget actively but not destructively.** Removal from working memory is not deletion from archive.
11. **Critical semantics are pinned.** Hard requirements, permissions, invariants, and exact identifiers do not receive unsafe lossy compression.
12. **Experimental codecs compete against a safe baseline.** No novel representation becomes production default without measured semantic advantage.
