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


def test_unit_semantic_store_promote_assertion_preserves_origin(tmp_dir):
    sem = SemanticStore(tmp_dir)
    sem.add_assertion("A1", "Auth", "uses", "JWT", scope="session",
                      runtime_id="codex", workspace_id="ws", project_id="proj",
                      origin_session="s1", origin_agent="main", decision_rationale="why")
    promoted_id = sem.promote_assertion("A1", "project")
    assert promoted_id and promoted_id.startswith("AST-PROM-")
    promoted = next(a for a in sem.query_current_state(runtime_id=None) if a["assertion_id"] == promoted_id)
    assert promoted["scope"] == "project"
    assert promoted["origin_assertion_id"] == "A1"
    assert (promoted["origin_session"], promoted["origin_agent"]) == ("s1", "main")
    assert (promoted["workspace_id"], promoted["project_id"]) == ("ws", "proj")
    assert sem.promote_assertion("missing", "project") is None
    assert sem.promote_assertion("A1", "bogus") is None
