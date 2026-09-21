# macOS Deployment

## Components
- Ollama service
- ContextOS daemon/MCP server
- SQLite/Postgres/vector store
- Codex CLI/IDE/Desktop

## Recommended paths
```text
~/contextos/               source
~/Library/Application Support/ContextOS/   data
~/Library/Logs/ContextOS/  logs
~/.codex/config.toml       Codex config
~/.codex/hooks.json        user hooks (or project equivalent)
```

## Daemonization
Use `launchd` for ContextOS if long-lived warm caches are desired. The MCP process may also be started directly by Codex using STDIO; keep background consolidation workers separate if needed.

## Health checks
Implement:
- DB writable/readable;
- Ollama reachable;
- configured models installed;
- vector index available;
- schema version current;
- pending migration state;
- queue depth;
- last successful context compilation.

## Backup
Back up event/source/semantic databases before derived caches. Derived vectors, VCL images, and codec artifacts should be rebuildable.

## Upgrade
1. snapshot DB;
2. migrate schema;
3. rebuild affected projections/indexes;
4. run semantic regression suite;
5. switch daemon;
6. retain rollback snapshot.

## Ollama outage
ContextOS continues with deterministic retrieval and structured cached memory. It must not make the entire Codex workflow unavailable merely because local inference is down.
