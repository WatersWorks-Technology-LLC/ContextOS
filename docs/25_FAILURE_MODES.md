# Failure Modes and Mitigations

| Failure | Effect | Detection | Mitigation |
|---|---|---|---|
| Local model hallucinates assertion | false memory | source mismatch / dual pass / verifier | candidate-only writes; provenance; fallback |
| Current state stale | Codex reasons from obsolete truth | timestamp, supersession inconsistency | event projection rebuild; PostToolUse ingestion |
| Retrieval omission | missing constraint/decision | benchmark miss; Codex page fault | hybrid retrieval; graph; conflicts/invariants pinned |
| Overcompression | relation/state lost | round-trip semantic diff | less aggressive codec |
| Entity merge error | unrelated memories contaminate | merge confidence/audit | stricter thresholds; split event |
| Cross-workspace retrieval | privacy/context contamination | namespace checks | deny-by-default workspace filter |
| Hook latency | Codex feels slow | p95 hook metric | deterministic fast path; async heavy work |
| Ollama outage | local context features unavailable | health check | deterministic fallback/cached state |
| Context thrash | excessive page faults | repeated load/evict | promotion/pinning/budget adjustment |
| VCL visual ambiguity | wrong graph decoding | VCL benchmark / semantic quiz | layout split; larger fonts; redundant labels |
| Codec drift after model update | sudden comprehension regression | periodic benchmark | model-specific profiles; automatic rollback |
| Prompt injection in stored artifact | memory subsystem follows hostile text | schema extraction boundary | treat source as data; fixed prompts; no tool execution |
| Source deleted/moved | provenance cannot expand | hash/path failure | content-addressed snapshots where policy allows |
| Excessive memory growth | storage/performance degradation | DB/index telemetry | archive partitions; rebuildable derived data |
