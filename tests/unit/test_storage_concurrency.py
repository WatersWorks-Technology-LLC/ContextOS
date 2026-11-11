import json
import multiprocessing as mp
from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore


def _ident():
    return IdentityScope(runtime_id="r", workspace_id="w", project_id="p", session_id="s", agent_id="a")


def test_source_store_second_instance_does_not_clobber_first(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # both load empty cache
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    assert set(json.loads((tmp_path / "sources.json").read_text())) == {"A", "B"}


def test_vector_index_second_instance_does_not_clobber_first(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"A", "B"}


def test_version_store_second_instance_does_not_clobber_first(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    a.create_commit("one", [], [], "s", identity=_ident())
    b.create_commit("two", [], [], "s", identity=_ident())
    assert len(json.loads((tmp_path / "versions.json").read_text())) == 2


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{truncated")
    ss = SourceStore(tmp_path)
    ss.put_source("x", source_id="X", identity=_ident())
    assert list(tmp_path.glob("sources.json.corrupt-*"))


def _worker(path, n):
    ss = SourceStore(path)
    for i in range(10):
        ss.put_source(f"c{n}-{i}", source_id=f"{n}-{i}", identity=_ident())


def test_source_store_multiprocess_no_lost_writes(tmp_path):
    ps = [mp.Process(target=_worker, args=(tmp_path, n)) for n in range(4)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    assert len(json.loads((tmp_path / "sources.json").read_text())) == 40
