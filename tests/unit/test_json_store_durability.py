import json
import multiprocessing as mp

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

ID = IdentityScope("codex", "ws", "proj", "s1")


def test_source_store_second_instance_does_not_drop_first_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert {"A", "B"} <= set(fresh._sources)


def test_vector_index_second_instance_does_not_drop_first_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert {"A", "B"} <= set(VectorIndex(tmp_path).documents)


def test_version_store_second_instance_does_not_drop_first_writes(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    a.create_commit("one", [], [], "s", identity=ID)
    b.create_commit("two", [], [], "s", identity=ID)
    assert len(ContextVersionStore(tmp_path).versions) == 2


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text('{"SRC-x": {"content": "valuable"')  # truncated
    s = SourceStore(tmp_path)
    s.put_source("new", source_id="N", identity=ID)
    saved = list(tmp_path.glob("sources.json.corrupt-*"))
    assert saved and "valuable" in saved[0].read_text()
    assert "N" in json.loads((tmp_path / "sources.json").read_text())


def _worker(path, i):
    s = SourceStore(__import__("pathlib").Path(path))
    for j in range(10):
        s.put_source(f"c{i}-{j}", source_id=f"{i}-{j}", identity=ID)


def test_concurrent_processes_do_not_lose_sources(tmp_path):
    ps = [mp.Process(target=_worker, args=(str(tmp_path), i)) for i in range(4)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    assert len(SourceStore(tmp_path)._sources) == 40
