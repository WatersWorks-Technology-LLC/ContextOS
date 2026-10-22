"""Two store instances on one directory model two processes sharing the files."""
import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_does_not_lose_other_writers_updates(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    assert set(SourceStore(tmp_path)._sources) == {"A", "B"}


def test_vector_index_does_not_lose_other_writers_updates(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha")
    b.add_document("B", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"A", "B"}


def test_version_store_does_not_lose_other_writers_updates(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx one", [], [], "s", identity=ID)
    cb = b.create_commit("ctx two", [], [], "s", identity=ID)
    assert set(ContextVersionStore(tmp_path).versions) == {ca["commit_id"], cb["commit_id"]}


def test_corrupt_source_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    SourceStore(tmp_path).put_source("x", source_id="A", identity=ID)
    backups = list(tmp_path.glob("sources.json.corrupt*"))
    assert backups and backups[0].read_text() == "{not json"
    assert "A" in json.loads((tmp_path / "sources.json").read_text())
