import io
import json
import logging
import sys
import tempfile
from pathlib import Path

from contextos.config import ContextOSConfig
from contextos.hooks.adapter import HookAdapter
from contextos.mcp.server import ContextOSMCPServer


def _run(server, lines, monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n".join(lines) + "\n"))
    monkeypatch.setattr(sys, "stdout", out)
    server.run_stdio()
    return [json.loads(l) for l in out.getvalue().splitlines()]


def test_stdio_internal_error_echoes_request_id_and_logs(monkeypatch, caplog):
    with tempfile.TemporaryDirectory() as td:
        server = ContextOSMCPServer(adapter=HookAdapter(config=ContextOSConfig(workspace_dir=Path(td))))
        # params is not an object -> handler raises internally
        bad = json.dumps({"jsonrpc": "2.0", "id": 42, "method": "initialize", "params": []})
        with caplog.at_level(logging.ERROR):
            resp = _run(server, [bad], monkeypatch)
        assert resp[0]["id"] == 42, "JSON-RPC error must echo the request id"
        assert resp[0]["error"]["code"] == -32603
        assert any("Traceback" in (r.exc_text or "") or r.exc_info for r in caplog.records)


def test_stdio_unparseable_line_gets_parse_error_with_null_id(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        server = ContextOSMCPServer(adapter=HookAdapter(config=ContextOSConfig(workspace_dir=Path(td))))
        resp = _run(server, ["{not json"], monkeypatch)
        assert resp[0]["id"] is None
        assert resp[0]["error"]["code"] == -32700
