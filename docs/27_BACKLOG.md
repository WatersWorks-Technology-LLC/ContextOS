# Initial Engineering Backlog

## Epic A — Runtime/MCP
- initialize Python/uv project
- MCP STDIO server skeleton
- health/status tool
- config loader
- workspace resolver
- structured logging

## Epic B — Codex hooks
- UserPromptSubmit adapter
- PostToolUse event capture
- Stop event capture
- Pre/PostCompact state anchor
- subagent context scoping
- hook integration tests

## Epic C — Persistence
- SQLite WAL setup
- migrations framework
- event/source tables
- semantic tables
- context commit tables
- backup/restore utility

## Epic D — Retrieval
- FTS5 index
- Ollama embedding client
- vector index
- entity alias resolver
- hybrid ranker

## Epic E — Semantic IR
- Pydantic schemas
- local extraction prompts
- temporal validity resolver
- supersession logic
- conflict detector

## Epic F — Graph
- graph projection
- weighted traversal
- dead-code eliminator
- causal/dependency slicer

## Epic G — Context compiler
- task classifier
- capsule generator
- relevance cascade
- invariants/open questions/deltas
- packet assembler

## Epic H — Budget/paging
- token estimator
- Z0–Z4 variants
- utility/cost allocation
- page-fault tracking
- cache promotion
- thrash detection

## Epic I — NCC-VCL
- grammar parser
- encoder/decoder
- vocabulary registry
- model-specific surface profiles
- exact escape syntax

## Epic J — Verification
- semantic checksum
- IR diff
- dual extraction
- fallback ladder

## Epic K — VCL research
- Graphviz/SVG renderer
- semantic quiz harness
- atlas packer
- renderer parameter search

## Epic L — Observability/security
- telemetry tables
- dashboards/export
- sensitivity policy
- redaction
- injection-hardening tests
