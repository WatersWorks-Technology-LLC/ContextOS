"""Regression tests: JSON-backed stores must not lose updates across instances/processes."""
import json
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "workspace", "project", "s1", "main")


def test_source_store_two_instances_do_not_lose_updates(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    sa = a.put_source("alpha", identity=ID)
    sb = b.put_source("beta", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sa) and fresh.get_source(sb)


def test_vector_index_two_instances_do_not_lose_updates(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha text")
    b.add_document("d2", "beta text")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_two_instances_do_not_lose_updates(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx a", [], [], "s", identity=ID)["commit_id"]
    cb = b.create_commit("ctx b", [], [], "s", identity=ID)["commit_id"]
    assert set(ContextVersionStore(tmp_path).versions) == {ca, cb}


def test_save_is_atomic_no_partial_file_or_temp_leftovers(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=ID)
    json.loads((tmp_path / "sources.json").read_text())
    assert not list(tmp_path.glob("*.tmp"))
