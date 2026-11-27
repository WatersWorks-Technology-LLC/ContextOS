from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore


def _ident():
    return IdentityScope("codex", "ws", "proj", "s1", "main")


def test_two_instances_do_not_lose_each_others_writes(tmp_path):
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)  # loaded before a writes, like a second process
    a.put_source("alpha", source_id="A", identity=_ident())
    b.put_source("beta", source_id="B", identity=_ident())
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") is not None
    assert fresh.get_source("B") is not None


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=_ident())
    assert (tmp_path / "sources.json.corrupt").read_text() == "{not json"
