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
    """Two processes/instances sharing one file must merge, not clobber."""
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    a, b = SourceStore(tmp_dir), SourceStore(tmp_dir)
    sa = a.put_source("from A", identity=identity)
    sb = b.put_source("from B", identity=identity)
    fresh = SourceStore(tmp_dir)
    assert fresh.get_source(sa) and fresh.get_source(sb)


def test_vector_index_concurrent_instances_do_not_lose_writes(tmp_dir):
    a, b = VectorIndex(tmp_dir), VectorIndex(tmp_dir)
    a.add_document("d1", "alpha text")
    b.add_document("d2", "beta text")
    assert set(VectorIndex(tmp_dir).documents) == {"d1", "d2"}


def test_version_store_concurrent_instances_do_not_lose_writes(tmp_dir):
    from contextos.storage.versioning import ContextVersionStore
    identity = IdentityScope("codex", "workspace", "project", "s1", "main")
    a, b = ContextVersionStore(tmp_dir), ContextVersionStore(tmp_dir)
    a.create_commit("ctx A", [], [], "s", identity=identity)
    b.create_commit("ctx B", [], [], "s", identity=identity)
    assert len(ContextVersionStore(tmp_dir).versions) == 2


def test_json_stores_leave_no_temp_files(tmp_dir):
    SourceStore(tmp_dir).put_source("x", identity=IdentityScope("c", "w", "p", "s", "m"))
    assert not list(tmp_dir.glob("*.tmp"))
