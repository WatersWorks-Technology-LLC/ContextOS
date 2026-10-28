"""Stores must not lose records written by another process/instance."""
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_keeps_other_instance_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    assert set(SourceStore(tmp_path)._sources) == {"A", "B"}


def test_vector_index_keeps_other_instance_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha")
    b.add_document("B", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"A", "B"}


def test_version_store_keeps_other_instance_writes(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("one", [], [], "s", identity=ID)
    cb = b.create_commit("two", [], [], "s", identity=ID)
    assert set(ContextVersionStore(tmp_path).versions) == {ca["commit_id"], cb["commit_id"]}
