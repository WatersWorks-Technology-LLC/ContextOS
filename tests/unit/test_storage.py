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
    """Two processes sharing one sources file must not overwrite each other's entries."""
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    a, b = SourceStore(tmp_dir), SourceStore(tmp_dir)
    a.put_source("from a", source_id="A", identity=identity)
    b.put_source("from b", source_id="B", identity=identity)
    fresh = SourceStore(tmp_dir)
    assert fresh.get_source("A") is not None
    assert fresh.get_source("B") is not None


def test_vector_index_concurrent_instances_do_not_lose_writes(tmp_dir):
    a, b = VectorIndex(tmp_dir), VectorIndex(tmp_dir)
    a.add_document("A", "alpha content")
    b.add_document("B", "beta content")
    fresh = VectorIndex(tmp_dir)
    assert set(fresh.documents) == {"A", "B"}


def test_source_store_save_is_atomic(tmp_dir, monkeypatch):
    """A failed write must leave the previous file intact, not truncated."""
    import json as _json
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    ss = SourceStore(tmp_dir)
    ss.put_source("keep me", source_id="K", identity=identity)

    def boom(*args, **kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(_json, "dump", boom)
    with pytest.raises(OSError):
        ss.put_source("new", source_id="N", identity=identity)
    monkeypatch.undo()
    assert SourceStore(tmp_dir).get_source("K") is not None
