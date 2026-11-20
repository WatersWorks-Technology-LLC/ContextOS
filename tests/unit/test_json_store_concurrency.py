"""Regression: JSON-file stores must not lose writes made by another instance/process."""
import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_second_instance_does_not_clobber(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") and fresh.get_source("B")
    # the writer's own view also sees the other instance's record
    assert b.get_source("A")


def test_vector_index_second_instance_does_not_clobber(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha doc")
    b.add_document("B", "beta doc")
    assert set(VectorIndex(tmp_path).documents) == {"A", "B"}


def test_version_store_second_instance_does_not_clobber(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx one", [], [], "s", identity=ID)
    cb = b.create_commit("ctx two", [], [], "s", identity=ID)
    assert set(ContextVersionStore(tmp_path).versions) == {ca["commit_id"], cb["commit_id"]}


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text('{"SRC-x": {"content": "precious"')  # truncated
    s = SourceStore(tmp_path)
    s.put_source("new", source_id="N", identity=ID)
    backups = list(tmp_path.glob("sources.json.corrupt*"))
    assert backups and "precious" in backups[0].read_text()
    assert json.loads((tmp_path / "sources.json").read_text()).keys() == {"N"}
