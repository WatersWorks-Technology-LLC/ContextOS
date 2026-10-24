import json
import pytest
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "workspace", "project", "s1", "main")


def test_source_store_second_writer_keeps_first_writers_records(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # two processes, both loaded empty
    sa = a.put_source("from A", identity=ID)
    sb = b.put_source("from B", identity=ID)
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert {sa, sb} <= set(on_disk)


def test_vector_index_second_writer_keeps_first_writers_docs(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha")
    b.add_document("d2", "beta")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"d1", "d2"}


def test_version_store_second_writer_keeps_first_writers_commits(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx A", [], [], "s", identity=ID)["commit_id"]
    cb = b.create_commit("ctx B", [], [], "s", identity=ID)["commit_id"]
    assert {ca, cb} <= set(json.loads((tmp_path / "versions.json").read_text()))


def test_save_is_atomic_and_leaves_no_temp_files(tmp_path, monkeypatch):
    s = SourceStore(tmp_path)
    s.put_source("keep me", identity=ID)
    before = (tmp_path / "sources.json").read_text()

    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr("contextos.storage.jsonfile.json.dump", boom)
    with pytest.raises(OSError):
        s.put_source("second", identity=ID)
    assert (tmp_path / "sources.json").read_text() == before
    assert not list(tmp_path.glob("*.tmp"))
