import json
from pathlib import Path

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex
from contextos.storage.versioning import ContextVersionStore

IDENT = IdentityScope("codex", "ws", "proj", "sess", "main")


def test_second_store_instance_does_not_drop_first_instances_writes(tmp_path):
    # Two processes each hold their own in-memory copy of the same file.
    a, b = SourceStore(tmp_path), SourceStore(tmp_path)
    sa = a.put_source("from A", identity=IDENT)
    sb = b.put_source("from B", identity=IDENT)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source(sa) and fresh.get_source(sb)

    va, vb = VectorIndex(tmp_path), VectorIndex(tmp_path)
    va.add_document("a", "alpha")
    vb.add_document("b", "beta")
    assert set(VectorIndex(tmp_path).documents) == {"a", "b"}

    ca, cb = ContextVersionStore(tmp_path), ContextVersionStore(tmp_path)
    ia = ca.create_commit("ctx A", [], [], "s", identity=IDENT)["commit_id"]
    ib = cb.create_commit("ctx B", [], [], "s", identity=IDENT)["commit_id"]
    assert {ia, ib} <= set(ContextVersionStore(tmp_path).versions)


def test_corrupt_store_is_quarantined_not_silently_overwritten(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text('{"SRC-old": {"content": "precious"', encoding="utf-8")  # truncated
    store = SourceStore(tmp_path)
    store.put_source("new", identity=IDENT)
    saved = list(Path(tmp_path).glob("sources.json.corrupt-*"))
    assert saved and "precious" in saved[0].read_text(encoding="utf-8")
    json.loads(path.read_text(encoding="utf-8"))  # live file is valid JSON


def test_save_leaves_no_temp_files(tmp_path):
    SourceStore(tmp_path).put_source("x", identity=IDENT)
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")) == []
