import json

from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore

ID = IdentityScope("codex", "ws", "proj", "sess", "main")


def test_second_store_instance_does_not_drop_first_instances_sources(tmp_path):
    """Two processes (modelled as two instances) must not lose each other's writes."""
    a = SourceStore(tmp_path)
    b = SourceStore(tmp_path)
    sa = a.put_source("from A", identity=ID)
    sb = b.put_source("from B", identity=ID)
    on_disk = json.loads((tmp_path / "sources.json").read_text())
    assert sa in on_disk and sb in on_disk
    assert SourceStore(tmp_path).get_source(sa)["content"] == "from A"


def test_put_source_leaves_no_partial_file(tmp_path):
    s = SourceStore(tmp_path)
    s.put_source("x", identity=ID)
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []
    json.loads((tmp_path / "sources.json").read_text())
