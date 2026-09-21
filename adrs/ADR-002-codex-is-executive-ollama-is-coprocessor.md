# ADR-002: Codex is executive; Ollama is context coprocessor

**Status:** Accepted

Local models perform context-heavy preparation, extraction, retrieval, compression, and verification. Codex retains responsibility for high-value reasoning, code changes, and important judgment. Local model output is not canonical by default.
