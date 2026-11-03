from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore

ID = IdentityScope("codex", "ws", "proj", "sess")


def test_two_writers_do_not_lose_each_others_sources(tmp_path):
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)  # second process: loaded before a wrote
    a.put_source("alpha", source_id="A", identity=ID)
    b.put_source("beta", source_id="B", identity=ID)
    fresh = SourceStore(tmp_path)
    assert fresh.get_source("A") is not None
    assert fresh.get_source("B") is not None
    # a long-lived reader sees the other writer's data
    assert a.get_source("B") is not None


def test_corrupt_file_is_preserved_not_overwritten(tmp_path):
    (tmp_path / "sources.json").write_text("{not json", encoding="utf-8")
    s = SourceStore(tmp_path)
    s.put_source("x", source_id="X", identity=ID)
    backups = list(tmp_path.glob("sources.json.corrupt*"))
    assert backups and backups[0].read_text(encoding="utf-8") == "{not json"
