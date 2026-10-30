import json
import multiprocessing
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore


def _ident():
    return IdentityScope(runtime_id="codex", workspace_id="w", project_id="p", session_id="s", agent_id="main")


def test_source_store_instances_do_not_lose_each_others_writes(tmp_path):
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    assert set(SourceStore(tmp_path)._sources) == {"A", "B"}


def test_vector_index_instances_do_not_lose_each_others_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha text")
    b.add_document("B", "beta text")
    assert set(VectorIndex(tmp_path).documents) == {"A", "B"}


def test_version_store_instances_do_not_lose_each_others_commits(tmp_path):
    a, b = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    c1 = a.create_commit("one", [], [], "s", identity=_ident())
    c2 = b.create_commit("two", [], [], "s", identity=_ident())
    assert set(ContextVersionStore(tmp_path).versions) == {c1["commit_id"], c2["commit_id"]}


def test_corrupt_source_file_is_quarantined_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json", encoding="utf-8")
    store = SourceStore(tmp_path)
    store.put_source("x", source_id="X", identity=_ident())
    corrupt = list(tmp_path.glob("sources.json.corrupt-*"))
    assert len(corrupt) == 1 and corrupt[0].read_text(encoding="utf-8") == "{not json"
    assert "X" in json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))


def _writer(path, n):
    store = SourceStore(Path(path))
    for i in range(20):
        store.put_source(f"c{n}-{i}", source_id=f"P{n}-{i}", identity=_ident())


def test_concurrent_processes_keep_all_sources(tmp_path):
    procs = [multiprocessing.Process(target=_writer, args=(str(tmp_path), n)) for n in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    assert len(SourceStore(tmp_path)._sources) == 80
