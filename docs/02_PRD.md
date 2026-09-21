# Product Requirements Document

## Product
**ContextOS** — local-first semantic memory and context compiler for Codex-compatible AI workflows.

## Problem
Long-running agents repeatedly spend context and reasoning capacity re-reading history, resolving obsolete facts, locating relevant evidence, and reconstructing current state. Large context windows reduce but do not eliminate this problem.

## Product outcome
Before Codex reasons on a user turn, ContextOS should normally supply a small verified context packet representing the relevant working world-state. Codex may expand any compressed item or retrieve raw evidence through MCP.

## Primary users
- developers using Codex CLI/IDE/Desktop with persistent projects;
- long-running autonomous or semi-autonomous agents;
- research users evaluating context compression and AI memory architectures.

## Functional requirements

### FR-1 Automatic pre-turn context
On `UserPromptSubmit`, ContextOS must classify the task, retrieve relevant memory, compile a packet, verify it, and return developer context within the configured synchronous latency budget.

### FR-2 Mid-turn expansion
Codex must be able to request state, timeline, conflicts, relationships, decision rationale, or raw sources through a small MCP tool surface.

### FR-3 Automatic observation
Tool calls and results must be observable through lifecycle hooks and recorded in the append-only event log.

### FR-4 Durable semantic memory
The system must maintain entities, assertions, relationships, events, episodes, decisions, constraints, conflicts, open questions, provenance, and temporal validity.

### FR-5 Current-state projection
The system must distinguish current, historical, proposed, rejected, unknown, and superseded assertions.

### FR-6 Task-conditioned retrieval
Retrieval must combine exact lookup, lexical search, embeddings, graph relevance, metadata, and optional local-model reranking.

### FR-7 Semantic dead-code elimination
Context not capable of materially affecting the current task should be omitted or reduced to low-resolution awareness.

### FR-8 Progressive disclosure
Memory objects must be available at multiple semantic resolutions, with raw evidence accessible on demand.

### FR-9 Context budget allocation
Context must be allocated by semantic utility per cost rather than FIFO history order.

### FR-10 Verification
Critical compressed information must pass semantic round-trip verification. Failed codecs must fall back automatically.

### FR-11 NCC-VCL
The first experimental compact textual codec must support normalized telegraphic language, VCL relation codes, explicit state, logic operators, source pointers, and confidence.

### FR-12 VCL/VCL-A
The system must support deterministic SVG visual context and packed atlases behind feature flags.

### FR-13 Benchmarking
Every turn must log enough telemetry to compare raw candidate context against delivered context and resulting task quality.

### FR-14 Workspace isolation
No memory may cross workspace boundaries unless explicitly configured.

## Non-functional requirements
- local-first operation;
- fail-open toward less compressed context, not silent omission;
- deterministic storage and provenance;
- typed JSON schemas for all local-model extraction;
- restart-safe persistence;
- graceful operation when Ollama is unavailable;
- typical hot-path context preparation target under 2 seconds;
- no experimental codec on critical facts unless verified.

## Initial success criteria
- >=5x reduction in historical/task-support context sent to Codex on benchmark workflows;
- 100% preservation of L0/L1 benchmark assertions;
- >=99% preservation of L2 relationship assertions;
- context packet preparation <2 seconds median on warm local state for ordinary turns;
- all compressed assertions source-addressable;
- no hidden mutation of event history.

## Non-goals for MVP
- replacing Codex reasoning;
- fully autonomous memory truth adjudication;
- model training or fine-tuning;
- VCL-C as production default;
- storing secrets that should not be persisted;
- cross-user cloud service.
