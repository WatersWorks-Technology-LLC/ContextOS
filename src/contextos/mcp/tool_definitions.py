"""MCP definitions; keep schemas/mcp_tools.schema.json in sync (tested)."""

SCOPE_PROPERTIES = {
    "cwd": {"type": "string", "description": "Absolute existing workspace directory. Never changes the server default."},
    "project_id": {
        "type": "string", "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$",
        "description": "Project within cwd; defaults to the bound session or selected workspace configuration.",
    },
    "session_id": {
        "type": "string", "minLength": 1,
        "description": "Bound by prepare_turn/session_start with cwd; a new named session always requires cwd.",
    },
    "agent_id": {
        "type": "string", "minLength": 1,
        "description": "Agent identity within the session; defaults to main (role for subagent_stop).",
    },
}


def _tool(name, description, properties=None):
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": {**(properties or {}), **SCOPE_PROPERTIES}}}


TOOLS = [
    _tool("prepare_turn", "Compile pre-turn context packet", {
        "prompt": {"type": "string"}, "turn_id": {"type": "string"}}),
    _tool("session_start", "Hydrate session state and goals"),
    _tool("post_tool_use", "Record tool output and update goal checkpoints", {
        "tool_name": {"type": "string"}, "tool_input": {"type": "object"}, "tool_output": {"type": "string"}}),
    _tool("pre_compact", "Snapshot context before compaction"),
    _tool("post_compact", "Rehydrate context post-compaction"),
    _tool("subagent_start", "Scope context for subagent", {
        "role": {"type": "string"}, "prompt": {"type": "string"}}),
    _tool("subagent_stop", "Record subagent outcome", {
        "role": {"type": "string"}, "result_text": {"type": "string"}}),
    _tool("stop_eval", "Evaluate goal completion before allowing session stop", {
        "final_text": {"type": "string"}}),
    _tool("query", "Query structured memory (state, timeline, decisions, conflicts)", {
        "query": {"type": "string"}, "mode": {"type": "string", "enum": [
            "search", "state", "timeline", "decisions", "constraints", "questions", "conflicts"]}}),
    _tool("expand", "Demand paging: raise semantic resolution level (Z0 to Z4)", {
        "id": {"type": "string"}, "level": {"type": "integer"}}),
    _tool("source", "Fetch exact raw evidence bundle", {
        "source_ids": {"type": "array", "items": {"type": "string"}}, "max_chars": {"type": "integer"}}),
    _tool("record", "Record durable decision or constraint", {
        "kind": {"type": "string"}, "payload": {"type": "object", "description":
            "Assertion content. Legacy session_id/agent_id are accepted; any supplied workspace/project/runtime identity must match the selected request scope."}}),
    _tool("visual", "Generate SVG visual context graph map"),
    _tool("stats", "Fetch operational diagnostics"),
]
