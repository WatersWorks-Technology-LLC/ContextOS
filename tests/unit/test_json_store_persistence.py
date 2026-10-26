import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore
from contextos.storage.vector_index import VectorIndex


def _ident():
    import inspect
    params = inspect.signature(IdentityScope).parameters
    return IdentityScope(**{p: "x" for p in params if params[p].default is inspect._empty})


def test_two_instances_do_not_lose_each_others_writes(tmp_path):
    a, b = VectorIndex(tmp_path), VectorIndex(tmp_path)
    a.add_document("A", "alpha")
    b.add_document("B", "beta")  # b loaded before A existed
    assert set(json.loads((tmp_path / "vectors.json").read_text())) == {"A", "B"}


def test_corrupt_file_is_preserved_not_silently_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{truncated")
    s = SourceStore(tmp_path)
    s.put_source("hello", identity=_ident())
    assert list(tmp_path.glob("sources.json.corrupt-*"))
    assert not list(tmp_path.glob("*.tmp"))
