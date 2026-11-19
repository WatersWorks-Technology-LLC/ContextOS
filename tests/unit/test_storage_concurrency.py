import json
import multiprocessing as mp
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

IDENT = IdentityScope("codex", "ws", "proj", "s1", "main")


def test_stale_second_instance_does_not_drop_first_writers_entries(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # both loaded empty
    a.put_source("alpha", identity=IDENT)
    b.put_source("beta", identity=IDENT)
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert len(on_disk) == 2


def test_vector_and_version_stores_merge_across_instances(tmp_path):
    v1, v2 = VectorIndex(tmp_path), VectorIndex(tmp_path)
    v1.add_document("d1", "one")
    v2.add_document("d2", "two")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"d1", "d2"}
    c1, c2 = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    c1.create_commit("x", [], [], "s", identity=IDENT)
    c2.create_commit("y", [], [], "s", identity=IDENT)
    assert len(json.loads((tmp_path / "versions.json").read_text())) == 2


def test_corrupt_file_is_quarantined_not_wiped(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("gamma", identity=IDENT)
    assert list(Path(tmp_path).glob("sources.json.corrupt-*"))


def _worker(d, n):
    s = SourceStore(Path(d))
    for i in range(10):
        s.put_source(f"w{n}-{i}", identity=IDENT)


def test_parallel_processes_lose_no_sources(tmp_path):
    SourceStore(tmp_path)
    ps = [mp.Process(target=_worker, args=(str(tmp_path), n)) for n in range(4)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    assert len(json.loads((tmp_path / "sources.json").read_text())) == 40
