"""Regression coverage for a globally configured MCP serving interleaved workspaces."""
import json
from pathlib import Path

import pytest

from contextos.config import ContextOSConfig, StorageConfig
from contextos.core.daemon_workers import DaemonWorkerPool
from contextos.core.ollama_coprocessor import OllamaCoprocessor
from contextos.hooks.adapter import HookAdapter
from contextos.identity import IdentityScope
from contextos.mcp.server import ContextOSMCPServer


@pytest.fixture
def server(tmp_path, monkeypatch):
    # Keep queued closures available to run after a workspace switch. Tests use
    # real files/SQLite, but neither daemon timing nor external model services.
    monkeypatch.setattr(DaemonWorkerPool, "start_workers", lambda self: None)
    monkeypatch.setattr(OllamaCoprocessor, "is_healthy", lambda self: False)
    launch = tmp_path / "documentation"
    launch.mkdir()
    adapter = HookAdapter(ContextOSConfig(workspace_dir=launch))
    return ContextOSMCPServer(adapter)


def call(server, name, **arguments):
    return server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}})["result"]


def data(result):
    assert not result.get("isError"), result
    return json.loads(result["content"][0]["text"])


def workspace(tmp_path, name):
    path = tmp_path / name
    path.mkdir()
    return str(path)


def record(server, label, **scope):
    return data(call(server, "record", kind="decision",
        payload={"subject": label, "predicate": "uses", "object": label + " value"}, **scope))


def test_prepare_turn_routes_durable_record_and_interleaved_queries(server, tmp_path):
    a = workspace(tmp_path, "mobile workspace")
    b = workspace(tmp_path, "web workspace")
    launch = server.adapter
    data(call(server, "prepare_turn", session_id="mobile", cwd=a, prompt="Mobile context"))
    first = data(call(server, "record", kind="decision", payload={
        "session_id": "mobile", "subject": "mobile-only", "predicate": "uses", "object": "local proof"}))
    data(call(server, "session_start", session_id="web", cwd=b))
    record(server, "web-only", session_id="web")
    for mode in ("search", "state", "timeline", "decisions"):
        rows = data(call(server, "query", session_id="mobile", mode=mode))
        assert [r["assertion_id"] for r in rows] == [first["assertion_id"]]
        assert rows[0]["workspace_id"] == a
        assert rows[0]["origin_session"] == "mobile"
    assert data(call(server, "stats", session_id="mobile"))["total_assertions"] == 1
    assert [r["subject"] for r in data(call(server, "query", cwd=b))] == ["web-only"]
    assert data(call(server, "query")) == []
    assert launch.events.get_events() == []
    assert server.adapter is launch
    assert data(call(server, "expand", id=first["assertion_id"], session_id="mobile", level=1))["payload"]["subject"] == "mobile-only"
    assert data(call(server, "expand", id=first["assertion_id"], session_id="web"))["status"] == "not_found"
    # Binding another session in the same scope reuses the existing worker pool.
    adapters_before = len(server.scopes._adapters)
    data(call(server, "session_start", session_id="mobile-2", cwd=a))
    assert len(server.scopes._adapters) == adapters_before


def test_legacy_launch_calls_and_start_binding_stay_stable(server, tmp_path):
    record(server, "launch")
    assert call(server, "session_start", session_id="legacy")["isError"]
    data(call(server, "session_start", session_id="legacy", cwd=str(server.adapter.config.workspace_dir)))
    record(server, "legacy", session_id="legacy")
    data(call(server, "prepare_turn", session_id="remote", cwd=workspace(tmp_path, "remote")))
    record(server, "remote", session_id="remote")
    assert {r["subject"] for r in data(call(server, "query"))} == {"launch", "legacy"}
    assert {r["subject"] for r in data(call(server, "query", session_id="legacy"))} == {"launch", "legacy"}
    result = call(server, "record", payload={"session_id": "unbound", "subject": "wrong"})
    assert result["isError"] and "Unknown session_id" in result["content"][0]["text"]
    assert data(call(server, "stats"))["total_assertions"] == 2


def test_session_cannot_be_rebound_and_conflicts_do_not_write(server, tmp_path):
    a = workspace(tmp_path, "a")
    b = workspace(tmp_path, "b")
    data(call(server, "session_start", session_id="same", cwd=a))
    for tool in ("prepare_turn", "session_start", "record", "query", "stats", "pre_compact"):
        assert call(server, tool, session_id="same", cwd=b)["isError"]
    for metadata in ({"session_id": "other"}, {"workspace": b}, {"workspace_id": b},
                     {"project": "other"}, {"runtime_id": "claude_code"},
                     {"origin_session": "other"}, {"origin_agent": "other"}):
        assert call(server, "record", session_id="same", payload=metadata)["isError"]
    assert call(server, "record", session_id="same", project_id="other", payload={})["isError"]
    assert not (Path(b) / ".contextos").exists()
    assert data(call(server, "stats", session_id="same"))["total_assertions"] == 0


@pytest.mark.parametrize("cwd", ["relative/path", "", 3, None])
def test_invalid_cwd_fails_before_storage_creation(server, cwd):
    assert call(server, "record", cwd=cwd, payload={})["isError"]
    assert data(call(server, "stats"))["total_assertions"] == 0


def test_missing_directory_and_project_traversal_fail_closed(server, tmp_path):
    missing = str(tmp_path / "does-not-exist")
    assert call(server, "record", cwd=missing, payload={})["isError"]
    assert not Path(missing).exists()
    for project in ("../escape", "/tmp/escape", "..", "", 42):
        assert call(server, "record", cwd=str(tmp_path), project_id=project, payload={})["isError"]


def test_explicit_projects_and_canonical_aliases(server, tmp_path):
    cwd = workspace(tmp_path, "mobile")
    alias = tmp_path / "mobile-alias"
    alias.symlink_to(cwd, target_is_directory=True)
    data(call(server, "session_start", cwd=cwd, project_id="iphone", session_id="one"))
    record(server, "iphone", session_id="one")
    data(call(server, "session_start", cwd=str(alias), project_id="iphone", session_id="one"))
    data(call(server, "session_start", cwd=cwd, project_id="ipad", session_id="two"))
    record(server, "ipad", session_id="two")
    assert [r["subject"] for r in data(call(server, "query", session_id="one"))] == ["iphone"]
    assert [r["subject"] for r in data(call(server, "query", cwd=cwd, project_id="ipad"))] == ["ipad"]
    assert call(server, "record", cwd=cwd, project_id="iphone", payload={"project": "ipad"})["isError"]
    assert data(call(server, "record", session_id="one", payload={"workspace": cwd, "project": "iphone"}))["status"] == "recorded"


def test_initialize_preserves_injected_configuration_and_runtime(server, tmp_path):
    cfg = ContextOSConfig(workspace_dir=tmp_path, workspace_id="custom-workspace", project_id="project",
        client_id="claude_code", storage=StorageConfig(data_dir=Path("custom-data")))
    adapter = HookAdapter(cfg)
    injected = ContextOSMCPServer(adapter)
    response = injected.handle_request({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "Codex"}}})
    assert "result" in response
    assert injected.adapter is adapter
    record(injected, "custom")
    row = data(call(injected, "query"))[0]
    assert (row["runtime_id"], row["producer_runtime"], row["origin_runtime"]) == ("claude_code",) * 3
    assert row["workspace_id"] == "custom-workspace" and row["project_id"] == "project"
    assert "custom-data" in str(adapter.semantic.db_path)


def test_initialize_detects_runtime_without_losing_launch_configuration(server, tmp_path, monkeypatch):
    original = ContextOSConfig.load.__func__
    cfg = ContextOSConfig(workspace_dir=tmp_path, project_id="launch-project")
    monkeypatch.setattr(ContextOSConfig, "load", classmethod(
        lambda cls, workspace_dir=None, **kw: original(cls, workspace_dir=workspace_dir, **kw)
        if workspace_dir is not None else cfg))
    detected = ContextOSMCPServer()
    request = {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "Antigravity"}}}
    assert "result" in detected.handle_request(request)
    record(detected, "runtime")
    row = data(call(detected, "query"))[0]
    assert row["runtime_id"] == "antigravity" and row["project_id"] == "launch-project"
    assert detected.adapter.config.workspace_dir == tmp_path
    assert "error" in detected.handle_request({**request, "params": {"clientInfo": {"name": "Codex"}}})


def test_all_reads_filter_foreign_rows_in_same_physical_store(server):
    adapter = server.adapter
    identity = IdentityScope.from_config(adapter.config, "default")
    for index, altered in enumerate(({}, {"runtime_id": "other"}, {"workspace_id": "other"},
                                      {"project_id": "other"}, {"origin_session": "other", "scope": "session"})):
        attrs = {"runtime_id": identity.runtime_id, "workspace_id": identity.workspace_id,
            "project_id": identity.project_id, "origin_session": identity.session_id, **altered}
        for kind, status in (("decision", "current"), ("constraint", "current"), ("question", "current"),
                             ("fact", "conflict"), ("decision", "rejected")):
            adapter.semantic.add_assertion(f"{index}-{kind}-{status}", "shared-label", "value", str(index),
                kind=kind, status=status, **attrs)
    for mode in ("search", "state", "timeline", "decisions", "constraints", "questions"):
        rows = data(call(server, "query", mode=mode))
        assert rows and all(r["object"] == "0" for r in rows)
    conflicts = data(call(server, "query", mode="conflicts"))
    assert all(r["object"] == "0" for r in conflicts["conflicts"] + conflicts["closed_branches"])
    expanded = data(call(server, "expand", id="shared-label", level=3))
    assert all(r["object"] == "0" for r in expanded["payload"]["assertions"])
    assert all(r["object"] == "0" for r in expanded["payload"]["known_conflicts"])
    assert data(call(server, "stats"))["total_assertions"] == 5


def test_sources_capsules_and_visual_use_request_adapter(server, tmp_path):
    a = workspace(tmp_path, "a")
    b = workspace(tmp_path, "b")
    data(call(server, "session_start", cwd=a, session_id="a"))
    data(call(server, "session_start", cwd=b, session_id="b"))
    aa, ia = server.scopes.resolve("query", {"session_id": "a"})
    bb, ib = server.scopes.resolve("query", {"session_id": "b"})
    for adapter, identity, label in ((aa, ia, "A"), (bb, ib, "B")):
        sid = adapter.sources.put_source(label + " evidence", source_id="same-source", identity=identity)
        adapter.semantic.add_assertion("same-assertion", "same-entity", "uses", label, source_ref=sid,
            runtime_id=identity.runtime_id, workspace_id=identity.workspace_id, project_id=identity.project_id)
        adapter.graph.add_node(label, label + " graph")
    assert data(call(server, "source", source_ids=["same-source"], session_id="a"))["same-source"]["content"] == "A evidence"
    assert data(call(server, "expand", id="same-entity", level=4, session_id="b"))["payload"]["sources"]["same-source"]["content"] == "B evidence"
    assert "A graph" in call(server, "visual", session_id="a")["content"][0]["text"]
    assert "A graph" not in call(server, "visual", session_id="b")["content"][0]["text"]
    foreign = IdentityScope(ia.runtime_id, "foreign", ia.project_id, ia.session_id)
    aa.shared_sources.put_source("wrong scope", source_id="foreign", identity=foreign)
    assert data(call(server, "source", source_ids=["foreign"], session_id="a")) == {}
    assert data(call(server, "source", source_ids=["same-source"], session_id="a", agent_id="other")) == {}


def test_lifecycle_hooks_keep_bound_store_and_goal_after_interleaving(server, tmp_path):
    a = workspace(tmp_path, "a")
    b = workspace(tmp_path, "b")
    data(call(server, "prepare_turn", cwd=a, session_id="a", prompt="/goal Finish A criteria: 1. Tests pass"))
    data(call(server, "prepare_turn", cwd=b, session_id="b", prompt="/goal Finish B criteria: 1. Manual acceptance"))
    assert "Finish A" in call(server, "session_start", session_id="a")["additionalContext"]
    assert call(server, "stop_eval", session_id="b")["decision"] == "block"
    call(server, "post_tool_use", session_id="a", tool_name="pytest", tool_output="1 passed in 0.01s")
    assert "Finish B" in call(server, "post_compact", session_id="b")["additionalContext"]
    assert "Finish A" not in call(server, "post_compact", session_id="b")["additionalContext"]
    snapshot = data(call(server, "pre_compact", session_id="a"))["snapshot_id"]
    assert snapshot in data(call(server, "source", source_ids=[snapshot], session_id="a"))
    assert data(call(server, "source", source_ids=[snapshot], session_id="b")) == {}
    goal = data(call(server, "session_start", session_id="a"))["active_goal"]
    assert goal["goal_id"] in call(server, "subagent_start", session_id="a", role="reviewer")["additionalContext"]
    data(call(server, "subagent_stop", session_id="a", role="reviewer", result_text="A reviewed"))
    assert "decision" not in call(server, "stop_eval", session_id="a", final_text="A complete")
    # Execute queued ingestion after all the interleaving; closures retain scope.
    for adapter in server.scopes._adapters.values():
        queue = adapter.worker_pool.p1_ingest_queue
        while not queue.empty():
            queue.get_nowait()()
            queue.task_done()
    aa, _ = server.scopes.resolve("query", {"session_id": "a"})
    bb, _ = server.scopes.resolve("query", {"session_id": "b"})
    assert all(e["workspace_id"] == a and e["session_id"] == "a" for e in aa.events.get_events())
    assert all(e["workspace_id"] == b and e["session_id"] == "b" for e in bb.events.get_events())
    assert {e["type"] for e in aa.events.get_events()} >= {"UserPromptSubmit", "SessionStart", "PostToolUse", "PreCompact", "SubagentStart", "SubagentStop", "Stop"}
    assert server.adapter.events.get_events() == []


def test_live_tool_schema_and_artifact_expose_same_scope_contract(server):
    tools = server.handle_request({"method": "tools/list"})["result"]["tools"]
    schema = Path(__file__).parents[2] / "schemas" / "mcp_tools.schema.json"
    assert tools == json.loads(schema.read_text())["tools"]
    for tool in tools:
        assert set(tool["inputSchema"]["properties"]) >= {"cwd", "project_id", "session_id"}


def test_implicit_start_does_not_poison_first_explicit_workspace(server, tmp_path):
    record(server, "private-launch-context")
    initial = call(server, "session_start", session_id="mobile-session")
    assert initial["isError"] and "additionalContext" not in initial
    assert server.adapter.events.get_events() == []
    cwd = workspace(tmp_path, "actual-mobile")
    prepared = call(server, "prepare_turn", session_id="mobile-session", cwd=cwd, prompt="private-launch-context")
    assert "private-launch-context" not in prepared["additionalContext"]
    record(server, "mobile-context", session_id="mobile-session")
    assert [r["subject"] for r in data(call(server, "query", session_id="mobile-session"))] == ["mobile-context"]


def test_agent_identity_applies_to_hydration_compaction_goals_and_sources(server, tmp_path):
    cwd = workspace(tmp_path, "agents")
    data(call(server, "session_start", cwd=cwd, session_id="agents"))
    adapter, base = server.scopes.resolve("query", {"session_id": "agents"})
    for agent in ("main", "child"):
        identity = IdentityScope(base.runtime_id, base.workspace_id, base.project_id, base.session_id, agent)
        adapter.semantic.add_assertion(agent, agent + "-secret", "requires", agent + "-only", kind="constraint",
            scope="session", runtime_id=identity.runtime_id, workspace_id=identity.workspace_id,
            project_id=identity.project_id, origin_session=identity.session_id, origin_agent=agent)
        adapter.goals.set_active_goal(agent + "-goal", acceptance_criteria=["Tests pass"], **identity.as_dict())
    prepared = call(server, "prepare_turn", session_id="agents", agent_id="child", prompt="constraints")
    assert "child-secret" in prepared["additionalContext"]
    assert "main-secret" not in prepared["additionalContext"] and "main-goal" not in prepared["additionalContext"]
    hydrated = call(server, "session_start", session_id="agents", agent_id="child")
    assert "Project State Assertions: 1" in hydrated["additionalContext"]
    assert "Pinned Invariants: 1" in hydrated["additionalContext"]
    assert "child-goal" in hydrated["additionalContext"] and "main-goal" not in hydrated["additionalContext"]
    snapshot = data(call(server, "pre_compact", session_id="agents", agent_id="child"))["snapshot_id"]
    assert data(call(server, "source", session_id="agents", agent_id="main", source_ids=[snapshot])) == {}
    content = data(call(server, "source", session_id="agents", agent_id="child", source_ids=[snapshot]))[snapshot]["content"]
    assert "child-secret" in content and "main-secret" not in content
    compacted = call(server, "post_compact", session_id="agents", agent_id="child")["additionalContext"]
    assert "child-only" in compacted and "main-only" not in compacted
    call(server, "post_tool_use", session_id="agents", agent_id="child", tool_name="pytest", tool_output="1 passed in 0.01s")
    assert "decision" not in call(server, "stop_eval", session_id="agents", agent_id="child")
    assert call(server, "stop_eval", session_id="agents", agent_id="main")["decision"] == "block"
    events = adapter.events.get_events()
    assert events[-1]["agent_id"] == "child"


def test_new_workspace_uses_its_configured_project_not_launch_project(server, tmp_path, monkeypatch):
    monkeypatch.delenv("CONTEXTOS_PROJECT_ID", raising=False)
    launch_config = ContextOSConfig(workspace_dir=server.adapter.config.workspace_dir, project_id="launch")
    configured = ContextOSMCPServer(HookAdapter(launch_config))
    cwd = workspace(tmp_path, "configured-target")
    config_dir = Path(cwd) / ".contextos"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("project_id: target-project\nworkspace_id: target-identity\n")
    data(call(configured, "session_start", cwd=cwd, session_id="configured"))
    record(configured, "target", session_id="configured")
    row = data(call(configured, "query", session_id="configured"))[0]
    assert row["project_id"] == "target-project" and row["workspace_id"] == "target-identity"
    assert data(call(configured, "query", cwd=cwd, project_id="launch")) == []
    record(configured, "explicit", cwd=cwd, project_id="explicit")
    assert data(call(configured, "query", cwd=cwd, project_id="explicit"))[0]["project_id"] == "explicit"


def test_runtime_cannot_change_after_explicit_request_before_initialize(server, tmp_path, monkeypatch):
    monkeypatch.setattr(ContextOSConfig, "load", classmethod(lambda cls, **kw: ContextOSConfig(workspace_dir=tmp_path)))
    uninitialized = ContextOSMCPServer()
    record(uninitialized, "before-handshake")
    response = uninitialized.handle_request({"method": "initialize", "params": {"clientInfo": {"name": "Claude"}}})
    assert "error" in response
    assert data(call(uninitialized, "query"))[0]["subject"] == "before-handshake"


@pytest.mark.parametrize("field", ["session_id", "agent_id", "project_id"])
def test_null_scope_fields_cannot_fall_back_to_launch_store(server, field):
    assert call(server, "record", payload={}, **{field: None})["isError"]
    assert data(call(server, "stats"))["total_assertions"] == 0
