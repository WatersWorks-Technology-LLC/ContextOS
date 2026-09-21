# External References

These links are implementation references rather than dependencies on undocumented behavior.

## OpenAI / Codex
- Codex MCP: https://developers.openai.com/docs/extend/mcp
- Codex hooks: https://developers.openai.com/docs/hooks
- Codex configuration basics: https://developers.openai.com/docs/config-file/config-basic
- Codex configuration reference: https://developers.openai.com/docs/config-file/config-reference

Key facts used by this design:
- local Codex clients support STDIO and Streamable HTTP MCP servers;
- Codex MCP configuration lives in `config.toml` and may be project-scoped for trusted projects;
- lifecycle hooks include events such as `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, subagent events, and `Stop`;
- `UserPromptSubmit` can return `additionalContext` as developer context.

## Ollama
- Structured outputs: https://docs.ollama.com/capabilities/structured-outputs
- Embeddings: https://docs.ollama.com/capabilities/embeddings
- Tool calling: https://docs.ollama.com/capabilities/tool-calling
- Model library: https://ollama.com/library

Key facts used by this design:
- local `/api/chat` supports schema-constrained structured output;
- `/api/embed` supports local embedding generation;
- Ollama supports function/tool calling for compatible models.

## Architecture background
- Event Sourcing (Martin Fowler): https://martinfowler.com/eaaDev/EventSourcing.html

Model names in examples are replaceable configuration defaults, not architectural requirements.
