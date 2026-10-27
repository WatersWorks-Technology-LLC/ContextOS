import json
import multiprocessing

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore


def _ident():
    return IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="main")


def test_source_store_does_not_lose_other_process_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)  # both loaded an empty file
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") and fresh.get_source("B")
    assert a.get_source("B") is not None  # readers see other writers


def test_vector_index_does_not_lose_other_process_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("d1", "hello world")
    b.add_document("d2", "goodbye world")
    assert set(VectorIndex(tmp_path).documents) == {"d1", "d2"}


def test_version_store_does_not_lose_other_process_writes(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ca = a.create_commit("ctx one", [], [], "s", identity=_ident())
    cb = b.create_commit("ctx two", [], [], "s", identity=_ident())
    ids = set(ContextVersionStore(tmp_path).versions)
    assert {ca["commit_id"], cb["commit_id"]} <= ids


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{truncated")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=_ident())
    assert list(tmp_path.glob("sources.json.corrupt-*"))
    assert json.loads((tmp_path / "sources.json").read_text()).keys() == {"X"}


def _writer(path, n):
    s = SourceStore(__import__("pathlib").Path(path))
    for i in range(n):
        s.put_source(f"c{n}-{i}", source_id=f"{n}-{i}", identity=_ident())


def test_parallel_processes_keep_all_sources(tmp_path):
    SourceStore(tmp_path)
    ps = [multiprocessing.Process(target=_writer, args=(str(tmp_path), n)) for n in (20, 21, 22)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    assert len(SourceStore(tmp_path)._sources) == 63
