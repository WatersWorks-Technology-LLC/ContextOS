import sys
import json
import uuid
from typing import Dict, Any
from ..hooks.adapter import HookAdapter
from ..core.capsules import ContextCapsuleManager
from ..codecs.vcl_svg import VCLSVGRenderer
from .scope import RequestScopes, ScopeError
from .tool_definitions import TOOLS

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
        self._injected_adapter = adapter is not None
        self._initialized = False
        self.scopes = RequestScopes(self.adapter)

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
            elif "codex" in cname:
                client_id = "codex"
            else:
                client_id = self.adapter.config.client_id

            # An injected adapter is an explicit configuration contract. Initialization
            # must not replace it with an adapter rooted in the process directory.
            if not self._injected_adapter and client_id != self.adapter.config.client_id:
                if self._initialized or self.scopes.has_requests:
                    return {"jsonrpc": "2.0", "id": req_id, "error": {
                        "code": -32602, "message": "Cannot change runtime identity after initialization or tool use"}}
                cfg = self.adapter.config.model_copy(deep=True, update={"client_id": client_id})
                self.adapter.worker_pool.stop_workers()
                self.adapter = HookAdapter(config=cfg)
                self.scopes = RequestScopes(self.adapter)
            self._initialized = True

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
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            if name not in {tool["name"] for tool in TOOLS}:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown tool"}}
            try:
                adapter, identity = self.scopes.resolve(name, args)
            except ScopeError as exc:
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "isError": True, "content": [{"type": "text", "text": str(exc)}]}}
            response = self._call_tool(req_id, name, args, adapter, identity)
            response["result"]["_meta"] = {"contextos": {
                "identity": identity.as_dict(), "cwd": str(adapter.config.workspace_dir.resolve())}}
            return response

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

    def _call_tool(self, req_id, name, args, adapter, identity):
        if name == "prepare_turn":
            prompt_text = args.get("prompt", "")
            sess_id = identity.session_id
            cwd_val = str(adapter.config.workspace_dir.resolve())
            res = adapter.on_user_prompt_submit(
                prompt_text,
                session_id=sess_id,
                cwd=cwd_val,
                agent_id=identity.agent_id
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
            sess_id = identity.session_id
            res = adapter.on_session_start(session_id=sess_id, agent_id=identity.agent_id)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

        elif name == "post_tool_use":
            tname = args.get("tool_name", "tool")
            tinput = args.get("tool_input", {})
            toutput = args.get("tool_output", "")
            sess_id = identity.session_id
            res = adapter.on_post_tool_use(tname, tinput, toutput, session_id=sess_id, agent_id=identity.agent_id)
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
            sess_id = identity.session_id
            res = adapter.on_pre_compact(session_id=sess_id, agent_id=identity.agent_id)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res)}]}}

        elif name == "post_compact":
            sess_id = identity.session_id
            res = adapter.on_post_compact(session_id=sess_id, agent_id=identity.agent_id)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

        elif name == "subagent_start":
            role = args.get("role", "subagent")
            prompt_txt = args.get("prompt", "")
            sess_id = identity.session_id
            res = adapter.on_subagent_start(role, prompt_txt, session_id=sess_id, parent_agent_id=identity.agent_id)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"hookSpecificOutput": {"additionalContext": res["additionalContext"]}, "additionalContext": res["additionalContext"], "content": [{"type": "text", "text": json.dumps(res)}]}}

        elif name == "subagent_stop":
            role = args.get("role", "subagent")
            result_txt = args.get("result_text", "")
            sess_id = identity.session_id
            adapter.on_subagent_stop(role, result_txt, session_id=sess_id, agent_id=identity.agent_id)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "recorded"})}]}}

        elif name == "stop_eval":
            final_txt = args.get("final_text", "")
            sess_id = identity.session_id
            res = adapter.on_stop(final_txt, session_id=sess_id, agent_id=identity.agent_id)

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
                results = adapter.semantic.query_current_state(kind="decision", identity=identity)
            elif mode == "constraints":
                results = adapter.semantic.query_current_state(kind="constraint", identity=identity)
            elif mode == "conflicts":
                results = adapter.semantic.query_conflicts_and_closed_branches(identity=identity)
            elif mode in ("state", "questions"):
                results = adapter.semantic.query_current_state(
                    kind="question" if mode == "questions" else None, identity=identity)
            else:
                results = adapter.semantic.search_assertions(kw, identity=identity)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(results)}]}}

        elif name == "expand":
            item_id = args.get("id")
            level = args.get("level", 3)
            expanded = ContextCapsuleManager(adapter.semantic, adapter.sources).expand(
                item_id, level=level, identity=identity)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(expanded)}]}}

        elif name == "source":
            sids = args.get("source_ids", [])
            max_chars = args.get("max_chars", 12000)
            sources = adapter.sources.get_sources(sids, max_chars=max_chars, identity=identity, allow_legacy=False)
            shared = adapter.shared_sources.get_sources(sids, max_chars=max_chars, identity=identity, allow_legacy=False)
            sources.update(shared)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(sources)}]}}

        elif name == "record":
            kind = args.get("kind", "fact")
            payload = args.get("payload", {})
            aid = f"AST-{uuid.uuid4().hex[:8]}"
            adapter.semantic.add_assertion(
                aid,
                subject=payload.get("subject", "system"),
                predicate=payload.get("predicate", "defined"),
                object_val=payload.get("object", str(payload)),
                kind=kind,
                decision_rationale=payload.get("rationale"),
                runtime_id=identity.runtime_id,
                producer_runtime=identity.runtime_id,
                workspace_id=identity.workspace_id,
                project_id=identity.project_id,
                origin_session=identity.session_id,
                origin_agent=identity.agent_id,
                origin_turn=payload.get("turn_id"),
                identity_confidence="observed"
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "recorded", "assertion_id": aid})}]}}

        elif name == "visual":
            nodes = adapter.graph.nodes.values()
            edges = []
            for s, neighbors in adapter.graph.adjacency.items():
                for n in neighbors:
                    edges.append({"source": s, "target": n["target"]})
            svg = VCLSVGRenderer.render_graph_svg(list(nodes), edges)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": svg}]}}

        elif name == "stats":
            st = adapter.semantic.get_stats(identity=identity)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(st)}]}}

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
