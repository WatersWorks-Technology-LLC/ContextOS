import multiprocessing
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex

IDENT = IdentityScope("codex", "/ws", "p", "s")


def _put(args):
    d, n = args
    store = SourceStore(Path(d))
    for i in range(10):
        store.put_source(f"content {n}-{i}", source_id=f"S{n}-{i}", identity=IDENT)
        VectorIndex(Path(d)).add_document(f"D{n}-{i}", f"doc {n} {i}")


def test_concurrent_processes_do_not_lose_writes(tmp_path):
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(4) as pool:
        pool.map(_put, [(str(tmp_path), n) for n in range(4)])
    assert len(SourceStore(tmp_path)._sources) == 40
    assert len(VectorIndex(tmp_path).documents) == 40


def test_corrupt_files_are_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{truncated")
    (tmp_path / "vectors.json").write_text("{truncated")
    SourceStore(tmp_path).put_source("x", identity=IDENT)
    VectorIndex(tmp_path).add_document("d", "x")
    assert len(list(tmp_path.glob("sources.json.corrupt-*"))) == 1
    assert len(list(tmp_path.glob("vectors.json.corrupt-*"))) == 1
