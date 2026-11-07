"""Regression tests: JSON-backed stores must not lose data across instances/processes or on corruption."""
import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_source_store_concurrent_instances_do_not_lose_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # both loaded before either writes
    sa = a.put_source("alpha", identity=ID)
    sb = b.put_source("beta", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sa) and fresh.get_source(sb)


def test_vector_index_concurrent_instances_do_not_lose_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha")
    b.add_document("d2", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_concurrent_instances_do_not_lose_writes(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    c1 = a.create_commit("one", [], [], "s", identity=ID)["commit_id"]
    c2 = b.create_commit("two", [], [], "s", identity=ID)["commit_id"]
    assert set(ContextVersionStore(tmp_path).versions) == {c1, c2}


def test_corrupt_store_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text('{"SRC-x": {"content": "precious"', encoding="utf-8")  # truncated
    s = SourceStore(tmp_path)
    s.put_source("new", identity=ID)
    backups = list(tmp_path.glob("sources.json.corrupt*"))
    assert backups and "precious" in backups[0].read_text(encoding="utf-8")


def test_save_is_atomic_no_temp_leftovers(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=ID)
    assert json.loads((tmp_path / "sources.json").read_text())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["sources.json", "sources.json.lock"]
