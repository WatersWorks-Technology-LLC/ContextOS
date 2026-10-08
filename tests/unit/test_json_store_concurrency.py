import json
import multiprocessing as mp

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex


def _identity():
    return IdentityScope(runtime_id="r", workspace_id="w", project_id="p", session_id="s", agent_id="a")


def test_source_store_second_writer_does_not_drop_first(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    ida = a.put_source("alpha", identity=_identity())
    idb = b.put_source("beta", identity=_identity())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(ida) and fresh.get_source(idb)


def test_vector_index_second_writer_does_not_drop_first(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "alpha")
    b.add_document("d2", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def _worker(path, i):
    VectorIndex(path).add_document(f"d{i}", f"text {i}")


def test_vector_index_parallel_processes(tmp_path):
    ctx = mp.get_context("fork")
    procs = [ctx.Process(target=_worker, args=(tmp_path, i)) for i in range(8)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    assert len(VectorIndex(tmp_path).documents) == 8


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", identity=_identity())
    assert list(tmp_path.glob("sources.json.corrupt*"))
    json.loads((tmp_path / "sources.json").read_text())


def test_no_temp_files_left_behind(tmp_path):
    VectorIndex(tmp_path).add_document("d", "x")
    assert [p.name for p in tmp_path.iterdir()] == ["vectors.json"] or \
        sorted(p.name for p in tmp_path.iterdir()) == ["vectors.json", "vectors.json.lock"]
