from contextos.core.shadow_experimenter import CounterfactualReplayEngine
from contextos.identity import IdentityScope
from contextos.storage.event_store import EventStore

IDENTITY = IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="main")
SECRETS = ["sk-abcdef0123456789abcdef", "hunter2hunter2", "ghp_0123456789abcdefghijklmnop", "AKIAABCDEFGHIJKLMNOP"]


def test_event_payload_secrets_not_persisted(tmp_path):
    store = EventStore(tmp_path)
    store.append_event("UserPromptSubmit", {
        "prompt": "use key sk-abcdef0123456789abcdef and password=hunter2hunter2 on AKIAABCDEFGHIJKLMNOP",
        "env": {"GITHUB_TOKEN": "ghp_0123456789abcdefghijklmnop"},
        "cwd": "/repo"}, identity=IDENTITY)
    raw = store.file_path.read_text()
    for secret in SECRETS:
        assert secret not in raw
    assert store.get_events()[0]["payload"]["cwd"] == "/repo"


def test_episode_secrets_not_persisted(tmp_path):
    engine = CounterfactualReplayEngine(tmp_path)
    engine.record_episode("t1", "token: sk-abcdef0123456789abcdef", [], [], "ok", identity=IDENTITY)
    assert "sk-abcdef0123456789abcdef" not in engine.file_path.read_text()
