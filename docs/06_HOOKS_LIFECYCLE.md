# Codex Hook Lifecycle Specification

## UserPromptSubmit
### Purpose
Compile context before Codex reasons.

### Synchronous path
1. Resolve workspace and task.
2. Append user prompt event.
3. Query exact/lexical/vector indexes.
4. Find task entities.
5. Add graph-relevant dependencies.
6. Apply semantic dead-code elimination.
7. Fetch invariants, conflicts, recent deltas.
8. Optionally rerank with fast Ollama model.
9. Run budget allocator.
10. Encode.
11. Verify critical semantics.
12. Return developer `additionalContext`.

### Time budget
Default timeout: 8–12 seconds at hook level, but design target <2 seconds median warm.

### Fail behavior
If ContextOS fails, return no injected context rather than blocking ordinary turns, except where an explicit safety/policy rule requires blocking.

## PreToolUse
### Purpose
Prevent known semantic-policy violations and surface immediately relevant invariants.

### Requirements
- deterministic only by default;
- no vector-wide search;
- no heavy local LLM;
- target <100 ms;
- may block only explicit configured policy violations.

## PostToolUse
### Purpose
Observe environment changes.

### Behavior
- synchronously append minimal event;
- enqueue full processing;
- return quickly;
- do not summarize large tool output on the hook path.

## PreCompact
Snapshot:
- active task roots;
- current context commit;
- hot capsules;
- invariants;
- unresolved conflicts/questions;
- source handles.

## PostCompact
Return a compact anchor sufficient for the post-compaction Codex session to reconnect to ContextOS.

## Stop
Append Codex's final response as an event and queue structured extraction for durable changes.

## SessionStart/End
Start warms workspace state; end commits pending deltas and schedules consolidation.

## Subagent hooks
Subagents receive a scoped semantic slice. Their results become candidate memory and require normal provenance/verification before promotion.
