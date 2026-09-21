# Configuration Reference

## Major sections

### `server`
- data directory
- log level
- MCP transport
- health port

### `workspace`
- root resolution strategy
- cross-workspace access policy
- ignored paths

### `models`
- embedding model
- fast model
- worker model
- analyst model
- timeout/concurrency

### `retrieval`
- lexical top-k
- vector top-k
- graph depth
- temporal decay
- rerank count

### `compiler`
- default text budget
- maximum pre-turn budget
- max sources
- minimum confidence
- dead-code threshold

### `verification`
- L0/L1 thresholds
- dual-pass rules
- maximum fallback attempts

### `paging`
- hot/warm/cold thresholds
- promotion counts
- thrash window
- keyframe interval

### `codecs`
- enabled codecs
- NCC vocabulary version
- symbol profile
- VCL renderer profile
- VCL-A feature flag

### `privacy`
- default sensitivity
- secret patterns
- local-only source types

### `experiments`
Feature flags for CSC-VCL, VCL-C, vector-symbolic memory, semantic wavelets, micro-model memory, and visual soft prompts.

## Configuration principle
All model names and experimental features must be configurable. Architecture code should depend on capabilities/roles, not vendor-specific model names.
