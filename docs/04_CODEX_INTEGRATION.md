# Codex Integration

## Integration strategy
ContextOS integrates with Codex through two independent mechanisms:

1. **MCP** for explicit context/memory tools.
2. **Lifecycle hooks** for automatic pre-turn compilation and post-action observation.

The result is a system in which Ollama/ContextOS is automatically upstream of Codex while remaining queryable during the turn.

## MCP server
Use a local STDIO server by default. Configure in `~/.codex/config.toml` for machine-wide use or `.codex/config.toml` for trusted-project scope.

Reference:
```toml
[mcp_servers.contextos]
command = "/opt/homebrew/bin/uv"
args = ["run", "--project", "/Users/USER/contextos", "contextos-mcp"]
cwd = "/Users/USER/contextos"
enabled = true
startup_timeout_sec = 20
tool_timeout_sec = 120
```

## Server instructions
The MCP `instructions` field should begin with a short self-contained contract:

> ContextOS provides persistent local memory and task-specific context. Prefer `source` over compressed memory when exact wording or conflicting evidence matters. Treat local-model inference as provisional unless verified. Use `query`/`expand` before asking the user to repeat prior project context. Record durable decisions, corrections, constraints, and task-state changes.

## Hook responsibilities
- `SessionStart`: warm workspace caches and produce a small session anchor.
- `UserPromptSubmit`: prepare verified task context and inject it as developer context.
- `PreToolUse`: deterministic policy/invariant lookup only; no heavy inference.
- `PostToolUse`: append event quickly; queue deeper ingestion.
- `PreCompact`: snapshot working semantic state and active references.
- `PostCompact`: inject a compact semantic anchor after context compaction.
- `SubagentStart`: provide a scoped semantic slice.
- `SubagentStop`: ingest useful findings as candidate memory.
- `Stop`: store Codex's final output and extract durable changes.
- `SessionEnd`: finalize deltas, caches, and optional consolidation jobs.

## Context injection policy
A normal `UserPromptSubmit` packet should be 800–1500 tokens. Complex turns may use 1500–2500. Beyond that, prefer MCP expansion during the turn.

## Transcript handling
Do not make the Codex transcript file format a primary persistence API. Use hook payloads as the authoritative event source. Transcript access may be used for debug/recovery only.

## Codex responsibilities
Codex remains responsible for:
- high-complexity reasoning;
- architectural judgment;
- code modification;
- validation strategy;
- user-visible responses;
- deciding when ambiguous local context needs raw-source expansion.

ContextOS/Ollama must never silently make high-impact user decisions and mark them canonical solely because a local model suggested them.
