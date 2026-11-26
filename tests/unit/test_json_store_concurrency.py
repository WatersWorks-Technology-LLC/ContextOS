"""Regression: JSON-file stores must not lose data across instances/processes."""
import json
import pytest
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_source_store_second_instance_does_not_drop_first_write(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # two processes
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") and fresh.get_source("B")


def test_vector_index_second_instance_does_not_drop_first_write(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert set(VectorIndex(tmp_path).documents) == {"A", "B"}


def test_version_store_second_instance_does_not_drop_first_write(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx a", [], [], "s", identity=ID)
    cb = b.create_commit("ctx b", [], [], "s", identity=ID)
    assert set(ContextVersionStore(tmp_path).versions) == {ca["commit_id"], cb["commit_id"]}


def test_save_is_atomic_no_tmp_left_and_valid_json(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=ID)
    json.loads((tmp_path / "sources.json").read_text())
    assert not list(tmp_path.glob("*.tmp"))


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=ID)
    assert (tmp_path / "sources.json.corrupt").read_text() == "{not json"
