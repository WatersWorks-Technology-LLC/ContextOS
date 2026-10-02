import json
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

IDENT = IdentityScope("rt", "ws", "proj", "sess")


def test_source_store_second_writer_does_not_drop_first(tmp_path):
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)  # second process: loaded before a writes
    a.put_source("alpha", source_id="A", identity=IDENT)
    b.put_source("beta", source_id="B", identity=IDENT)
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert set(on_disk) == {"A", "B"}


def test_vector_index_second_writer_does_not_drop_first(tmp_path):
    a = VectorIndex(tmp_path)
    b = VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"A", "B"}


def test_version_store_second_writer_does_not_drop_first(tmp_path):
    a = ContextVersionStore(tmp_path)
    b = ContextVersionStore(tmp_path)
    ra = a.create_commit("ctx one", [], [], "s", identity=IDENT)
    rb = b.create_commit("ctx two", [], [], "s", identity=IDENT)
    assert set(json.loads((tmp_path / "versions.json").read_text())) == {
        ra["commit_id"], rb["commit_id"]}


def test_corrupt_store_is_quarantined_not_overwritten(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=IDENT)
    backups = list(tmp_path.glob("sources.json.corrupt-*"))
    assert len(backups) == 1 and backups[0].read_text() == "{not json"
    assert set(json.loads(path.read_text())) == {"X"}


def test_save_leaves_no_partial_tmp_files(tmp_path):
    SourceStore(tmp_path).put_source("x", source_id="X", identity=IDENT)
    assert not list(tmp_path.glob("*.tmp"))
