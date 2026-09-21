# MCP Interface Specification

Keep the public tool surface deliberately small. Tool definitions consume context and excessive specialization makes Codex orchestration worse.

## 1. `prepare_turn`
Primarily invoked by `UserPromptSubmit`.

Input:
```json
{
  "session_id": "...",
  "turn_id": "...",
  "workspace": "...",
  "cwd": "...",
  "prompt": "...",
  "model": "..."
}
```

Output fields:
- `context_text`
- `context_commit`
- `confidence`
- `expandable_ids`
- `source_ids`
- `metrics`

The hook adapter transforms `context_text` into Codex `additionalContext`.

## 2. `query`
Generic structured retrieval.

Input:
```json
{
  "query": "why was decision D22 made?",
  "mode": "search|state|timeline|conflicts|related|decisions|questions",
  "entity_ids": ["optional"],
  "max_items": 10,
  "resolution": 2
}
```

Output: typed results with confidence, temporal validity, and source pointers.

## 3. `expand`
Raises semantic resolution of a capsule/entity/assertion.

Input:
```json
{"id":"AUTH", "level":3}
```

Levels:
- 0 identity
- 1 current state
- 2 key relationships
- 3 detailed semantic capsule
- 4 raw evidence bundle

## 4. `source`
Fetch original evidence.

Input:
```json
{"source_ids":["S17","S22"], "max_chars":12000}
```

Never paraphrase this result unless explicitly requested; it is an evidence operation.

## 5. `record`
Explicit durable write used by Codex for high-value semantic changes.

Input:
```json
{
  "kind": "decision|constraint|fact|question|correction|task_state",
  "payload": {},
  "source_refs": []
}
```

All writes create events first; projections update afterward.

## 6. `visual`
Generate VCL/VCL-A representations.

Input:
```json
{
  "ids":["..."],
  "format":"vcl|vcl-a|timeline|dependency",
  "zoom":2
}
```

## 7. `stats`
Operational diagnostics. Should not be used as normal task context.

Returns latency, compression, cache, model-routing, and verification metrics.

## Tool output rules
- include IDs and provenance;
- mark inference and uncertainty explicitly;
- never imply absence when retrieval is incomplete;
- cap default output aggressively;
- supply expansion handles instead of giant payloads.
