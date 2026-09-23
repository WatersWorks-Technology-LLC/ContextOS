# MCP Interface Specification

## Request identity and workspace routing

Every tool accepts `cwd`, `project_id`, `session_id`, and `agent_id` at the top
level. `cwd` must identify an existing absolute directory; symlinks are resolved
before routing. `project_id` is a single safe directory name. Runtime identity
comes from the server configuration/MCP client handshake, never from assertion
content. An explicitly injected adapter keeps its configuration at initialize.

For a named session, first call either `prepare_turn` or `session_start` with
`cwd`. This binds the session ID to one canonical workspace and project for the
lifetime of that MCP server. Subsequent tools can supply only `session_id`.
An explicit conflicting workspace or project fails with `result.isError = true`
before any tool operation. Use a new session ID for a different workspace or
project, including when two concurrent tasks happen to have the same session ID.
There is no process-wide active workspace, `chdir`, or last-used workspace fallback.

```json
{"name":"session_start","arguments":{"cwd":"/work/mobile","project_id":"iphone","session_id":"mobile-task"}}
{"name":"prepare_turn","arguments":{"session_id":"mobile-task","prompt":"Review release acceptance"}}
{"name":"record","arguments":{"session_id":"mobile-task","kind":"decision","payload":{"subject":"release","predicate":"targets","object":"iPhone"}}}
{"name":"query","arguments":{"session_id":"mobile-task","mode":"decisions"}}
```

A tool can also use an explicit `cwd` and optional `project_id` without binding a
session. Supplying an unknown named session plus `cwd` permits that one request;
only `prepare_turn`/`session_start` establish reusable bindings. Omitting
`project_id` uses the bound project, the launch project for the launch cwd, or
the selected workspace's configuration for a new cwd. Configuration precedence
is explicit project, `CONTEXTOS_PROJECT_ID`, workspace YAML, then `default`.
Adapters and worker pools are reused per workspace/project/runtime.

Calls that omit both `cwd` and `session_id` retain the fixed launch workspace for
legacy single-workspace clients. They never inherit another task's workspace.
A new **named** session without `cwd` now fails, including `session_start`. This
avoids hydrating the server's launch project before the client's first explicit
workspace selection. After such an error, `prepare_turn(session_id, cwd, prompt)`
can establish the correct binding. Already bound named sessions need no `cwd`.

`agent_id` defaults to `main`; `subagent_stop` defaults to its `role`. Lifecycle
hooks, goal checkpoints, hydration, source writes, and reads carry that agent
identity. `subagent_start` uses the selected agent as the parent of its `role`.
Tool results include the resolved identity and canonical cwd under
`result._meta.contextos` for client diagnostics.

## Tool behavior

| Tool | Content arguments | Result |
| --- | --- | --- |
| `prepare_turn` | `prompt`, optional `turn_id` | Compiled context in `additionalContext`, hook output, and JSON text. `turn_id` is currently accepted but compilation generates its own commit identity. |
| `session_start` | none | Scoped assertion/pin counts and active goal. |
| `post_tool_use` | `tool_name`, `tool_input`, `tool_output` | Scoped goal checkpoint and queued evidence ingestion. |
| `pre_compact` | none | Source ID of the scoped assertion/invariant snapshot. |
| `post_compact` | none | Scoped invariant and active-goal context. |
| `subagent_start` | `role`, `prompt` | Context and inherited parent-goal reference. |
| `subagent_stop` | `role`, `result_text` | Recorded subagent result. |
| `stop_eval` | `final_text` | Block/reason for an unfinished scoped goal; no block on an allowed stop. |
| `query` | `query`, `mode` | Assertions or conflict/closed-branch lists. Modes: `search`, `state`, `timeline`, `decisions`, `constraints`, `questions`, `conflicts`. `timeline` uses the bounded historical search, not an event timeline. |
| `expand` | `id`, `level` | Z0 identity, Z1 state, Z2 relationships, Z3 rationale/conflicts, or Z4 evidence. |
| `source` | `source_ids`, optional `max_chars` | Exact scoped evidence, default 12000 characters per store. |
| `record` | `kind`, `payload` | Durable assertion ID. |
| `visual` | none | SVG of the selected adapter's in-memory graph. |
| `stats` | none | Scoped assertion counts and referenced entity count. |

`record.payload` accepts `subject`, `predicate`, `object`, `rationale`, and
`turn_id`. Legacy `payload.session_id` and `payload.agent_id` select the same
binding as their top-level equivalents; contradictory values fail. Payload
`project`/`project_id`, `workspace`/`workspace_id`/`cwd`, and runtime/origin identity
fields are consistency assertions only. They must match the selected scope;
they never select a store or overwrite provenance. Use top-level `cwd` and
`project_id` to select storage. The writer records runtime, workspace, project,
origin session, and origin agent from the resolved identity.

Client-store queries, expansion, and stats filter runtime/workspace/project
identity, even if a physical database contains foreign records. Session and
ephemeral assertions additionally match their originating session and agent.
Durable project assertions remain reusable by sessions in that project. Exact
source retrieval requires the full identity; legacy/foreign sources are omitted.
Hook retrieval may additionally use deliberately shared durable truth within the
selected workspace/project; it excludes shared transient state. Graphs are
in-memory adapter state, separate across workspace/project/runtime.

## Upgrade and recovery

Restart the MCP server after installing this change so clients discover the new
tool schemas. Bind active sessions again after every restart: bindings are
process-local, not inferred from recent activity or old event records. Update
any custom named `SessionStart` hook to pass `cwd: "${cwd}"`; the shipped
`UserPromptSubmit` configuration already supplies cwd to `prepare_turn`.

No database relocation, deletion, or assertion rewriting is performed. Existing
storage paths continue to follow `ContextOSConfig`, including configured data
directories, workspace IDs, projects, and runtime partitions. Records previously
written into the wrong launch workspace remain there. Identity-scoped MCP reads
omit legacy records whose stored identity does not match; review any necessary
corrections or migrations separately rather than relabeling provenance silently.
This routing contract provides local namespace isolation, not authorization to
access a directory for an untrusted remote client.
