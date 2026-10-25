"""Two store instances (two processes) sharing one data dir must not lose each other's writes."""
import json
import pytest
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_source_store_stale_instance_does_not_drop_other_writer(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    sa = a.put_source("from a", identity=ID)
    sb = b.put_source("from b", identity=ID)
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert {sa, sb} <= set(on_disk)
    assert SourceStore(tmp_path).get_source(sa)["content"] == "from a"


def test_vector_index_stale_instance_does_not_drop_other_writer(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha text")
    b.add_document("d2", "beta text")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"d1", "d2"}


def test_version_store_stale_instance_does_not_drop_other_writer(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx a", [], [], "s", identity=ID)["commit_id"]
    cb = b.create_commit("ctx b", [], [], "s", identity=ID)["commit_id"]
    assert {ca, cb} <= set(json.loads((tmp_path / "versions.json").read_text()))


def test_source_store_corrupt_file_is_not_silently_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("new", identity=ID)
    assert list(tmp_path.glob("sources.json.corrupt*")), "corrupt file must be preserved"
