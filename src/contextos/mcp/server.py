import sys
import json
import uuid
from typing import Dict, Any
from ..hooks.adapter import HookAdapter
from ..core.capsules import ContextCapsuleManager
from ..codecs.vcl_svg import VCLSVGRenderer
from ..identity import IdentityScope

class ContextOSMCPServer:
    """
    ContextOS MCP STDIO Server exposing:
    - prepare_turn
    - query
    - expand (Z0-Z4 demand paging)
    - source (exact evidence retrieval)
    - record (durable writes)
    - visual (SVG visual context atlas)
    - stats
    """
    def __init__(self, adapter: HookAdapter = None):
        self.adapter = adapter or HookAdapter()
        self.capsules = ContextCapsuleManager(self.adapter.semantic, self.adapter.sources)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            client_info = params.get("clientInfo", {})
            cname = client_info.get("name", "").lower()
            if "antigravity" in cname:
                client_id = "antigravity"
            elif "claude" in cname:
                client_id = "claude_code"
            else:
                client_id = "codex"
            
            # Re-initialize adapter with detected client_id
            from ..config import ContextOSConfig
            cfg = ContextOSConfig.load(client_id=client_id)
            self.adapter = HookAdapter(config=cfg)
            self.capsules = ContextCapsuleManager(self.adapter.semantic, self.adapter.sources)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "contextos",
                        "version": "1.0.0"
                    }
                }
            }


        elif method == "notifications/initialized" or method == "initialized":
            return None

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {"name": "prepare_turn", "description": "Compile pre-turn context packet", "inputSchema": {"type": "object", "properties": {"prompt": {"type": "string"}, "session_id": {"type": "string"}, "turn_id": {"type": "string"}, "cwd": {"type": "string"}}}},
                        {"name": "session_start", "description": "Hydrate session state and goals", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}}},
                        {"name": "post_tool_use", "description": "Record tool output and update goal checkpoints", "inputSchema": {"type": "object", "properties": {"tool_name": {"type": "string"}, "tool_input": {"type": "object"}, "tool_output": {"type": "string"}, "session_id": {"type": "string"}}}},
                        {"name": "pre_compact", "description": "Snapshot context before compaction", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}}},
                        {"name": "post_compact", "description": "Rehydrate context post-compaction", "inputSchema": {"type": "object", "properties": {"session_id": {"type": "string"}}}},
                        {"name": "subagent_start", "description": "Scope context for subagent", "inputSchema": {"type": "object", "properties": {"role": {"type": "string"}, "prompt": {"type": "string"}, "session_id": {"type": "string"}}}},
                        {"name": "subagent_stop", "description": "Record subagent outcome", "inputSchema": {"type": "object", "properties": {"role": {"type": "string"}, "result_text": {"type": "string"}, "session_id": {"type": "string"}}}},
                        {"name": "stop_eval", "description": "Evaluate goal completion before allowing session stop", "inputSchema": {"type": "object", "properties": {"final_text": {"type": "string"}, "session_id": {"type": "string"}}}},
                        {"name": "query", "description": "Query structured memory (state, timeline, decisions, conflicts)", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string"}}}},
                        {"name": "expand", "description": "Demand paging: raise semantic resolution level (Z0 to Z4)", "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "level": {"type": "integer"}}}},
                        {"name": "source", "description": "Fetch exact raw evidence bundle", "inputSchema": {"type": "object", "properties": {"source_ids": {"type": "array", "items": {"type": "string"}}, "max_chars": {"type": "integer"}}}},
                        {"name": "record", "description": "Record durable decision or constraint", "inputSchema": {"type": "object", "properties": {"kind": {"type": "string"}, "payload": {"type": "object"}}}},
                        {"name": "visual", "description": "Generate SVG visual context graph map", "inputSchema": {"type": "object"}},
                        {"name": "stats", "description": "Fetch operational diagnostics", "inputSchema": {"type": "object"}}
                    ]
                }
            }

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})

            if name == "prepare_turn":
                prompt_text = args.get("prompt", "")
                sess_id = args.get("session_id", "default")
                cwd_val = args.get("cwd")
                res = self.adapter.on_user_prompt_submit(
                    prompt_text,
                    session_id=sess_id,
                    cwd=cwd_val
                )
                hook_output = {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": res.get("additionalContext", ""),
                    "telemetry": res.get("telemetry", {})
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "hookSpecificOutput": hook_output,
                        "additionalContext": res.get("additionalContext", ""),
                        "content": [{"type": "text", "text": json.dumps(res)}]
                    }
                }

            elif name == "session_start":
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_session_start(session_id=sess_id)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

            elif name == "post_tool_use":
                tname = args.get("tool_name", "tool")
                tinput = args.get("tool_input", {})
                toutput = args.get("tool_output", "")
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_post_tool_use(tname, tinput, toutput, session_id=sess_id)
                hook_output = {
                    "hookEventName": "PostToolUse",
                    "additionalContext": res.get("additionalContext", "")
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "hookSpecificOutput": hook_output,
                        "additionalContext": res.get("additionalContext", ""),
                        "content": [{"type": "text", "text": json.dumps(res)}]
                    }
                }

            elif name == "pre_compact":
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_pre_compact(session_id=sess_id)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res)}]}}

            elif name == "post_compact":
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_post_compact(session_id=sess_id)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

            elif name == "subagent_start":
                role = args.get("role", "subagent")
                prompt_txt = args.get("prompt", "")
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_subagent_start(role, prompt_txt, session_id=sess_id)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

            elif name == "subagent_stop":
                role = args.get("role", "subagent")
                result_txt = args.get("result_text", "")
                sess_id = args.get("session_id", "default")
                self.adapter.on_subagent_stop(role, result_txt, session_id=sess_id)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "recorded"})}]}}

            elif name == "stop_eval":
                final_txt = args.get("final_text", "")
                sess_id = args.get("session_id", "default")
                res = self.adapter.on_stop(final_txt, session_id=sess_id)
                
                # Codex Stop hook expects decision="block" to create autonomous continuation prompt!
                if res.get("decision") == "block":
                    hook_output = {
                        "decision": "block",
                        "reason": res.get("reason", "Active goal unfulfilled.")
                    }
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": hook_output, "decision": "block", "reason": res.get("reason"), "content": [{"type": "text", "text": json.dumps(res)}]}}
                # For allowed stops, return empty dict result per Codex documentation specification
                return {"jsonrpc": "2.0", "id": req_id, "result": {}}


            elif name == "query":
                kw = args.get("query", "")
                mode = args.get("mode", "search")
                if mode == "decisions":
                    results = self.adapter.semantic.query_current_state(kind="decision")
                elif mode == "constraints":
                    results = self.adapter.semantic.query_current_state(kind="constraint")
                elif mode == "conflicts":
                    results = self.adapter.semantic.query_conflicts_and_closed_branches()
                else:
                    results = self.adapter.semantic.search_assertions(kw)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(results)}]}}

            elif name == "expand":
                item_id = args.get("id")
                level = args.get("level", 3)
                expanded = self.capsules.expand(item_id, level=level)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(expanded)}]}}

            elif name == "source":
                sids = args.get("source_ids", [])
                max_chars = args.get("max_chars", 12000)
                identity = IdentityScope.from_config(self.adapter.config,
                    args.get("session_id", "default"), args.get("agent_id", "main"))
                sources = self.adapter.sources.get_sources(sids, max_chars=max_chars, identity=identity)
                shared = self.adapter.shared_sources.get_sources(sids, max_chars=max_chars, identity=identity)
                sources.update(shared)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(sources)}]}}

            elif name == "record":
                kind = args.get("kind", "fact")
                payload = args.get("payload", {})
                aid = f"AST-{uuid.uuid4().hex[:8]}"
                self.adapter.semantic.add_assertion(
                    aid,
                    subject=payload.get("subject", "system"),
                    predicate=payload.get("predicate", "defined"),
                    object_val=payload.get("object", str(payload)),
                    kind=kind,
                    decision_rationale=payload.get("rationale"),
                    runtime_id=self.adapter.config.client_id,
                    workspace_id=self.adapter.config.workspace_id or str(self.adapter.config.workspace_dir.resolve()),
                    project_id=self.adapter.config.project_id,
                    origin_session=payload.get("session_id", "default"),
                    origin_agent=payload.get("agent_id", "main"),
                    origin_turn=payload.get("turn_id"),
                    identity_confidence="observed"
                )
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "recorded", "assertion_id": aid})}]}}

            elif name == "visual":
                nodes = self.adapter.graph.nodes.values()
                edges = []
                for s, neighbors in self.adapter.graph.adjacency.items():
                    for n in neighbors:
                        edges.append({"source": s, "target": n["target"]})
                svg = VCLSVGRenderer.render_graph_svg(list(nodes), edges)
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": svg}]}}

            elif name == "stats":
                st = self.adapter.semantic.get_stats()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(st)}]}}

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

    def run_stdio(self):
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
