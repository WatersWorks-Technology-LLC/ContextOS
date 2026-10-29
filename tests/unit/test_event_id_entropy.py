import tempfile
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.event_store import EventStore


def test_event_ids_have_collision_resistant_length():
    with tempfile.TemporaryDirectory() as d:
        store = EventStore(Path(d))
        identity = IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="main")
        evt = store.append_event("note", {"x": 1}, identity=identity)
        assert len(evt["event_id"].removeprefix("EVT-")) >= 32
