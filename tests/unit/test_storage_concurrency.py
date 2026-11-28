"""Regression: JSON-backed stores must not lose records written by another process/instance."""
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_keeps_other_instance_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    sa = a.put_source("alpha", identity=ID)
    sb = b.put_source("beta", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sa) and fresh.get_source(sb)


def test_vector_index_keeps_other_instance_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha text")
    b.add_document("d2", "beta text")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_keeps_other_instance_writes(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx one", [], [], "s", identity=ID)["commit_id"]
    cb = b.create_commit("ctx two", [], [], "s", identity=ID)["commit_id"]
    fresh = ContextVersionStore(tmp_path)
    assert fresh.get_commit(ca) and fresh.get_commit(cb)


def test_save_is_atomic_no_tmp_left(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=ID)
    assert not list(tmp_path.glob("*.tmp"))
