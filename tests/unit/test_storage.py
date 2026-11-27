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


def test_promote_assertion_works(tmp_path):
    from contextos.storage.semantic_store import SemanticStore
    st = SemanticStore(tmp_path)
    st.add_assertion("A1", "s", "p", "o", scope="session")
    pid = st.promote_assertion("A1", "project")
    assert pid and pid.startswith("AST-PROM-")


def test_source_store_multi_instance_no_lost_updates(tmp_path):
    from contextos.identity import IdentityScope
    from contextos.storage.source_store import SourceStore
    ident = IdentityScope("codex", "w", "p", "s")
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # two "processes"
    a.put_source("one", source_id="A", identity=ident)
    b.put_source("two", source_id="B", identity=ident)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") and fresh.get_source("B")
    assert a.get_source("B")  # sees other writer


def test_source_store_corrupt_file_preserved(tmp_path):
    from contextos.identity import IdentityScope
    from contextos.storage.source_store import SourceStore
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=IdentityScope("c", "w", "p", "s"))
    assert list(tmp_path.glob("sources.json.corrupt-*"))
