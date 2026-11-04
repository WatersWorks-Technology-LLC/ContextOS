"""Regression: JSON-file stores must not lose updates across instances/processes
and must not wipe a corrupt file silently."""
import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_source_store_two_instances_do_not_lose_updates(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") and fresh.get_source("B")
    assert a.get_source("B") is not None  # writer sees peer's data after refresh


def test_vector_index_two_instances_do_not_lose_updates(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "hello world")
    b.add_document("d2", "goodbye world")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_two_instances_do_not_lose_updates(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    c1 = a.create_commit("one", [], [], "s", identity=ID)
    c2 = b.create_commit("two", [], [], "s", identity=ID)
    assert set(ContextVersionStore(tmp_path).versions) == {c1["commit_id"], c2["commit_id"]}


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json", encoding="utf-8")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=ID)
    assert list(tmp_path.glob("sources.json.corrupt-*")), "corrupt data must be kept"
    assert "X" in json.loads((tmp_path / "sources.json").read_text())
