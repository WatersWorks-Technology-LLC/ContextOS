import pytest
import json
import tempfile
from pathlib import Path
from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter
from contextos.mcp.server import ContextOSMCPServer

@pytest.fixture
def mcp_server():
    with tempfile.TemporaryDirectory() as td:
        cfg = ContextOSConfig(workspace_dir=Path(td))
        adapter = HookAdapter(config=cfg)
        yield ContextOSMCPServer(adapter=adapter)

def test_integration_mcp_tools_list(mcp_server):
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    resp = mcp_server.handle_request(req)
    assert resp["id"] == 1
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "prepare_turn" in tool_names
    assert "query" in tool_names
    assert "expand" in tool_names
    assert "source" in tool_names
    assert "record" in tool_names
    assert "visual" in tool_names

def test_integration_mcp_record_query_visual(mcp_server):
    rec_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "record",
            "arguments": {
                "kind": "decision",
                "payload": {"subject": "Database", "predicate": "uses", "object": "Postgres", "rationale": "ACID compliance"}
            }
        }
    }
    rec_resp = mcp_server.handle_request(rec_req)
    assert rec_resp["id"] == 2

    # Query
    query_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "query",
            "arguments": {"query": "Database", "mode": "decisions"}
        }
    }
    query_resp = mcp_server.handle_request(query_req)
    text_res = query_resp["result"]["content"][0]["text"]
    data = json.loads(text_res)
    assert len(data) >= 1
    assert data[0]["subject"] == "Database"

    # Visual SVG
    vis_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "visual", "arguments": {}}
    }
    vis_resp = mcp_server.handle_request(vis_req)
    svg_text = vis_resp["result"]["content"][0]["text"]
    assert "<svg" in svg_text
