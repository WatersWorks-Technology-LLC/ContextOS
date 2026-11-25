"""RequestScopes must not grow its session map without bound."""
from contextos.config import ContextOSConfig
from contextos.core.daemon_workers import DaemonWorkerPool
from contextos.core.ollama_coprocessor import OllamaCoprocessor
from contextos.hooks.adapter import HookAdapter
from contextos.mcp.scope import RequestScopes


def test_session_map_is_bounded_and_keeps_recent(tmp_path, monkeypatch):
    monkeypatch.setattr(DaemonWorkerPool, "start_workers", lambda self: None)
    monkeypatch.setattr(OllamaCoprocessor, "is_healthy", lambda self: False)
    ws = tmp_path / "ws"
    ws.mkdir()
    scopes = RequestScopes(HookAdapter(ContextOSConfig(workspace_dir=ws)))
    cap = RequestScopes.MAX_SESSIONS
    for i in range(cap + 50):
        scopes.resolve("session_start", {"session_id": f"s{i}", "cwd": str(ws)})
    assert len(scopes._sessions) == cap
    assert f"s{cap + 49}" in scopes._sessions
    assert "s0" not in scopes._sessions
