from contextos.identity import IdentityScope
from contextos.storage.source_store import SourceStore


def test_same_content_from_other_identity_does_not_rebind_owner(tmp_path):
    owner = IdentityScope("codex", "ws", "proj_a", "s")
    other = IdentityScope("codex", "ws", "proj_b", "s")
    store = SourceStore(tmp_path)
    sid = store.put_source("shared text", identity=owner)
    sid2 = store.put_source("shared text", identity=other)
    assert sid2 != sid
    assert store.get_sources([sid], identity=owner)
    assert store.get_sources([sid2], identity=other)
    assert not store.get_sources([sid], identity=other)
