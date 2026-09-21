# Implementation Plan

## Phase 0 — Baseline
### Deliverables
- benchmark workflows without ContextOS;
- token/context/latency logs;
- semantic question set.
### Definition of done
Baseline results stored and repeatable.

## Phase 1 — MCP + hooks
Build ContextOS daemon, MCP server, `UserPromptSubmit`, `PostToolUse`, and `Stop` integration.
### DoD
A user prompt automatically receives a trivial ContextOS packet; tool/result events are recorded.

## Phase 2 — Lossless event/source store
Append-only schema, workspace isolation, hashing, basic source retrieval.
### DoD
Restart-safe history with source IDs and no mutation path for event semantics.

## Phase 3 — Hybrid retrieval
FTS/BM25 + embeddings + aliases.
### DoD
Known benchmark passages retrieved with target recall.

## Phase 4 — Semantic IR/current state
Entities, assertions, constraints, decisions, temporal state, supersession, conflicts.
### DoD
Current-state questions answerable without rereading full history.

## Phase 5 — Knowledge graph and semantic slicing
Graph traversal, dependency/causal slices, dead-code elimination.
### DoD
Relevant context is materially smaller than hybrid search candidate pool without benchmark loss.

## Phase 6 — Capsules and paging
Z0–Z4 representations, `expand`, `source`, hot/warm/cold.
### DoD
Codex can begin with compact context and expand exact evidence on demand.

## Phase 7 — NCC-VCL
Encoder, decoder, vocab registry, tokenizer profiles.
### DoD
Round-trip semantic tests pass for protected benchmark assertions.

## Phase 8 — Semantic verification
Checksums, dual-pass extraction, fallback ladder.
### DoD
Bad compressed representations are automatically rejected.

## Phase 9 — Budget optimizer
Utility/cost auction, native representation selector, minimal evidence set.
### DoD
Configurable packet budgets are met while maintaining fidelity thresholds.

## Phase 10 — Deltas, keyframes, cache/prefetch
Context commits, semantic diff, stable prefix, promotion/thrashing detection.
### DoD
Long continuing sessions send mostly deltas and expansions.

## Phase 11 — VCL
Deterministic SVG renderer and visual benchmark suite.
### DoD
Graph questions meet fidelity target and provide measurable efficiency benefit on at least one model/profile.

## Phase 12 — VCL-A
Atlas packer, foveated area allocation, tile expansion.
### DoD
Atlas beats separate VCL frames or is disabled by evidence.

## Phase 13 — Research branch
CSC-VCL, VCL-C, vector symbolic memory, semantic wavelets, micro-model memory, visual soft prompts.

## Parallel requirements throughout
- telemetry;
- migration scripts;
- security review;
- regression corpus;
- ADR maintenance;
- documentation updates.
