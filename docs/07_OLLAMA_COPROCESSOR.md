# Ollama Context Coprocessor

## Role
Ollama performs context-heavy local work that does not justify premium Codex reasoning.

## Priority order
Always prefer:
1. deterministic algorithms;
2. embeddings/vector math;
3. small fast local model;
4. medium worker model;
5. strong local analyst;
6. Codex escalation.

## Workloads appropriate for Ollama
- task classification;
- schema-constrained entity/assertion extraction;
- candidate reranking;
- episode summarization;
- duplicate detection assistance;
- contradiction classification;
- semantic capsule generation;
- NCC/CSC codec generation and decoding;
- semantic round-trip verification;
- answerability index generation;
- low-risk source summarization.

## Workloads that should remain Codex/user decisions
- architectural decisions with substantial downstream impact;
- ambiguous corrections to canonical truth;
- high-risk judgment;
- destructive actions;
- user intent resolution when evidence is genuinely insufficient.

## Suggested model roles
Do not hard-code model names into architecture. Configure by capability.

Example:
```yaml
embedding: qwen3-embedding
fast_classifier: qwen3:4b
worker: gpt-oss:20b
analyst: glm-4.7-flash
```

The actual list must be benchmarked on the local machine.

## Structured outputs
All extraction/consolidation requests must use JSON Schema/Pydantic-compatible structured output and temperature near zero. Reject invalid responses rather than parsing prose heuristically.

## Confidence escalation
- >=0.95: accept low-risk local result if deterministic checks pass.
- 0.80–0.95: second local verification for important assertions.
- 0.60–0.80: retrieve more evidence; do not canonicalize automatically.
- <0.60: expose uncertainty to Codex.

## Local model isolation
The local model does not directly mutate canonical tables. It emits **candidates**. Deterministic application code validates IDs, schemas, provenance, temporal rules, and promotion policy before state changes occur.
