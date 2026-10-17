import pytest
import tempfile
from pathlib import Path
from contextos.storage.event_store import EventStore
from contextos.storage.source_store import SourceStore
from contextos.storage.semantic_store import SemanticStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.knowledge_graph import KnowledgeGraph
from contextos.identity import IdentityScope

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_unit_event_store(tmp_dir):
    es = EventStore(tmp_dir)
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    evt = es.append_event("TestEvent", {"key": "val"}, session_id="s1", identity=identity)
    assert evt["event_id"].startswith("EVT-")
    assert len(es.get_events()) == 1

def test_unit_source_store(tmp_dir):
    ss = SourceStore(tmp_dir)
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    sid = ss.put_source("Evidence body", identity=identity)
    assert sid.startswith("SRC-")
    assert ss.get_source(sid)["content"] == "Evidence body"

def test_unit_semantic_store_temporal(tmp_dir):
    sem = SemanticStore(tmp_dir)
    aid = sem.add_assertion("A1", "Auth", "uses", "JWT", kind="decision")
    assert aid == "A1"
    
    current = sem.query_current_state()
    assert len(current) == 1
    assert current[0]["observed_at"] is not None

    # Test closed branch memoization
    sem.record_closed_branch("D14", "SessionTokens", "Security vulnerability", "reopen_if_patch_available")
    cb = sem.query_conflicts_and_closed_branches()
    assert len(cb["closed_branches"]) == 1


def test_source_store_concurrent_instances_do_not_lose_writes(tmp_dir):
    """Two processes (modelled as two instances) sharing one file must keep each other's sources."""
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    a = SourceStore(tmp_dir)
    b = SourceStore(tmp_dir)
    sid_a = a.put_source("from A", identity=identity)
    sid_b = b.put_source("from B", identity=identity)
    fresh = SourceStore(tmp_dir)
    assert fresh.get_source(sid_a) is not None
    assert fresh.get_source(sid_b) is not None


def test_source_store_corrupt_file_is_not_silently_overwritten(tmp_dir):
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    path = tmp_dir / "sources.json"
    path.write_text("{ not json")
    ss = SourceStore(tmp_dir)
    ss.put_source("new", identity=identity)
    backups = list(tmp_dir.glob("sources.json.corrupt*"))
    assert backups and backups[0].read_text() == "{ not json"
