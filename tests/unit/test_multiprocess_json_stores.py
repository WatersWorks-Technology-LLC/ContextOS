"""Two store instances (e.g. two processes) sharing one directory must not lose writes."""
import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex

IDENT = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_source_store_concurrent_instances_do_not_lose_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    sid_a = a.put_source("from a", identity=IDENT)
    sid_b = b.put_source("from b", identity=IDENT)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sid_a) is not None
    assert fresh.get_source(sid_b) is not None
    # the writer's own cache also sees the other instance's record
    assert a.get_source(sid_b) is not None


def test_vector_index_concurrent_instances_do_not_lose_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha text")
    b.add_document("d2", "beta text")
    fresh = VectorIndex(tmp_path)
    assert set(fresh.documents) == {"d1", "d2"}


def test_store_files_are_written_atomically(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=IDENT)
    assert json.loads((tmp_path / "sources.json").read_text())
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []
