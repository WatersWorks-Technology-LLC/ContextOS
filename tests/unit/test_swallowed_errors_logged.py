import logging

from contextos.config import ContextOSConfig
from contextos.identity import IdentityScope
from contextos.storage.event_store import EventStore


def test_invalid_config_yaml_is_logged_not_silent(tmp_path, caplog):
    (tmp_path / ".contextos").mkdir()
    (tmp_path / ".contextos" / "config.yaml").write_text("project_id: [unclosed\n")
    with caplog.at_level(logging.WARNING):
        cfg = ContextOSConfig.load(workspace_dir=tmp_path)
    assert cfg.project_id == "default"
    assert any("config.yaml" in r.getMessage() for r in caplog.records)


def test_corrupt_event_line_is_logged(tmp_path, caplog):
    store = EventStore(tmp_path)
    identity = IdentityScope(runtime_id="codex", workspace_id="w", project_id="p",
                             session_id="s", agent_id="main")
    store.append_event("t", {"a": 1}, identity=identity)
    with open(store.file_path, "a", encoding="utf-8") as f:
        f.write("{not json\n")
    with caplog.at_level(logging.WARNING):
        events = store.get_events()
    assert len(events) == 1
    assert any("events.jsonl" in r.getMessage() for r in caplog.records)
