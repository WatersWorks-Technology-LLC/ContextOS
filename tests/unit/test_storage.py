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


def test_bugsweep_json_stores_do_not_lose_concurrent_writes(tmp_dir):
    """Two store instances (e.g. two processes) on one dir must not clobber each other."""
    from contextos.storage.versioning import ContextVersionStore
    ident = IdentityScope("codex", "workspace", "project", "s1", "main")
    a, b = SourceStore(tmp_dir), SourceStore(tmp_dir)
    sa = a.put_source("alpha", identity=ident)
    sb = b.put_source("beta", identity=ident)
    fresh = SourceStore(tmp_dir)
    assert fresh.get_source(sa) and fresh.get_source(sb)

    va, vb = VectorIndex(tmp_dir), VectorIndex(tmp_dir)
    va.add_document("d1", "alpha text")
    vb.add_document("d2", "beta text")
    assert set(VectorIndex(tmp_dir).documents) == {"d1", "d2"}

    ca, cb = ContextVersionStore(tmp_dir), ContextVersionStore(tmp_dir)
    c1 = ca.create_commit("ctx one", [], [], "s", identity=ident)["commit_id"]
    c2 = cb.create_commit("ctx two", [], [], "s", identity=ident)["commit_id"]
    assert {c1, c2} <= set(ContextVersionStore(tmp_dir).versions)


def test_bugsweep_corrupt_json_store_is_preserved_not_overwritten(tmp_dir):
    ident = IdentityScope("codex", "workspace", "project", "s1", "main")
    (tmp_dir / "sources.json").write_text('{"SRC-x": {"content": "precious"', encoding="utf-8")
    ss = SourceStore(tmp_dir)
    ss.put_source("new", identity=ident)
    assert list(tmp_dir.glob("sources.json.corrupt-*")), "corrupt file must be kept for recovery"
