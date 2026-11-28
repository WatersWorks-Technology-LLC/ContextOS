"""Regression: JSON stores must not lose writes across instances/processes or wipe corrupt data."""
import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_second_writer_does_not_drop_first(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", identity=ID)
    b.put_source("beta", identity=ID)
    assert len(json.loads((tmp_path / "sources.json").read_text())) == 2


def test_vector_index_second_writer_does_not_drop_first(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha")
    b.add_document("d2", "beta")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"d1", "d2"}


def test_versions_second_writer_does_not_drop_first(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    a.create_commit("one", [], [], "s", identity=ID)
    b.create_commit("two", [], [], "s", identity=ID)
    assert len(json.loads((tmp_path / "versions.json").read_text())) == 2


def test_corrupt_store_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text('{"SRC-x": {"content": "precious"')  # truncated
    store = SourceStore(tmp_path)
    store.put_source("new", identity=ID)
    backups = list(tmp_path.glob("sources.json.corrupt-*"))
    assert len(backups) == 1 and "precious" in backups[0].read_text()
