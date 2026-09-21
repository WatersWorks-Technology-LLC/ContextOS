# ContextOS — Documentation Pack

ContextOS is a domain-independent semantic memory and context operating system for AI agents. Its reference integration is a symbiotic architecture in which:

- **Codex** is the executive reasoning and acting model.
- **Ollama** is the local context coprocessor.
- **ContextOS** maintains durable memory, retrieves and compiles task-specific working context, verifies semantic fidelity, and exposes controlled memory operations over MCP.

The objective is not merely prompt compression. The objective is to compile the **smallest trustworthy working world-model** necessary for the next act of reasoning.

## Start here

1. `docs/00_INDEX.md`
2. `docs/02_PRD.md`
3. `docs/03_SYSTEM_ARCHITECTURE.md`
4. `docs/04_CODEX_INTEGRATION.md`
5. `docs/26_IMPLEMENTATION_PLAN.md`
6. `docs/29_AGENTS.md`

## Reference artifacts

- `examples/codex_config.toml` — Codex MCP configuration example
- `examples/hooks.json` — lifecycle hook configuration example
- `examples/contextos.yaml` — server configuration example
- `examples/models.yaml` — local Ollama routing example
- `examples/context_packet.txt` — example compiled working-memory packet
- `schemas/semantic_ir.schema.json` — canonical semantic IR schema
- `schemas/context_packet.schema.json` — compiled packet schema
- `schemas/mcp_tools.schema.json` — MCP tool interface summary

## Implementation rule

All experimental representations—NCC-VCL, CSC-VCL, VCL, VCL-A, VCL-C, vector-symbolic memory, semantic wavelets, micro-model memory, and visual soft prompts—must compile from the same canonical semantic IR. None may become the sole source of truth.
